"""
Dependency Injection system for Pantainos

This module provides a lightweight dependency injection framework that supports
both the legacy (event, ctx) handler style and the new explicit dependency style.
"""

from .container import ServiceContainer

__all__ = [
    "ServiceContainer",
]
