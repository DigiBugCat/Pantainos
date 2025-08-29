"""
Base plugin interface for Pantainos
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Callable
from typing import Any, TypeVar

F = TypeVar("F", bound=Callable[..., Any])


class Plugin(ABC):
    """
    Base class for all Pantainos plugins

    Plugins extend the framework with domain-specific functionality
    like platform integrations, web interfaces, metrics collection, etc.
    """

    def __init__(self, **config: Any) -> None:
        """
        Initialize plugin with configuration

        Args:
            **config: Plugin-specific configuration parameters
        """
        self.config = config
        self.app: Any | None = None
        self.pages: dict[str, dict[str, Any]] = {}
        self.apis: dict[str, dict[str, Any]] = {}

    @property
    @abstractmethod
    def name(self) -> str:
        """Plugin name (used for identification)"""
        pass

    def _mount(self, app: Any) -> None:
        """
        Internal mount hook called by the application.

        Args:
            app: The Pantainos application instance
        """
        self.app = app

    async def emit(self, event_type: str, data: dict[str, Any], source: str | None = None) -> None:
        """
        Emit a namespaced event through the application.

        Args:
            event_type: Event type (will be prefixed with plugin name)
            data: Event data payload
            source: Optional source override (defaults to plugin name)
        """
        if not self.app:
            raise RuntimeError(f"Plugin {self.name} not mounted to application")

        # Create namespaced event type
        full_type = f"{self.name}.{event_type}"
        actual_source = source or self.name

        await self.app.event_bus.emit(full_type, data, actual_source)

    async def start(self) -> None:
        """
        Start the plugin.

        Called when the application starts.
        """
        # Optional hook - override in subclasses if needed
        return

    async def stop(self) -> None:
        """
        Stop the plugin.

        Called when the application stops.
        """
        # Optional hook - override in subclasses if needed
        return

    def page(self, route: str = "") -> Callable[[F], F]:
        """Decorator for registering plugin web pages"""

        def decorator(func: F) -> F:
            self.pages[route] = {"handler": func, "type": "page"}
            return func

        return decorator

    def api(self, route: str) -> Callable[[F], F]:
        """Decorator for registering plugin API endpoints"""

        def decorator(func: F) -> F:
            self.apis[route] = {"handler": func, "type": "api"}
            return func

        return decorator
