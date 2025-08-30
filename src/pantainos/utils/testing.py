"""
Testing utilities for Pantainos
"""

from typing import Any

from pantainos.runtime.types import Event


def create_mock_event(event_type: str, **data: Any) -> Event:
    """
    Create a mock event for testing

    Args:
        event_type: The event type
        **data: Event data as keyword arguments

    Returns:
        Event object
    """
    return Event(type=event_type, data=data, source="test")
