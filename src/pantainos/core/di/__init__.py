"""
Dependency Injection system for Pantainos

This module provides a lightweight dependency injection framework that supports
both the legacy (event, ctx) handler style and the new explicit dependency style.
"""

from .container import ServiceContainer
from .inspector import HandlerInspector, HandlerStyle
from .registry import HandlerRegistry

__all__ = [
    "HandlerInspector",
    "HandlerRegistry",
    "HandlerStyle",
    "ServiceContainer",
]
