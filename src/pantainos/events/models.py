"""
Event system with Pydantic models and type-safe conditions

This module provides the EventModel base class that allows events to define
their own type-safe conditions as class methods, enabling clean and discoverable
event filtering.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, ClassVar

if TYPE_CHECKING:
    from collections.abc import Callable

from pydantic import BaseModel, Field

from .conditions import Condition


class EventModel(BaseModel):
    """
    Base class for typed events with built-in condition support.

    This class allows events to define their own conditions as class methods,
    providing type-safe filtering and IDE autocomplete support.
    """

    # Event type that links this model to string events
    event_type: ClassVar[str]

    # Optional source tracking
    source: str = Field(default="system", description="Source that emitted this event")

    @classmethod
    def condition(cls, check: Callable[[EventModel], bool], name: str = "") -> Condition[EventModel]:
        """
        Create a typed condition for this event model.

        This is the base method that all event-specific conditions should use
        to ensure proper typing.

        Args:
            check: Function that takes an instance of this event and returns bool
            name: Human-readable name for debugging

        Returns:
            Type-safe condition that only works with this event type
        """
        return Condition[cls](check, name or f"{cls.__name__}_condition")

    # Common conditions that work with any event model
    @classmethod
    def source_is(cls, source: str) -> Condition[EventModel]:
        """Check if event came from a specific source"""
        return cls.condition(lambda event: event.source == source, f"source_is({source})")

    @classmethod
    def has_field(cls, field_name: str) -> Condition[EventModel]:
        """Check if event has a specific field"""
        return cls.condition(lambda event: hasattr(event, field_name), f"has_field({field_name})")

    @classmethod
    def field_equals(cls, field_name: str, value: Any) -> Condition[EventModel]:
        """Check if a field equals a specific value"""

        def check(event: EventModel) -> bool:
            if not hasattr(event, field_name):
                return False
            return getattr(event, field_name) == value

        return cls.condition(check, f"field_equals({field_name}, {value})")

    @classmethod
    def field_contains(cls, field_name: str, substring: str) -> Condition[EventModel]:
        """Check if a string field contains a substring (case-insensitive)"""

        def check(event: EventModel) -> bool:
            if not hasattr(event, field_name):
                return False
            field_value = getattr(event, field_name)
            if not isinstance(field_value, str):
                return False
            return substring.lower() in field_value.lower()

        return cls.condition(check, f"field_contains({field_name}, {substring})")


# Common Event Models


class GenericEvent(EventModel):
    """
    Generic event for dynamic/unknown event types.

    Use this for simple events, testing, or when the schema is not known.
    """

    # Event type override for routing
    type: str = Field(description="The actual event type for routing")

    # Flexible data field
    data: dict[str, Any] = Field(default_factory=dict, description="Event payload")

    @property
    def event_type(self) -> str:
        """Return the instance-specific event type"""
        return self.type


class SystemEvent(EventModel):
    """System-level events (startup, shutdown, etc.)"""

    event_type: ClassVar[str] = "system"

    action: str = Field(description="System action (startup, shutdown, reload, etc.)")
    version: str | None = Field(default=None, description="Application version")
    hostname: str | None = Field(default=None, description="System hostname")
    pid: int | None = Field(default=None, description="Process ID")
    uptime: float | None = Field(default=None, description="System uptime in seconds")
    extra_metadata: dict[str, Any] = Field(default_factory=dict, description="Additional dynamic metadata")


class SampleEvent(EventModel):
    """Sample event for testing purposes"""

    event_type: ClassVar[str] = "test.event"

    message: str = Field(default="Test message", description="Test message")
    data: dict[str, Any] = Field(default_factory=dict, description="Test data")


class WebhookEvent(EventModel):
    """Event from webhook endpoints"""

    event_type: ClassVar[str] = "webhook.received"

    endpoint: str = Field(description="Webhook endpoint path")
    method: str = Field(default="POST", description="HTTP method")
    headers: dict[str, str] = Field(default_factory=dict, description="Request headers")
    body: dict[str, Any] = Field(default_factory=dict, description="Request body")


class ErrorEvent(EventModel):
    """Error event for exception handling"""

    event_type: ClassVar[str] = "error"

    error: str = Field(description="Error message")
    error_type: str = Field(default="Exception", description="Type of error")
    traceback: str | None = Field(default=None, description="Traceback if available")
    module: str | None = Field(default=None, description="Module where error occurred")
    function: str | None = Field(default=None, description="Function where error occurred")
    line_number: int | None = Field(default=None, description="Line number where error occurred")
    user_id: str | None = Field(default=None, description="User ID associated with error")
    request_id: str | None = Field(default=None, description="Request ID associated with error")
    extra_context: dict[str, Any] = Field(default_factory=dict, description="Additional dynamic context")


class MetricEvent(EventModel):
    """Metric/monitoring event"""

    event_type: ClassVar[str] = "metric.update"

    metrics: dict[str, float] = Field(default_factory=dict, description="Metric values")
    timestamp: float | None = Field(default=None, description="Metric timestamp")
    tags: dict[str, str] = Field(default_factory=dict, description="Metric tags")


class PluginHealthEvent(EventModel):
    """Plugin health status event"""

    event_type: ClassVar[str] = "plugin.health"

    plugin_name: str = Field(description="Name of the plugin")
    status: str = Field(description="Health status (healthy, degraded, unhealthy)")
    message: str = Field(description="Health check message")
    check_duration_ms: float | None = Field(default=None, description="Time taken for health check in milliseconds")
    details: dict[str, Any] = Field(default_factory=dict, description="Additional health details")

    @classmethod
    def from_health_check(
        cls, plugin_name: str, health_check: Any, check_duration_ms: float | None = None
    ) -> PluginHealthEvent:
        """Create event from a HealthCheck result"""
        return cls(
            plugin_name=plugin_name,
            status=health_check.status.value,
            message=health_check.message,
            check_duration_ms=check_duration_ms,
            details=health_check.details or {},
        )


class SystemHealthEvent(EventModel):
    """Overall system health status event"""

    event_type: ClassVar[str] = "system.health"

    overall_status: str = Field(description="Overall system health status")
    healthy_plugins: int = Field(default=0, description="Number of healthy plugins")
    degraded_plugins: int = Field(default=0, description="Number of degraded plugins")
    unhealthy_plugins: int = Field(default=0, description="Number of unhealthy plugins")
    plugin_statuses: dict[str, str] = Field(default_factory=dict, description="Individual plugin health statuses")
    check_summary: dict[str, Any] = Field(default_factory=dict, description="Health check summary details")
