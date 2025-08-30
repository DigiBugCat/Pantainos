"""
Pantainos - FastAPI-like Python Framework for Event-Driven Applications

A minimal framework for building event-driven applications with type-safe conditions,
plugin architecture, and dependency injection - designed to be imported and extended,
not configured through files.
"""

from collections.abc import Callable
from typing import Any

__version__ = "0.2.1"

# New core architecture - FastAPI-like patterns
from .application import Pantainos

# Core services
from .core.di.container import ServiceContainer
from .core.event_bus import EventBus, HandlerRegistry

# Database repositories
from .db.repositories.base import BaseRepository
from .db.repositories.event_repository import EventRepository
from .db.repositories.variable_repository import VariableRepository
from .events import Condition, EventModel, PluginHealthEvent, SystemHealthEvent
from .plugin import Plugin
from .plugin.base import HealthCheck, HealthStatus


# Decorator function for event handlers
def on_event(event_type: str, **kwargs: Any) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """Decorator for registering event handlers - FastAPI-style"""

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        # Store metadata for application to pick up
        func.event_type = event_type
        func.event_kwargs = kwargs
        return func

    return decorator


__all__ = [
    "BaseRepository",
    "Condition",
    "EventBus",
    "EventModel",
    "EventRepository",
    "HandlerRegistry",
    "HealthCheck",
    "HealthStatus",
    "Pantainos",
    "Plugin",
    "PluginHealthEvent",
    "ServiceContainer",
    "SystemHealthEvent",
    "VariableRepository",
    "__version__",
    "on_event",
]
