"""
Event Bus - Central event routing system for Pantainos
"""

import asyncio
import contextlib
import inspect
import logging
from collections import defaultdict
from collections.abc import Awaitable, Callable
from typing import Any

from pantainos.core.di.container import ServiceContainer
from pantainos.events import EventModel

logger = logging.getLogger(__name__)


class HandlerRegistry:
    """Simple registry for tracking handlers by module"""

    def __init__(self) -> None:
        self.handlers_by_module: dict[str, list[tuple[str, Callable]]] = {}


class EventBus:
    """
    Clean event bus without global state dependencies.

    This replaces the old EventBus that relied on HandlerRegistry and global state.
    """

    def __init__(self, container: ServiceContainer) -> None:
        self.handlers: dict[str, list[dict[str, Any]]] = defaultdict(list)
        self.container = container
        self.running = False
        self.event_queue: asyncio.Queue[EventModel] = asyncio.Queue()
        self.processing_task: asyncio.Task[None] | None = None
        self.handler_registry = HandlerRegistry()

    def register(self, event_type: str, handler: Callable[..., Awaitable[Any]], condition: Any | None = None) -> None:
        """Register a handler with optional condition"""
        self.handlers[event_type].append({"handler": handler, "condition": condition, "name": handler.__name__})
        logger.debug(f"Registered handler {handler.__name__} for event {event_type}")

    async def emit(self, event: EventModel) -> None:
        """Emit an event to all registered handlers"""
        await self.event_queue.put(event)
        logger.debug(f"Event queued: {event.event_type} from {event.source}")

    async def start(self) -> None:
        """Start the event processing loop"""
        self.running = True
        self.processing_task = asyncio.create_task(self._process_events())
        logger.info("EventBus started")

    async def stop(self) -> None:
        """Stop the event processing loop"""
        self.running = False
        if self.processing_task:
            self.processing_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self.processing_task
        logger.info("EventBus stopped")

    async def _process_events(self) -> None:
        """Process events from the queue"""
        while self.running:
            try:
                # Wait for event with timeout to allow for shutdown
                event = await asyncio.wait_for(self.event_queue.get(), timeout=1.0)
                task = asyncio.create_task(self._dispatch_event(event))
                # Store task reference to avoid RUF006 warning
                self._background_tasks = getattr(self, "_background_tasks", set())
                self._background_tasks.add(task)
                task.add_done_callback(self._background_tasks.discard)
            except TimeoutError:
                continue
            except Exception as e:
                logger.error(f"Error in event processing: {e}", exc_info=True)

    async def _dispatch_event(self, event: EventModel) -> None:
        """Dispatch event to all matching handlers"""
        # Process middleware first - middleware can modify or block events
        if hasattr(self, "middleware"):
            for middleware in self.middleware:
                try:
                    result = middleware(event)
                    if asyncio.iscoroutine(result):
                        event = await result
                    else:
                        event = result
                    # If middleware returns None, block the event
                    if event is None:
                        logger.debug("Event blocked by middleware")
                        return
                except Exception as e:
                    logger.error(f"Error in middleware: {e}", exc_info=True)
                    return

        # Log event to database if EventRepository is available
        await self._log_event_to_database(event)

        # Call event hooks for every event
        if hasattr(self, "event_hooks"):
            for hook in self.event_hooks:
                try:
                    result = hook(event)
                    if asyncio.iscoroutine(result):
                        await result
                except Exception as e:
                    logger.error(f"Error in event hook: {e}", exc_info=True)

        handlers = self.handlers.get(event.event_type, [])

        if not handlers:
            logger.debug(f"No handlers for event {event.event_type}")
            return

        # Create tasks for all handlers that pass conditions
        tasks = []
        for handler_info in handlers:
            handler = handler_info["handler"]
            condition = handler_info["condition"]
            name = handler_info["name"]

            # Check condition if present
            if condition:
                try:
                    if not condition(event):
                        logger.debug(f"Handler {name} filtered out by condition")
                        continue
                except Exception as e:
                    logger.error(f"Error in condition for {name}: {e}")
                    continue

            # Create task for handler execution with DI
            task = asyncio.create_task(self._execute_handler(handler, event))
            tasks.append(task)

        # Wait for all handlers to complete
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)

    async def _log_event_to_database(self, event: EventModel) -> None:
        """Log event to database if EventRepository is available"""
        try:
            # Try to get EventRepository from container
            from pantainos.db.repositories.event_repository import EventRepository

            event_repo = self.container.resolve(EventRepository)

            # Extract user_id from event data if available
            user_id = None
            if hasattr(event, "data") and isinstance(event.data, dict):
                user_id = event.data.get("user_id")

            # Log the event
            await event_repo.log_event(
                event_type=event.event_type, data=event.data if hasattr(event, "data") else {}, user_id=user_id
            )

        except (ImportError, KeyError):
            # EventRepository not available or not registered - skip logging
            pass
        except Exception as e:
            # Log error but don't break event processing
            logger.debug(f"Failed to log event to database: {e}")

    async def _execute_handler(self, handler: Callable[..., Awaitable[Any]], event: EventModel) -> None:
        """Execute a handler with dependency injection"""
        try:
            # Get handler signature for dependency injection
            sig = inspect.signature(handler)

            # First parameter is always the event
            params = list(sig.parameters.values())
            if not params:
                await handler()
                return

            # Build arguments
            args = [event]  # First arg is always the event

            # Inject dependencies for remaining parameters
            for param in params[1:]:
                if param.annotation and param.annotation != inspect.Parameter.empty:
                    try:
                        dependency = self.container.resolve(param.annotation)
                        args.append(dependency)
                    except Exception as e:
                        logger.warning(f"Could not inject {param.annotation} for {handler.__name__}: {e}")
                        # Skip this handler if we can't inject required dependencies
                        return
                else:
                    # Provide None for untyped parameters to allow handler execution
                    args.append(None)

            # Execute handler
            result = handler(*args)
            if asyncio.iscoroutine(result):
                await result

        except Exception as e:
            logger.error(f"Error executing handler {handler.__name__}: {e}", exc_info=True)
            # Call error handlers if they exist
            if hasattr(self, "error_handlers"):
                for error_handler in self.error_handlers:
                    try:
                        result = error_handler(e, handler.__name__)
                        if asyncio.iscoroutine(result):
                            await result
                    except Exception as err_handler_error:
                        logger.error(f"Error in error handler: {err_handler_error}", exc_info=True)

    def register_handler(
        self,
        event_type: str,
        handler: Callable[..., Awaitable[Any]],
        filters: list[Callable] | None = None,
        priority: int = 100,
    ) -> None:
        """Register a handler with filters and priority (test-compatible interface)"""
        # Convert filters to a single condition function
        condition = None
        if filters:

            def combined_condition(event: EventModel) -> bool:
                return all(f(event) for f in filters)

            condition = combined_condition

        # Store handler with priority info for sorting
        handler_info = {"handler": handler, "condition": condition, "name": handler.__name__, "priority": priority}
        self.handlers[event_type].append(handler_info)
        # Sort handlers by priority (lower number = higher priority)
        self.handlers[event_type].sort(key=lambda h: h.get("priority", 100))
        logger.debug(f"Registered handler {handler.__name__} for event {event_type} with priority {priority}")

    def unregister_handler(self, event_type: str, handler: Callable[..., Awaitable[Any]]) -> None:
        """Unregister a specific handler for an event type"""
        if event_type in self.handlers:
            self.handlers[event_type] = [h for h in self.handlers[event_type] if h["handler"] != handler]

    def add_event_hook(self, hook: Callable[[EventModel], Awaitable[None]]) -> None:
        """Add a hook that will be called for every event"""
        if not hasattr(self, "event_hooks"):
            self.event_hooks: list[Callable[[EventModel], Awaitable[None]]] = []
        self.event_hooks.append(hook)

    def remove_event_hook(self, hook: Callable[[EventModel], Awaitable[None]]) -> None:
        """Remove an event hook"""
        if hasattr(self, "event_hooks") and hook in self.event_hooks:
            self.event_hooks.remove(hook)

    def add_middleware(self, middleware: Callable[[EventModel], Awaitable[EventModel | None]]) -> None:
        """Add middleware to process events"""
        if not hasattr(self, "middleware"):
            self.middleware: list[Callable[[EventModel], Awaitable[EventModel | None]]] = []
        self.middleware.append(middleware)

    def add_error_handler(self, error_handler: Callable[[Exception, str], Awaitable[None]]) -> None:
        """Add an error handler for handler exceptions"""
        if not hasattr(self, "error_handlers"):
            self.error_handlers: list[Callable[[Exception, str], Awaitable[None]]] = []
        self.error_handlers.append(error_handler)

    def get_stats(self) -> dict[str, Any]:
        """Get event bus statistics"""
        handler_counts = {}
        for event_type, handlers in self.handlers.items():
            handler_counts[event_type] = len(handlers)

        return {
            "running": self.running,
            "registered_events": list(self.handlers.keys()),
            "handler_counts": handler_counts,
        }

    def unregister_module_handlers(self, module_name: str) -> int:
        """Unregister all handlers for a specific module"""
        if module_name not in self.handler_registry.handlers_by_module:
            return 0

        removed_count = 0
        for event_type, handler in self.handler_registry.handlers_by_module[module_name]:
            if event_type in self.handlers:
                original_count = len(self.handlers[event_type])
                self.handlers[event_type] = [h for h in self.handlers[event_type] if h["handler"] != handler]
                removed_count += original_count - len(self.handlers[event_type])

        # Remove module from registry
        del self.handler_registry.handlers_by_module[module_name]
        return removed_count
