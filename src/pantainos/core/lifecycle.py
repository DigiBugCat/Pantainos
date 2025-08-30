"""
Application lifecycle management for Pantainos.

This module handles the startup and shutdown of application components
in the correct order, including event bus, scheduler, plugins, and database.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pantainos.core.di.container import ServiceContainer
    from pantainos.core.event_bus import EventBus
    from pantainos.db.initializer import DatabaseInitializer
    from pantainos.plugin.manager import PluginRegistry
    from pantainos.scheduler import ScheduleManager

logger = logging.getLogger(__name__)


class LifecycleManager:
    """
    Manages the startup and shutdown lifecycle of Pantainos application components.

    Coordinates the initialization and cleanup of:
    - Database connections
    - Event bus
    - Schedule manager
    - Plugin registry
    - Web server (if enabled)
    """

    def __init__(
        self,
        container: ServiceContainer,
        event_bus: EventBus,
        schedule_manager: ScheduleManager,
        plugin_registry: PluginRegistry,
        db_initializer: DatabaseInitializer,
    ) -> None:
        """Initialize lifecycle manager with application components."""
        self.container = container
        self.event_bus = event_bus
        self.schedule_manager = schedule_manager
        self.plugin_registry = plugin_registry
        self.db_initializer = db_initializer

    async def start(
        self,
        database_url: str | None = None,
        master_key: str | None = None,
        emit_startup_event: bool = True,
    ) -> None:
        """
        Start the application components in the correct order.

        Args:
            database_url: Database connection URL (optional)
            master_key: Master encryption key for secure storage (optional)
            emit_startup_event: Whether to emit system.startup event
        """
        # Initialize a database if needed
        if database_url and database_url != ":memory:":
            await self.db_initializer.initialize(database_url, master_key)

        # Start event bus
        await self.event_bus.start()

        # Start schedule manager
        await self.schedule_manager.start()

        # Start web server if enabled
        # Note: Web server startup is handled via ASGI lifespan in production
        # This is mainly for standalone start() calls

        # Initialize plugins
        await self.plugin_registry.start_all()

        # Emit startup event for handlers to react to
        if emit_startup_event:
            from pantainos.events import GenericEvent

            event = GenericEvent(type="system.startup", data={"timestamp": "startup"}, source="system")
            await self.event_bus.emit(event)

        logger.info("Pantainos application started")

    async def stop(self) -> None:
        """Stop the application components in reverse order."""
        # Stop schedule manager
        await self.schedule_manager.stop()

        # Stop event bus
        await self.event_bus.stop()

        # Stop plugins
        await self.plugin_registry.stop_all()

        # Close database
        await self.db_initializer.close()

        logger.info("Pantainos application stopped")
