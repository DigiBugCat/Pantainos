"""
Type-safe condition system for event filtering

This module provides a type-safe way to filter events using conditions
that are typed to specific event models, ensuring IDE support and
compile-time error checking.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any, Generic, TypeVar

if TYPE_CHECKING:
    from collections.abc import Callable

logger = logging.getLogger(__name__)

# Type variable for event models
E = TypeVar("E")


class Condition(Generic[E]):
    """
    Type-safe condition that can check events of a specific type.

    Conditions can be composed using & (AND), | (OR), and ~ (NOT) operators
    to create complex filtering logic while maintaining type safety.
    """

    def __init__(self, check: Callable[[E], bool], name: str = "") -> None:
        """
        Create a new condition.

        Args:
            check: Function that takes an event and returns True/False
            name: Human-readable name for debugging
        """
        self.check = check
        self.name = name or "unnamed_condition"

    def __call__(self, event: E) -> bool:
        """Allow condition to be called directly"""
        try:
            return self.check(event)
        except Exception as e:
            logger.error(f"Error in condition '{self.name}': {e}")
            return False

    def __and__(self, other: Condition[E]) -> Condition[E]:
        """Combine conditions with AND logic"""

        def combined(event: E) -> bool:
            return self.check(event) and other.check(event)

        return Condition(combined, f"({self.name} AND {other.name})")

    def __or__(self, other: Condition[E]) -> Condition[E]:
        """Combine conditions with OR logic"""

        def combined(event: E) -> bool:
            return self.check(event) or other.check(event)

        return Condition(combined, f"({self.name} OR {other.name})")

    def __invert__(self) -> Condition[E]:
        """Negate condition with NOT logic"""
        return Condition(lambda event: not self.check(event), f"NOT {self.name}")

    def __repr__(self) -> str:
        return f"Condition({self.name})"


def always_true() -> Condition[Any]:
    """Condition that always passes - useful as a default"""
    return Condition(lambda _: True, "always_true")


def always_false() -> Condition[Any]:
    """Condition that never passes - useful for disabling handlers"""
    return Condition(lambda _: False, "always_false")


# Core conditions that work with any event type
def equals(field: str, value: Any) -> Condition[Any]:
    """Check if event field equals a value"""

    def check(event: Any) -> bool:
        if hasattr(event, field):
            return getattr(event, field) == value
        if hasattr(event, "data") and isinstance(event.data, dict):
            return event.data.get(field) == value
        return False

    return Condition(check, f"equals({field}, {value})")


def contains(field: str, value: Any) -> Condition[Any]:
    """Check if event field contains a value"""

    def check(event: Any) -> bool:
        if hasattr(event, field):
            field_value = getattr(event, field)
        elif hasattr(event, "data") and isinstance(event.data, dict):
            field_value = event.data.get(field)
        else:
            return False

        if isinstance(field_value, str):
            return str(value).lower() in field_value.lower()
        if isinstance(field_value, list | tuple):
            return value in field_value
        return False

    return Condition(check, f"contains({field}, {value})")


def greater_than(field: str, value: float) -> Condition[Any]:
    """Check if numeric field is greater than value"""

    def check(event: Any) -> bool:
        if hasattr(event, field):
            field_value = getattr(event, field)
        elif hasattr(event, "data") and isinstance(event.data, dict):
            field_value = event.data.get(field, 0)
        else:
            return False

        try:
            return float(field_value) > float(value)
        except (TypeError, ValueError):
            return False

    return Condition(check, f"greater_than({field}, {value})")


def less_than(field: str, value: float) -> Condition[Any]:
    """Check if numeric field is less than value"""

    def check(event: Any) -> bool:
        if hasattr(event, field):
            field_value = getattr(event, field)
        elif hasattr(event, "data") and isinstance(event.data, dict):
            field_value = event.data.get(field, 0)
        else:
            return False

        try:
            return float(field_value) < float(value)
        except (TypeError, ValueError):
            return False

    return Condition(check, f"less_than({field}, {value})")


def between(field: str, min_val: float, max_val: float) -> Condition[Any]:
    """Check if numeric field is between min and max values (inclusive)"""

    def check(event: Any) -> bool:
        if hasattr(event, field):
            field_value = getattr(event, field)
        elif hasattr(event, "data") and isinstance(event.data, dict):
            field_value = event.data.get(field, 0)
        else:
            return False

        try:
            val = float(field_value)
            return float(min_val) <= val <= float(max_val)
        except (TypeError, ValueError):
            return False

    return Condition(check, f"between({field}, {min_val}, {max_val})")
