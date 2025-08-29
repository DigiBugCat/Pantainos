"""
Pantainos Application - FastAPI-like event-driven framework

This module provides the main Pantainos class with app-bound decorators,
type-safe event filtering, and plugin mounting capabilities.
"""

from __future__ import annotations

import asyncio
import logging
from typing import TYPE_CHECKING, Any, TypeVar

if TYPE_CHECKING:
    from collections.abc import Awaitable, Callable

from .conditions import Condition
from .core.di.container import ServiceContainer
from .core.event_bus import EventBus
from .core.scheduler import ScheduleManager
from .events import Event, EventModel
from .schedules import Schedule
from .web.server import WebServer

# Try to import Pydantic for type checking
try:
    from pydantic import BaseModel

    PYDANTIC_AVAILABLE = True
except ImportError:
    BaseModel = type(None)  # Fallback for type checking
    PYDANTIC_AVAILABLE = False

# Type variable for event models
E = TypeVar("E", bound="EventModel")

logger = logging.getLogger(__name__)


class Pantainos:
    """
    Main Pantainos application class with FastAPI-like decorators.

    Provides app-bound decorators for event handling, type-safe conditions,
    and plugin mounting capabilities.
    """

    def __init__(self, database_url: str = "sqlite:///pantainos.db", debug: bool = False, **kwargs: Any) -> None:
        """
        Initialize Pantainos application.

        Args:
            database_url: Database connection URL
            debug: Enable debug logging
            **kwargs: Additional application parameters
        """
        self.database_url = database_url
        self.debug = debug
        self.kwargs = kwargs

        # Core components - no global state!
        self.container = ServiceContainer()
        self.event_bus = EventBus(self.container)
        self.schedule_manager = ScheduleManager(self.event_bus, self.container)
        self.plugins: dict[str, Any] = {}
        self.routers: list[Any] = []

        # Database will be initialized on startup
        self.database: Any | None = None

        # Web server initialization
        if kwargs.get("web_dashboard"):
            self.web_server = WebServer(self)

        if debug:
            logging.basicConfig(level=logging.DEBUG)

        self.logger = logging.getLogger(__name__)

    def on(
        self, event_type: str | type[E], *, when: Condition[E] | None = None
    ) -> Callable[[Callable[..., Awaitable[Any]]], Callable[..., Awaitable[Any]]]:
        """
        Register an event handler with optional conditions.

        This is the main decorator for registering event handlers in a type-safe way.

        Args:
            event_type: Event type (string) or EventModel class
            when: Optional condition for filtering events

        Returns:
            Decorator function

        Example:
            @app.on("user.login")
            async def handle_login(event):
                print(f"User {event.data['user']} logged in")

            @app.on(ChatMessage, when=ChatMessage.command("hello"))
            async def hello_cmd(event: ChatMessage, twitch: TwitchPlugin):
                await twitch.send(f"Hello {event.user}!")
        """

        def decorator(handler: Callable[..., Awaitable[Any]]) -> Callable[..., Awaitable[Any]]:
            # Check if it's a Schedule instance or subclass
            if isinstance(event_type, Schedule):
                # It's a Schedule instance - register with schedule manager
                self._register_scheduled_handler(handler, event_type)
            elif isinstance(event_type, type) and issubclass(event_type, Schedule):
                # It's a Schedule class - create instance and register
                schedule_instance = event_type()
                self._register_scheduled_handler(handler, schedule_instance)
            elif isinstance(event_type, type) and issubclass(event_type, EventModel):
                # It's a Pydantic model - get the event_type string
                actual_event_type = event_type.event_type

                # Wrap handler to auto-parse dict data to model
                wrapped_handler = self._wrap_with_model(handler, event_type)

                # Register with condition that can work with parsed model
                model_condition = self._adapt_condition_for_model(when, event_type) if when else None
                self.event_bus.register(actual_event_type, wrapped_handler, model_condition)
            else:
                # String event type - register as-is
                self.event_bus.register(str(event_type), handler, when)

            return handler

        return decorator

    def _wrap_with_model(
        self, handler: Callable[..., Awaitable[Any]], model_class: type[E]
    ) -> Callable[..., Awaitable[Any]]:
        """Wrap handler to auto-parse dict data to Pydantic model"""

        async def wrapped(event: Event) -> Any:
            # Parse dict data to model
            try:
                if PYDANTIC_AVAILABLE and hasattr(model_class, "model_validate"):
                    # Pydantic v2
                    parsed_event = model_class.model_validate(event.data)
                elif PYDANTIC_AVAILABLE and hasattr(model_class, "parse_obj"):
                    # Pydantic v1
                    parsed_event = model_class.parse_obj(event.data)  # type: ignore
                else:
                    # Fallback - create instance directly
                    parsed_event = model_class(**event.data)  # type: ignore

                # Replace event with parsed model
                new_event = Event(type=event.type, data=parsed_event, source=event.source)
                return await handler(new_event)

            except Exception as e:
                self.logger.error(f"Failed to parse event data to {model_class.__name__}: {e}")
                raise

        return wrapped

    def _adapt_condition_for_model(self, condition: Condition[E] | None, model_class: type[E]) -> Condition[Any] | None:
        """Adapt a model-specific condition to work with Event objects"""
        if not condition:
            return None

        def adapted_check(event: Event) -> bool:
            # The condition expects a model instance
            # By the time this runs, event.data should be the parsed model
            if hasattr(event, "data") and isinstance(event.data, model_class):
                return condition(event.data)
            return False

        return Condition(adapted_check, f"adapted_{condition.name}")

    def _register_scheduled_handler(self, handler: Callable[..., Awaitable[Any]], schedule: Schedule) -> None:
        """
        Register a scheduled handler with the schedule manager.

        Args:
            handler: Handler function to execute on schedule
            schedule: Schedule instance (Interval, Cron, Watch, etc.)
        """
        from .schedules import Cron, Interval, Watch

        # Debug: print schedule type
        self.logger.debug(f"Registering schedule: {type(schedule)} - {schedule}")

        # Register scheduled handler synchronously by directly adding to scheduled_tasks
        if isinstance(schedule, Interval):
            self.schedule_manager.scheduled_tasks.append(
                {
                    "handler": handler,
                    "schedule": schedule,
                    "type": "interval",
                    "execution_count": 0,
                    "last_execution": 0.0,
                }
            )
        elif isinstance(schedule, Cron):
            self.schedule_manager.scheduled_tasks.append(
                {
                    "handler": handler,
                    "schedule": schedule,
                    "type": "cron",
                    "execution_count": 0,
                    "next_execution": self.schedule_manager.calculate_next_cron_time(schedule),
                }
            )
        elif isinstance(schedule, Watch):
            self.schedule_manager.scheduled_tasks.append(
                {
                    "handler": handler,
                    "schedule": schedule,
                    "type": "watch",
                    "execution_count": 0,
                    "last_check": 0.0,
                    "previous_results": [],
                }
            )
        else:
            # Generic schedule - determine type from event_type
            if schedule.event_type == "@interval":
                self.schedule_manager.scheduled_tasks.append(
                    {
                        "handler": handler,
                        "schedule": schedule,
                        "type": "interval",
                        "execution_count": 0,
                        "last_execution": 0.0,
                    }
                )
            elif schedule.event_type == "@cron":
                self.schedule_manager.scheduled_tasks.append(
                    {
                        "handler": handler,
                        "schedule": schedule,
                        "type": "cron",
                        "execution_count": 0,
                        "next_execution": self.schedule_manager.calculate_next_cron_time(schedule),
                    }
                )
            elif schedule.event_type == "@watch":
                self.schedule_manager.scheduled_tasks.append(
                    {
                        "handler": handler,
                        "schedule": schedule,
                        "type": "watch",
                        "execution_count": 0,
                        "last_check": 0.0,
                        "previous_results": [],
                    }
                )

        self.logger.debug(f"Registered scheduled handler: {handler.__name__} for {schedule.event_type}")

    def mount(self, plugin: Any, name: str | None = None) -> None:
        """
        Mount a plugin as an event source and injectable dependency.

        Args:
            plugin: Plugin instance to mount
            name: Optional name override (defaults to plugin.name)
        """
        plugin_name = name or getattr(plugin, "name", plugin.__class__.__name__.lower())

        # Store plugin
        self.plugins[plugin_name] = plugin

        # Register plugin as injectable dependency
        self.container.register_singleton(type(plugin), plugin)

        # Call plugin's mount hook if it exists
        if hasattr(plugin, "_mount"):
            plugin._mount(self)  # noqa: SLF001

        # Mount plugin pages and APIs to web server if enabled
        if hasattr(self, "web_server") and self.web_server:
            self.web_server.mount_plugin_pages(plugin)
            self.web_server.mount_plugin_apis(plugin)

        self.logger.info(f"Mounted plugin: {plugin_name}")

    def include_router(self, router: Any, prefix: str = "") -> None:
        """
        Include a router's handlers in this application.

        Args:
            router: Router instance containing handlers
            prefix: Additional prefix for the router's event types
        """
        # Store router reference
        self.routers.append({"router": router, "prefix": prefix})

        # Register all handlers from the router
        for event_type, handlers in router.get_all_handlers().items():
            # Apply additional prefix if provided
            final_event_type = event_type
            if prefix and not event_type.startswith(f"{prefix}."):
                final_event_type = f"{prefix}.{event_type}"

            # Register each handler
            for handler_info in handlers:
                handler = handler_info["handler"]
                condition = handler_info["condition"]
                original_event_type = handler_info["original_event_type"]

                # Handle Pydantic models vs string events
                if isinstance(original_event_type, type) and hasattr(original_event_type, "event_type"):
                    # It's a Pydantic model - use the wrapped handler approach
                    wrapped_handler = self._wrap_with_model(handler, original_event_type)
                    model_condition = (
                        self._adapt_condition_for_model(condition, original_event_type) if condition else None
                    )
                    self.event_bus.register(final_event_type, wrapped_handler, model_condition)
                else:
                    # String event type - register as-is
                    self.event_bus.register(final_event_type, handler, condition)

                # Register router-specific dependencies
                for dep_type, dep_instance in handler_info.get("dependencies", {}).items():
                    if not self.container.is_registered(dep_type):
                        self.container.register_singleton(dep_type, dep_instance)

        self.logger.info(f"Included router with {len(router.get_all_handlers())} handler groups")

    async def emit(self, event_type: str, data: dict[str, Any], source: str = "system") -> None:
        """Emit an event through the event bus"""
        await self.event_bus.emit(event_type, data, source)

    async def start(self) -> None:
        """Start the application"""
        # Initialize database if needed
        if self.database_url and self.database_url != ":memory:":
            await self._initialize_database()

        # Start event bus
        await self.event_bus.start()

        # Start schedule manager
        await self.schedule_manager.start()

        # Start web server if enabled
        if hasattr(self, "web_server") and self.web_server:
            await self.web_server.start()

        # Initialize plugins
        for plugin_name, plugin in self.plugins.items():
            if hasattr(plugin, "start"):
                try:
                    await plugin.start()
                    self.logger.debug(f"Started plugin: {plugin_name}")
                except Exception as e:
                    self.logger.error(f"Error starting plugin {plugin_name}: {e}")

        self.logger.info("Pantainos application started")

    async def stop(self) -> None:
        """Stop the application"""
        # Stop schedule manager
        await self.schedule_manager.stop()

        # Stop event bus
        await self.event_bus.stop()

        # Stop plugins
        for plugin_name, plugin in self.plugins.items():
            if hasattr(plugin, "stop"):
                try:
                    await plugin.stop()
                    self.logger.debug(f"Stopped plugin: {plugin_name}")
                except Exception as e:
                    self.logger.error(f"Error stopping plugin {plugin_name}: {e}")

        # Close database
        if self.database and hasattr(self.database, "close"):
            await self.database.close()

        self.logger.info("Pantainos application stopped")

    async def run(self) -> None:
        """Run the application until interrupted"""
        await self.start()

        # Use asyncio.Event for clean shutdown instead of sleep loop
        shutdown_event = asyncio.Event()
        try:
            await shutdown_event.wait()
        except KeyboardInterrupt:
            self.logger.info("Shutting down...")
        finally:
            await self.stop()

    async def _initialize_database(self) -> None:
        """Initialize database and repositories"""
        try:
            from .db.database import Database
            from .db.repositories.event_repository import EventRepository
            from .db.repositories.variable_repository import VariableRepository

            self.database = Database(self.database_url)
            await self.database.initialize()

            # Register repositories as injectable services
            self.container.register_factory(EventRepository, lambda: EventRepository(self.database))
            self.container.register_factory(VariableRepository, lambda: VariableRepository(self.database))

            self.logger.info("Database initialized")

        except ImportError:
            self.logger.warning("Database components not available")
        except Exception as e:
            self.logger.error(f"Failed to initialize database: {e}")
            raise
