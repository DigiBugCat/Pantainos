"""
Events module for Pantainos.

This module provides the event system including event models, conditions,
and type-safe event filtering capabilities.
"""

from .conditions import Condition, equals
from .models import (
    ErrorEvent,
    EventModel,
    GenericEvent,
    MetricEvent,
    PluginHealthEvent,
    SampleEvent,
    SystemEvent,
    SystemHealthEvent,
    WebhookEvent,
)

__all__ = [
    "Condition",
    "ErrorEvent",
    "EventModel",
    "GenericEvent",
    "MetricEvent",
    "PluginHealthEvent",
    "SampleEvent",
    "SystemEvent",
    "SystemHealthEvent",
    "WebhookEvent",
    "equals",
]
