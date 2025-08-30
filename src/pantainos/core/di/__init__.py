"""
Dependency Injection system for Pantainos

This module provides a lightweight dependency injection framework that supports
explicit dependency injection for event handlers.
"""

from .container import ServiceContainer

__all__ = [
    "ServiceContainer",
]
