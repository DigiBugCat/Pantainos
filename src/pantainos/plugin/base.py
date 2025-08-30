"""
Base plugin interface for Pantainos
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Callable
from dataclasses import dataclass
from enum import Enum
from typing import TYPE_CHECKING, Any, TypeVar, overload

if TYPE_CHECKING:
    from datetime import datetime

from pantainos.events import EventModel, GenericEvent

F = TypeVar("F", bound=Callable[..., Any])


class HealthStatus(Enum):
    """Plugin health status levels"""

    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"


@dataclass
class HealthCheck:
    """Health check result for a plugin"""

    status: HealthStatus
    message: str
    timestamp: datetime
    details: dict[str, Any] | None = None

    def __post_init__(self) -> None:
        if self.details is None:
            self.details = {}

    @classmethod
    def healthy(cls, message: str, **details: Any) -> HealthCheck:
        """Create a healthy status health check"""
        from datetime import datetime

        return cls(status=HealthStatus.HEALTHY, message=message, timestamp=datetime.now(), details=details)

    @classmethod
    def degraded(cls, message: str, **details: Any) -> HealthCheck:
        """Create a degraded status health check"""
        from datetime import datetime

        return cls(status=HealthStatus.DEGRADED, message=message, timestamp=datetime.now(), details=details)

    @classmethod
    def unhealthy(cls, message: str, **details: Any) -> HealthCheck:
        """Create an unhealthy status health check"""
        from datetime import datetime

        return cls(status=HealthStatus.UNHEALTHY, message=message, timestamp=datetime.now(), details=details)


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

    @abstractmethod
    async def health_check(self) -> HealthCheck:
        """
        Check the health status of the plugin.

        Returns:
            HealthCheck: Current health status with message and optional details

        Example:
            async def health_check(self) -> HealthCheck:
                try:
                    await self.api_client.ping()
                    return HealthCheck.healthy("API connection successful")
                except Exception as e:
                    return HealthCheck.unhealthy(f"API connection failed: {e}")
        """
        pass

    def _mount(self, app: Any) -> None:
        """
        Internal mount hook called by the application.

        Args:
            app: The Pantainos application instance
        """
        self.app = app

    @overload
    async def emit(self, event_type_or_event: EventModel, data: None = None, source: str | None = None) -> None: ...

    @overload
    async def emit(self, event_type_or_event: str, data: dict[str, Any], source: str | None = None) -> None: ...

    async def emit(
        self, event_type_or_event: str | EventModel, data: dict[str, Any] | None = None, source: str | None = None
    ) -> None:
        """
        Emit a namespaced event through the application.

        Args:
            event_type_or_event: Event type string or EventModel instance
            data: Event data payload (for string event types)
            source: Optional source override (defaults to plugin name)
        """
        if not self.app:
            raise RuntimeError(f"Plugin {self.name} not mounted to application")

        if isinstance(event_type_or_event, EventModel):
            # Direct EventModel emission - namespace the event type
            event = event_type_or_event
            namespaced_type = f"{self.name}.{event.event_type}"
            # Create a new instance with namespaced type
            event_data = event.model_dump()
            event_data.pop("source", None)  # Remove source to override
            namespaced_event = GenericEvent(type=namespaced_type, data=event_data, source=source or self.name)
            await self.app.event_bus.emit(namespaced_event)
        else:
            # String-based emission - create GenericEvent
            if data is None:
                data = {}

            full_type = f"{self.name}.{event_type_or_event}"
            actual_source = source or self.name

            event = GenericEvent(type=full_type, data=data, source=actual_source)
            await self.app.event_bus.emit(event)

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
