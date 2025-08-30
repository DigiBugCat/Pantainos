"""
ASGI application management for Pantainos.

This module handles FastAPI integration, ASGI lifespan management,
and web route setup for Pantainos applications.
"""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from collections.abc import AsyncGenerator

if TYPE_CHECKING:
    from pantainos.application import Pantainos

# FastAPI imports with availability check
try:
    from fastapi import FastAPI
    from fastapi.responses import HTMLResponse

    WEB_AVAILABLE = True
except ImportError:
    WEB_AVAILABLE = False
    # Fallback types for when FastAPI is not available
    FastAPI = Any  # type: ignore[misc,assignment]
    HTMLResponse = Any  # type: ignore[misc,assignment]

logger = logging.getLogger(__name__)


class ASGIManager:
    """
    Manages ASGI application lifecycle and web routes for Pantainos.

    Handles FastAPI integration, lifespan events, and route setup.
    """

    def __init__(self, app: Pantainos) -> None:
        """Initialize ASGI manager with Pantainos app instance."""
        self.app = app
        self.fastapi = self._create_fastapi_app()

    def _create_fastapi_app(self) -> FastAPI:
        """Create and configure FastAPI application."""
        if not WEB_AVAILABLE:
            raise RuntimeError("Web dependencies not available. Install with: pip install fastapi uvicorn nicegui")

        fastapi_app = FastAPI(
            title="Pantainos API",
            description="REST API for Pantainos event-driven application",
            version="0.1.0",
            lifespan=self.lifespan,
        )

        self._setup_web_routes(fastapi_app)
        return fastapi_app

    @asynccontextmanager
    async def lifespan(self, _fastapi_app: FastAPI) -> AsyncGenerator[None, None]:
        """ASGI lifespan protocol - manages startup/shutdown."""
        # Startup
        await self._startup()
        yield
        # Shutdown
        await self._shutdown()

    async def _startup(self) -> None:
        """Internal startup logic."""
        await self.app.lifecycle_manager.start(
            database_url=self.app.database_url,
            master_key=self.app.master_key,
            emit_startup_event=True,
        )
        # Update database reference after initialization
        self.app.database = self.app.db_initializer.database

        logger.info("Pantainos application started via ASGI")

    async def _shutdown(self) -> None:
        """Internal shutdown logic."""
        await self.app.lifecycle_manager.stop()

        logger.info("Pantainos application stopped gracefully")

    def _setup_web_routes(self, fastapi_app: FastAPI) -> None:
        """Setup web routes."""

        @fastapi_app.get("/ui/docs", response_class=HTMLResponse)
        def get_documentation() -> str:
            """Serve styled documentation page."""
            try:
                from pantainos.web.ui import DocumentationUI

                doc_ui = DocumentationUI(self.app)
                return doc_ui.create_documentation_page()
            except RuntimeError:
                return "<html><body><h1>Documentation unavailable</h1><p>NiceGUI not installed</p></body></html>"

        @fastapi_app.get("/ui/events", response_class=HTMLResponse)
        def get_event_explorer() -> str:
            """Serve Event Explorer interface."""
            try:
                from pantainos.web.event_explorer import NICEGUI_AVAILABLE

                if not NICEGUI_AVAILABLE:
                    return "<html><body><h1>Event Explorer unavailable</h1><p>NiceGUI not installed</p></body></html>"
                # Placeholder implementation
                return """<html><head><title>Event Explorer</title><style>body { font-family: monospace; background: #1a1a1a; color: #fff; padding: 20px; }</style></head><body><h1>🔍 Event Explorer</h1><p><strong>Note:</strong> Event Explorer requires NiceGUI app context.</p></body></html>"""
            except Exception:
                return "<html><body><h1>Event Explorer Error</h1></body></html>"

    def __call__(self) -> FastAPI:
        """Make ASGI manager callable to return FastAPI app."""
        return self.fastapi
