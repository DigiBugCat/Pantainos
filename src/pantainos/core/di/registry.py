"""
Handler Registry for Dependency Injection

This module provides the HandlerRegistry class that manages handler registration
and creates dependency injection wrappers for both legacy and explicit handler styles.
"""

from __future__ import annotations

import inspect
import logging
from collections import defaultdict
from functools import wraps
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from collections.abc import Awaitable, Callable

    from .container import ServiceContainer

from .inspector import HandlerInspector, HandlerStyle

logger = logging.getLogger(__name__)


class HandlerRegistry:
    """
    Registry that manages handler registration and dependency injection.

    Supports both legacy (event, ctx) and explicit dependency injection styles.
    """

    def __init__(self, container: ServiceContainer) -> None:
        self.container = container
        self.handlers: dict[str, list[dict[str, Any]]] = defaultdict(list)
        self.inspector = HandlerInspector()
        # Track handlers by module for hot reloading
        self.handlers_by_module: dict[str, list[tuple[str, Callable[..., Any]]]] = defaultdict(list)

    def _get_calling_module(self) -> str | None:
        """
        Detect which module is registering a handler by inspecting the call stack.

        Returns:
            Module name if detected, None otherwise
        """
        try:
            # Walk up the call stack to find the first frame outside of this registry
            frame = inspect.currentframe()
            while frame:
                frame = frame.f_back
                if not frame:
                    break

                module_name = frame.f_globals.get("__name__")
                if (
                    module_name
                    and isinstance(module_name, str)
                    and module_name != __name__
                    and "modules." in module_name
                ):
                    # Extract just the module name (e.g., "chat" from "modules.chat.actions.basic_commands")
                    parts = module_name.split(".")
                    if len(parts) >= 2 and parts[0] == "modules":
                        return str(parts[1])  # Return "chat", "alerts", etc.

            return None
        except Exception:
            return None

    def register(
        self,
        event_type: str,
        handler: Callable[..., Any],
        filters: list[Callable[..., bool]] | None = None,
        priority: int = 5,
    ) -> None:
        """
        Register a handler for an event type with automatic dependency injection.

        Args:
            event_type: The event type to handle (e.g., "twitch.chat.message")
            handler: The handler function (legacy or explicit style)
            filters: Optional filter functions
            priority: Handler priority (lower = higher priority)
        """
        # Inspect the handler to determine its style and dependencies
        handler_info = self.inspector.inspect_handler(handler)

        if not handler_info["is_valid"]:
            logger.warning(
                f"Handler {handler_info['handler_name']} failed validation: {handler_info['validation_message']}"
            )
            return

        # Create the appropriate wrapper based on handler style
        if handler_info["style"] == HandlerStyle.LEGACY:
            wrapped_handler = self._create_legacy_wrapper(handler, handler_info)
        else:
            wrapped_handler = self._create_explicit_wrapper(handler, handler_info)

        # Detect calling module for tracking
        calling_module = self._get_calling_module()

        # Store handler registration info
        handler_record = {
            "handler": wrapped_handler,
            "original_handler": handler,
            "filters": filters or [],
            "priority": priority,
            "style": handler_info["style"],
            "dependencies": handler_info.get("dependencies", []),
            "handler_name": handler_info["handler_name"],
            "is_async": handler_info["is_async"],
            "module": calling_module,
        }

        self.handlers[event_type].append(handler_record)

        # Track handler by module for hot reloading
        if calling_module:
            self.handlers_by_module[calling_module].append((event_type, handler))

        # Sort by priority after adding
        self.handlers[event_type].sort(key=lambda h: h["priority"])

        logger.info(
            f"Registered {handler_info['style'].value} style handler "
            f"{handler_info['handler_name']} for event {event_type}"
            f"{f' (module: {calling_module})' if calling_module else ''}"
        )

    def _create_legacy_wrapper(
        self, handler: Callable[..., Any], handler_info: dict[str, Any]
    ) -> Callable[[Any, Any], Awaitable[None]]:
        """
        Create a wrapper for legacy (event, ctx) style handlers.

        Args:
            handler: The legacy handler function
            handler_info: Handler inspection results

        Returns:
            Wrapped handler that maintains legacy interface
        """
        if handler_info["is_async"]:

            @wraps(handler)
            async def async_legacy_wrapper(event: Any, context: Any) -> None:
                await handler(event, context)

            return async_legacy_wrapper

        @wraps(handler)
        async def sync_legacy_wrapper(event: Any, context: Any) -> None:
            handler(event, context)

        return sync_legacy_wrapper

    def _create_explicit_wrapper(
        self, handler: Callable[..., Any], handler_info: dict[str, Any]
    ) -> Callable[[Any, Any], Awaitable[None]]:
        """
        Create a wrapper for explicit dependency injection style handlers.

        Args:
            handler: The explicit style handler function
            handler_info: Handler inspection results

        Returns:
            Wrapped handler that resolves and injects dependencies
        """
        dependencies = handler_info.get("dependencies", [])

        if handler_info["is_async"]:

            @wraps(handler)
            async def async_explicit_wrapper(event: Any, _context: Any) -> None:
                # Resolve dependencies from the container
                resolved_deps = []
                for dep_type in dependencies:
                    try:
                        dep = self.container.resolve(dep_type)
                        resolved_deps.append(dep)
                    except KeyError:
                        logger.error(
                            f"Failed to resolve dependency {dep_type.__name__} "
                            f"for handler {handler_info['handler_name']}"
                        )
                        # Re-raise to fail fast on missing dependencies
                        raise

                # Call handler with event + resolved dependencies
                await handler(event, *resolved_deps)

        else:

            @wraps(handler)
            async def sync_explicit_wrapper(event: Any, _context: Any) -> None:
                # Resolve dependencies from the container
                resolved_deps = []
                for dep_type in dependencies:
                    try:
                        dep = self.container.resolve(dep_type)
                        resolved_deps.append(dep)
                    except KeyError:
                        logger.error(
                            f"Failed to resolve dependency {dep_type.__name__} "
                            f"for handler {handler_info['handler_name']}"
                        )
                        # Re-raise to fail fast on missing dependencies
                        raise

                # Call handler with event + resolved dependencies
                handler(event, *resolved_deps)

        return async_explicit_wrapper if handler_info["is_async"] else sync_explicit_wrapper

    def get_handlers(self, event_type: str) -> list[dict[str, Any]]:
        """
        Get all registered handlers for an event type.

        Args:
            event_type: The event type to get handlers for

        Returns:
            List of handler records sorted by priority
        """
        return self.handlers.get(event_type, [])

    def unregister(self, event_type: str, handler: Callable[..., Any]) -> bool:
        """
        Unregister a handler for an event type.

        Args:
            event_type: The event type
            handler: The original handler function

        Returns:
            True if handler was found and removed, False otherwise
        """
        handlers = self.handlers.get(event_type, [])

        for i, handler_record in enumerate(handlers):
            if handler_record["original_handler"] is handler:
                del handlers[i]
                logger.info(f"Unregistered handler {handler.__name__} for event {event_type}")
                return True

        return False

    def unregister_module_handlers(self, module_name: str) -> int:
        """
        Unregister all handlers from a specific module.

        Args:
            module_name: The module name (e.g., "chat", "alerts")

        Returns:
            Number of handlers removed
        """
        handlers_to_remove = self.handlers_by_module.get(module_name, [])
        removed_count = 0

        for event_type, handler in handlers_to_remove:
            if self.unregister(event_type, handler):
                removed_count += 1

        # Clear the module tracking
        if module_name in self.handlers_by_module:
            del self.handlers_by_module[module_name]

        logger.info(f"Unregistered {removed_count} handlers from module '{module_name}'")
        return removed_count

    def clear_handlers(self, event_type: str | None = None) -> None:
        """
        Clear handlers for a specific event type or all event types.

        Args:
            event_type: Event type to clear, or None to clear all
        """
        if event_type is None:
            self.handlers.clear()
            logger.info("Cleared all registered handlers")
        else:
            self.handlers[event_type].clear()
            logger.info(f"Cleared handlers for event type {event_type}")

    def get_stats(self) -> dict[str, Any]:
        """
        Get statistics about registered handlers.

        Returns:
            Dictionary with handler statistics
        """
        total_handlers = sum(len(handlers) for handlers in self.handlers.values())

        style_counts = {"legacy": 0, "explicit": 0}
        for handlers in self.handlers.values():
            for handler_record in handlers:
                style = handler_record["style"].value
                style_counts[style] += 1

        return {
            "total_handlers": total_handlers,
            "event_types": list(self.handlers.keys()),
            "handlers_per_event": {event: len(handlers) for event, handlers in self.handlers.items()},
            "style_distribution": style_counts,
            "registered_services": len(self.container.get_registered_types()),
        }

    def validate_dependencies(self) -> list[str]:
        """
        Validate that all handler dependencies can be resolved.

        Returns:
            List of error messages for missing dependencies
        """
        errors = []

        for event_type, handlers in self.handlers.items():
            for handler_record in handlers:
                if handler_record["style"] == HandlerStyle.EXPLICIT:
                    dependencies = handler_record.get("dependencies", [])
                    for dep_type in dependencies:
                        if not self.container.is_registered(dep_type):
                            errors.append(
                                f"Handler {handler_record['handler_name']} for event "
                                f"{event_type} requires unregistered dependency "
                                f"{dep_type.__name__}"
                            )

        return errors

    def create_active_trigger_wrapper(self, handler: Callable[..., Any]) -> Callable[[Any, Any], Awaitable[None]]:
        """
        Create a wrapper for active trigger handlers with dependency injection.

        This allows active triggers to use the same DI system as event handlers.

        Args:
            handler: The handler function to wrap

        Returns:
            Wrapped handler compatible with active trigger execution
        """
        handler_info = self.inspector.inspect_handler(handler)

        if not handler_info["is_valid"]:
            raise ValueError(f"Invalid handler: {handler_info['validation_message']}")

        if handler_info["style"] == HandlerStyle.LEGACY:
            return self._create_legacy_wrapper(handler, handler_info)
        return self._create_explicit_wrapper(handler, handler_info)

    def __repr__(self) -> str:
        total_handlers = sum(len(handlers) for handlers in self.handlers.values())
        event_count = len(self.handlers)
        return f"HandlerRegistry(handlers={total_handlers}, events={event_count})"
