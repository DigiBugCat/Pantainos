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

from .conditions import Condition

# Try to import Pydantic, fall back to basic functionality if not available
try:
    from pydantic import BaseModel, Field

    PYDANTIC_AVAILABLE = True
except ImportError:
    # Minimal BaseModel-like class if Pydantic isn't available
    class BaseModel:
        def __init__(self, **data: Any) -> None:
            for key, value in data.items():
                setattr(self, key, value)

    def Field(**_kwargs: Any) -> Any:  # noqa: N802
        """Fallback Field function when Pydantic isn't available"""
        return None

    PYDANTIC_AVAILABLE = False


class Event:
    """
    Basic event structure for non-Pydantic events.

    This is used for simple dict-based events that don't need validation.
    """

    def __init__(self, type: str, data: dict[str, Any], source: str = "system") -> None:
        self.type = type
        self.data = data
        self.source = source


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


# Alias for compatibility with existing code
EventType = str
