"""
Documentation generator for extracting handler information from Pantainos applications.

Automatically extracts event handlers, their conditions, dependencies, and
docstrings to generate comprehensive API documentation.
"""

from __future__ import annotations

import inspect
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from pantainos.application import Pantainos


class DocumentationGenerator:
    """
    Generates documentation by extracting handler information from the event system.

    Analyzes event handlers registered with the application to automatically
    generate documentation including signatures, dependencies, conditions, and
    docstrings.

    Args:
        app: The Pantainos application instance to document

    Example:
        >>> app = Pantainos()
        >>> generator = DocumentationGenerator(app)
        >>> docs = generator.extract_handlers_docs()
        >>> print(docs['handlers'])
    """

    def __init__(self, app: Pantainos) -> None:
        """
        Initialize documentation generator with Pantainos application.

        Args:
            app: The Pantainos application to analyze
        """
        self.app = app

    def extract_handlers_docs(self) -> dict[str, Any]:
        """
        Extract documentation from all registered event handlers.

        Analyzes the event bus to extract comprehensive information about
        each handler including their event types, conditions, dependencies,
        and documentation.

        Returns:
            Dictionary containing handler documentation with structure:
            {
                "handlers": [
                    {
                        "event_type": str,
                        "handler_name": str,
                        "docstring": str,
                        "signature": str,
                        "dependencies": list[str],
                        "conditions": dict | None,
                        "source": str
                    }
                ]
            }
        """
        handlers_docs = []

        # Extract handlers from event bus
        if hasattr(self.app, "event_bus") and hasattr(self.app.event_bus, "handlers"):
            for event_type, handler_list in self.app.event_bus.handlers.items():
                for handler_info in handler_list:
                    handler_doc = self._extract_handler_info(event_type, handler_info)
                    handlers_docs.append(handler_doc)

        return {"handlers": handlers_docs}

    def _extract_handler_info(self, event_type: str, handler_info: dict[str, Any]) -> dict[str, Any]:
        """
        Extract detailed information from a single handler.

        Args:
            event_type: The event type this handler responds to
            handler_info: Handler information from the event bus

        Returns:
            Dictionary containing detailed handler information
        """
        handler = handler_info.get("handler")
        condition = handler_info.get("condition")
        source = handler_info.get("source", "core")

        # Extract handler name
        handler_name = getattr(handler, "__name__", str(handler))

        # Extract docstring
        docstring = inspect.getdoc(handler) or ""

        # Extract signature
        try:
            signature = str(inspect.signature(handler))
        except (ValueError, TypeError):
            signature = "Unknown signature"

        # Extract dependencies from function parameters
        dependencies = self._extract_dependencies(handler)

        # Extract condition information
        conditions = self._extract_condition_info(condition)

        return {
            "event_type": event_type,
            "handler_name": handler_name,
            "docstring": docstring,
            "signature": signature,
            "dependencies": dependencies,
            "conditions": conditions,
            "source": source,
        }

    def _extract_dependencies(self, handler: Any) -> list[str]:
        """
        Extract dependency parameter names from handler signature.

        Args:
            handler: The handler function to analyze

        Returns:
            List of parameter names excluding 'event'
        """
        try:
            sig = inspect.signature(handler)
            params = list(sig.parameters.keys())
            # Remove 'event' parameter as it's always present
            return [param for param in params if param != "event"]
        except (ValueError, TypeError):
            return []

    def _extract_condition_info(self, condition: Any) -> dict[str, Any] | None:
        """
        Extract information from handler conditions.

        Args:
            condition: The condition object to analyze

        Returns:
            Dictionary with condition information or None if no condition
        """
        if condition is None:
            return None

        # Extract condition name and basic info
        condition_info = {"name": getattr(condition, "name", str(condition))}

        # Add type information if available
        condition_type = type(condition).__name__
        if condition_type != "MagicMock":  # Avoid test mock names in real usage
            condition_info["type"] = condition_type

        return condition_info
