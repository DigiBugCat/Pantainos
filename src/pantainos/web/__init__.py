"""
Web interface module for Pantainos.

Provides FastAPI + NiceGUI integration for web-based application management,
documentation, and plugin configuration interfaces.
"""

from .server import WebServer

__all__ = ["WebServer"]
