"""
Pantainos - FastAPI-like Python Framework for Event-Driven Applications

A minimal framework for building event-driven applications with type-safe conditions,
plugin architecture, and dependency injection - designed to be imported and extended,
not configured through files.
"""

__version__ = "0.1.0"

# New core architecture - FastAPI-like patterns
from collections.abc import Callable
from typing import Any

from .application import Pantainos
from .conditions import Condition

# Core services
from .core.di.container import ServiceContainer
from .core.event_bus import EventBus, HandlerRegistry

# Database repositories
from .db.repositories.base import BaseRepository
from .db.repositories.event_repository import EventRepository
from .db.repositories.variable_repository import VariableRepository
from .events import Event, EventModel
from .plugin import Plugin
from .router import Router


# Decorator function for event handlers
def on_event(event_type: str, **kwargs: Any) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """Decorator for registering event handlers - FastAPI-style"""

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        # Store metadata for application to pick up
        func._event_type = event_type  # noqa: SLF001
        func._event_kwargs = kwargs  # noqa: SLF001
        return func

    return decorator


__all__ = [
    "BaseRepository",
    "Condition",
    "Event",
    "EventBus",
    "EventModel",
    "EventRepository",
    "HandlerRegistry",
    "Pantainos",
    "Plugin",
    "Router",
    "ServiceContainer",
    "VariableRepository",
    "__version__",
    "on_event",
]
