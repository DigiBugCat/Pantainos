"""
Web server integrating FastAPI and NiceGUI for Pantainos applications.

Provides REST API endpoints for application management and a NiceGUI-based
web interface for documentation and plugin configuration.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from fastapi import FastAPI
    from fastapi.responses import HTMLResponse

    from pantainos.application import Pantainos
    from pantainos.plugin.base import Plugin

    WEB_AVAILABLE = True
else:
    try:
        from fastapi import FastAPI
        from fastapi.responses import HTMLResponse

        WEB_AVAILABLE = True
    except ImportError:
        WEB_AVAILABLE = False
        FastAPI = Any  # type: ignore[assignment,misc]
        HTMLResponse = Any  # type: ignore[assignment,misc]


class WebServer:
    """
    Web server providing FastAPI REST API and NiceGUI interface.

    Integrates with Pantainos applications to provide web-based management,
    documentation, and plugin configuration interfaces.

    Usage:
        app = Pantainos()
        web_server = WebServer(app)
        await web_server.start(port=8080)

    Args:
        pantainos_app: The Pantainos application instance

    Example:
        >>> app = Pantainos()
        >>> web_server = WebServer(app)
        >>> await web_server.start()
    """

    def __init__(self, pantainos_app: Pantainos) -> None:
        """
        Initialize web server with Pantainos application.

        Args:
            pantainos_app: The Pantainos application to serve
        """
        if not WEB_AVAILABLE:
            raise RuntimeError("Web dependencies not available. Install with: pip install fastapi uvicorn nicegui")

        self.app = pantainos_app
        self.fastapi = FastAPI(
            title="Pantainos API", description="REST API for Pantainos event-driven application", version="0.1.0"
        )
        self.plugin_pages: dict[str, dict[str, Any]] = {}

        # Register documentation route - NiceGUI components require proper setup
        self._setup_documentation_route()

    def _setup_documentation_route(self) -> None:
        """Setup documentation route for styled HTML interface."""

        @self.fastapi.get("/ui/docs", response_class=HTMLResponse)
        def get_documentation() -> str:
            """Serve styled documentation page"""
            try:
                from .ui import DocumentationUI

                doc_ui = DocumentationUI(self.app)
                return doc_ui.create_documentation_page()
            except RuntimeError:
                return "<html><body><h1>Documentation unavailable</h1><p>NiceGUI not installed</p></body></html>"

        @self.fastapi.get("/ui/events", response_class=HTMLResponse)
        def get_event_explorer() -> str:
            """Serve Event Explorer interface"""
            try:
                from .event_explorer import NICEGUI_AVAILABLE

                if not NICEGUI_AVAILABLE:
                    return "<html><body><h1>Event Explorer unavailable</h1><p>NiceGUI not installed</p></body></html>"

                # Note: NiceGUI requires its own app context for proper rendering
                # This is a placeholder - actual NiceGUI integration needs ui.run()
                return """
                <html>
                <head>
                    <title>Event Explorer</title>
                    <style>
                        body { font-family: monospace; background: #1a1a1a; color: #fff; padding: 20px; }
                        .notice { background: #2a2a2a; padding: 20px; border-radius: 5px; margin: 20px 0; }
                        code { background: #333; padding: 2px 5px; border-radius: 3px; }
                    </style>
                </head>
                <body>
                    <h1>🔍 Event Explorer</h1>
                    <div class="notice">
                        <p><strong>Note:</strong> Event Explorer requires NiceGUI app context.</p>
                        <p>To use the Event Explorer, start the application with NiceGUI integration:</p>
                        <pre><code>from pantainos import Pantainos
from pantainos.web.event_explorer import EventExplorer
from nicegui import ui

app = Pantainos(database_url="sqlite:///pantainos.db")
explorer = EventExplorer(app)

@ui.page('/events')
def events_page():
    explorer.create_interface()

ui.run(port=8080)</code></pre>
                    </div>
                </body>
                </html>
                """
            except Exception as e:
                return f"<html><body><h1>Error</h1><p>{e!s}</p></body></html>"

    def mount_plugin_pages(self, plugin: Plugin) -> None:
        """
        Mount web pages for a plugin as UI routes.

        Args:
            plugin: Plugin instance with registered pages
        """
        if not hasattr(plugin, "pages"):
            return

        pages = getattr(plugin, "pages", None)
        if not pages or not isinstance(pages, dict):
            return

        plugin_name = plugin.name
        self.plugin_pages[plugin_name] = pages

        # Register each page as a UI route with FastAPI
        base_path = f"/ui/plugins/{plugin_name}"

        for route_path, page_info in pages.items():
            handler = page_info.get("handler")
            if not handler:
                continue

            # Construct full UI path
            full_path = f"{base_path}/" if route_path == "" else f"{base_path}/{route_path}"

            # Register page as GET route
            self.fastapi.get(full_path)(handler)

    def mount_plugin_apis(self, plugin: Plugin) -> None:
        """
        Mount API endpoints for a plugin to the FastAPI application.

        Args:
            plugin: Plugin instance with registered APIs
        """
        if not hasattr(plugin, "apis"):
            return

        apis = getattr(plugin, "apis", None)
        if not apis or not isinstance(apis, dict):
            return

        plugin_name = plugin.name
        base_path = f"/api/plugins/{plugin_name}"

        # Register each API endpoint with FastAPI
        for route_path, endpoint_info in apis.items():
            handler = endpoint_info.get("handler")
            if not handler:
                continue

            # Construct full path
            full_path = f"{base_path}{route_path}"

            # Register endpoint with FastAPI (determine HTTP method by route pattern)
            if route_path.endswith("/reset") or "reset" in route_path:
                self.fastapi.post(full_path)(handler)  # Reset endpoints are POST
            elif route_path == "/events":
                self.fastapi.post(full_path)(handler)  # Events endpoint is POST
            else:  # Metrics and other endpoints - GET
                self.fastapi.get(full_path)(handler)

    def get_fastapi_app(self) -> FastAPI:
        """Get the FastAPI application instance."""
        return self.fastapi

    async def start(self, port: int = 8080, host: str = "127.0.0.1") -> None:
        """
        Start the web server using uvicorn.

        Args:
            port: Port to bind to (default: 8080)
            host: Host to bind to (default: "127.0.0.1" for local access)
        """
        try:
            import uvicorn
        except ImportError as e:
            raise RuntimeError("uvicorn not available. Install with: pip install uvicorn") from e

        # Create server configuration for async context
        config = uvicorn.Config(app=self.fastapi, port=port, host=host, log_level="info")
        server = uvicorn.Server(config)

        # Start server in async context
        await server.serve()
