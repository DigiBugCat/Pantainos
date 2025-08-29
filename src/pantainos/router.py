"""
Pantainos Router - FastAPI-like router for organizing handlers

This module provides the Router class for organizing event handlers
into logical groups that can be included in the main application.
"""

from __future__ import annotations

from collections import defaultdict
from typing import TYPE_CHECKING, Any, TypeVar

if TYPE_CHECKING:
    from collections.abc import Awaitable, Callable

    from .conditions import Condition

from .events import EventModel

# Type variable for event models
E = TypeVar("E", bound="EventModel")


class Router:
    """
    Router for organizing event handlers into logical groups.

    Similar to FastAPI's APIRouter, this allows you to organize handlers
    by domain or functionality and include them in the main app.

    Example:
        # chat_router.py
        from pantainos import Router
        from .events import ChatMessage
        from .plugins import TwitchPlugin

        router = Router(prefix="twitch")

        @router.on(ChatMessage, when=ChatMessage.command("hello"))
        async def hello_cmd(event: ChatMessage, twitch: TwitchPlugin):
            await twitch.send_message(f"Hello {event.user}!")

        # main.py
        from pantainos import Pantainos
        from .chat_router import router

        app = Pantainos()
        app.include_router(router)  # Handlers get "twitch." prefix
    """

    def __init__(self, prefix: str = "", dependencies: dict[type, Any] | None = None) -> None:
        """
        Initialize router.

        Args:
            prefix: Event type prefix for all handlers in this router
            dependencies: Additional dependencies to inject for this router's handlers
        """
        self.prefix = prefix
        self.dependencies = dependencies or {}
        self.handlers: dict[str, list[dict[str, Any]]] = defaultdict(list)

    def on(
        self, event_type: str | type[E], *, when: Condition[E] | None = None
    ) -> Callable[[Callable[..., Awaitable[Any]]], Callable[..., Awaitable[Any]]]:
        """
        Register an event handler with optional conditions.

        Args:
            event_type: Event type (string) or EventModel class
            when: Optional condition for filtering events

        Returns:
            Decorator function

        Example:
            @router.on(ChatMessage, when=ChatMessage.command("hello"))
            async def hello_cmd(event: ChatMessage, twitch: TwitchPlugin):
                await twitch.send_message(f"Hello {event.user}!")
        """

        def decorator(handler: Callable[..., Awaitable[Any]]) -> Callable[..., Awaitable[Any]]:
            # Determine actual event type string
            if isinstance(event_type, type) and issubclass(event_type, EventModel):
                # It's a Pydantic model - get the event_type string
                actual_event_type = event_type.event_type
            else:
                # String event type
                actual_event_type = str(event_type)

            # Apply prefix if configured
            if self.prefix and not actual_event_type.startswith(f"{self.prefix}."):
                # Only add prefix if not already present
                if actual_event_type.startswith(self.prefix):
                    # Handle case where event_type is just the prefix
                    actual_event_type = f"{self.prefix}.{actual_event_type}"
                else:
                    actual_event_type = f"{self.prefix}.{actual_event_type}"

            # Store handler info
            handler_info = {
                "handler": handler,
                "condition": when,
                "name": handler.__name__,
                "event_type": actual_event_type,
                "original_event_type": event_type,
                "dependencies": self.dependencies.copy(),  # Copy router-level dependencies
            }

            self.handlers[actual_event_type].append(handler_info)

            return handler

        return decorator

    def include_router(self, router: Router, prefix: str = "") -> None:
        """
        Include another router's handlers in this router.

        Args:
            router: Router to include
            prefix: Additional prefix for the included router's handlers
        """
        for event_type, handlers in router.handlers.items():
            # Apply additional prefix if provided
            if prefix and not event_type.startswith(f"{prefix}."):
                event_type = f"{prefix}.{event_type}"

            # Add handlers to our collection
            for handler_info in handlers:
                # Update event type with new prefix
                updated_handler_info = handler_info.copy()
                updated_handler_info["event_type"] = event_type

                # Merge dependencies
                merged_dependencies = self.dependencies.copy()
                merged_dependencies.update(handler_info["dependencies"])
                updated_handler_info["dependencies"] = merged_dependencies

                self.handlers[event_type].append(updated_handler_info)

    def add_dependency(self, dependency_type: type, instance: Any) -> None:
        """
        Add a dependency that will be injected into all handlers in this router.

        Args:
            dependency_type: Type of the dependency
            instance: Instance to inject
        """
        self.dependencies[dependency_type] = instance

    def get_all_handlers(self) -> dict[str, list[dict[str, Any]]]:
        """Get all handlers registered with this router."""
        return dict(self.handlers)
