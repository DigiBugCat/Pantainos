"""
Pantainos Application - FastAPI-like event-driven framework

This module provides the main Pantainos class with app-bound decorators,
type-safe event filtering, and plugin mounting capabilities.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any, TypeVar

from .utils.logging import setup_logging

if TYPE_CHECKING:
    from collections.abc import Awaitable, Callable

    from fastapi import FastAPI

    from .events import Condition

from .core.di.container import ServiceContainer
from .core.event_bus import EventBus
from .db.initializer import DatabaseInitializer
from .events import EventModel, GenericEvent
from .plugin.manager import PluginRegistry
from .scheduler import CronTask, IntervalTask, Schedule, ScheduleManager, WatchTask
from .utils.runner import ApplicationRunner

# Type variable for event models
E = TypeVar("E", bound="EventModel")

logger = logging.getLogger(__name__)


class Pantainos:
    """
    Main Pantainos application class with FastAPI-like decorators.

    Provides app-bound decorators for event handling, type-safe conditions,
    and plugin mounting capabilities.
    """

    def __init__(
        self,
        database_url: str = "sqlite:///pantainos.db",
        debug: bool = False,
        master_key: str | None = None,
        **kwargs: Any,
    ) -> None:
        """
        Initialize Pantainos application.

        Args:
            database_url: Database connection URL
            debug: Enable debug logging
            master_key: Master encryption key for secure storage (optional)
            **kwargs: Additional application parameters
        """
        self.database_url = database_url
        self.debug = debug
        self.master_key = master_key
        self.kwargs = kwargs

        # Core components - no global state!
        self.container = ServiceContainer()
        self.event_bus = EventBus(self.container)
        self.schedule_manager = ScheduleManager(self.event_bus, self.container)
        self.plugin_registry = PluginRegistry(self.container)

        # Component managers
        self.db_initializer = DatabaseInitializer(self.container)
        self.runner = ApplicationRunner(self)

        # ASGI manager - import here to avoid circular imports
        from .core.asgi import ASGIManager

        self.asgi_manager = ASGIManager(self)

        # Lifecycle manager
        from .core.lifecycle import LifecycleManager

        self.lifecycle_manager = LifecycleManager(
            self.container,
            self.event_bus,
            self.schedule_manager,
            self.plugin_registry,
            self.db_initializer,
        )

        # Database will be initialized on startup
        self.database: Any | None = None

        if debug:
            setup_logging(debug=True, app_name="pantainos")

        self.logger = logging.getLogger(__name__)

    def __call__(self) -> FastAPI:
        """Make Pantainos callable as ASGI app"""
        return self.asgi_manager()

    def run(self, **kwargs: Any) -> None:
        """Run the application using uvicorn"""
        self.runner.run(**kwargs)

    @property
    def plugins(self) -> dict[str, Any]:
        """Backward compatibility property for accessing mounted plugins."""
        return self.plugin_registry.get_all()

    def on(
        self, event_type: str | type[E] | Schedule, *, when: Condition[E] | None = None
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
            # Schedule instance - register directly
            if isinstance(event_type, Schedule):
                self._register_scheduled_handler(handler, event_type)

            # Schedule class - create instance and register (must come before EventModel case)
            elif isinstance(event_type, type) and issubclass(event_type, Schedule):
                schedule_instance = event_type()
                self._register_scheduled_handler(handler, schedule_instance)

            # EventModel class - register directly with event_type
            elif isinstance(event_type, type) and issubclass(event_type, EventModel):
                actual_event_type = event_type.event_type
                self.event_bus.register(actual_event_type, handler, when)

            # String event type - register directly
            else:
                self.event_bus.register(str(event_type), handler, when)

            return handler

        return decorator

    def _register_scheduled_handler(self, handler: Callable[..., Awaitable[Any]], schedule: Schedule) -> None:
        """
        Register a handler to execute on a schedule (interval, cron, or watch).
        """
        from .scheduler import Cron, Interval, Watch

        self.logger.debug(f"Registering schedule: {type(schedule).__name__} - {schedule}")

        # Create a typed task based on a schedule type
        if isinstance(schedule, Interval):
            task: IntervalTask | CronTask | WatchTask = IntervalTask(
                handler=handler,
                schedule=schedule,
            )
        elif isinstance(schedule, Cron):
            task = CronTask(
                handler=handler,
                schedule=schedule,
                next_execution=self.schedule_manager.calculate_next_cron_time(schedule),
            )
        elif isinstance(schedule, Watch):
            task = WatchTask(
                handler=handler,
                schedule=schedule,
            )
        else:
            self.logger.warning(f"Unknown schedule type: {schedule.event_type}")
            return

        self.schedule_manager.scheduled_tasks.append(task)
        self.logger.debug(f"Registered scheduled handler: {handler.__name__} for {schedule.event_type}")

    def mount(self, plugin: Any, name: str | None = None) -> None:
        """
        Integrate a plugin into the application, making it available for dependency injection
        and allowing it to contribute web pages/APIs.
        """
        web_server = getattr(self, "web_server", None)
        self.plugin_registry.mount(plugin, name, web_server)

    async def emit(
        self, event_type_or_event: str | EventModel, data: dict[str, Any] | None = None, source: str = "system"
    ) -> None:
        """
        Broadcast an event to all registered handlers.

        Supports both typed EventModel instances and legacy dict-based events.

        Args:
            event_type_or_event: Either a typed EventModel instance or string event type
            data: Event payload data (only used when event_type_or_event is a string)
            source: Origin of the event (defaults to "system")

        Examples:
            # Typed event (recommended)
            await app.emit(SystemEvent(action="startup", version="1.0.0"))

            # dict-based events for generic events
            await app.emit("user.login", {"user_id": "123"}, source="web")
        """
        if isinstance(event_type_or_event, EventModel):
            # Direct typed event emission
            await self.event_bus.emit(event_type_or_event)
        else:
            # Legacy string-based emission - create GenericEvent
            if data is None:
                data = {}
            event = GenericEvent(type=event_type_or_event, data=data, source=source)
            await self.event_bus.emit(event)

    async def start(self) -> None:
        """Start the application"""
        await self.lifecycle_manager.start(
            database_url=self.database_url,
            master_key=self.master_key,
            emit_startup_event=True,
        )
        # Update database reference after initialization
        self.database = self.db_initializer.database

    async def stop(self) -> None:
        """Stop the application"""
        await self.lifecycle_manager.stop()

    async def _initialize_database(self) -> None:
        """Initialize database using DatabaseInitializer."""
        self.database = await self.db_initializer.initialize(self.database_url, self.master_key)
