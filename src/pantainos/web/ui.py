"""
NiceGUI web interface components for Pantainos documentation.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from nicegui import ui

    NICEGUI_AVAILABLE = True
else:
    try:
        from nicegui import ui

        NICEGUI_AVAILABLE = True
    except ImportError:
        NICEGUI_AVAILABLE = False
        ui = Any  # type: ignore[assignment,misc]

if TYPE_CHECKING:
    from pantainos.application import Pantainos


class DocumentationUI:
    """
    NiceGUI-based documentation interface for Pantainos applications.
    """

    def __init__(self, app: Pantainos) -> None:
        """
        Initialize documentation UI with Pantainos application.
        """
        if not NICEGUI_AVAILABLE:
            raise RuntimeError("NiceGUI not available. Install with: pip install nicegui")

        self.app = app

    def create_documentation_page(self) -> str:
        """
        Create the main documentation page as styled HTML.
        """
        from .docs import DocumentationGenerator

        # Extract documentation data
        doc_generator = DocumentationGenerator(self.app)
        docs_data = doc_generator.extract_handlers_docs()

        # Build handlers section HTML
        handlers_html = ""
        for handler in docs_data.get("handlers", []):
            handler_name = handler.get("handler_name", "")
            event_type = handler.get("event_type", "")
            docstring = handler.get("docstring", "")
            handlers_html += f"""
                <div class="handler-card">
                    <h4>{handler_name}</h4>
                    <div class="event-type">Event: {event_type}</div>
                    <div class="handler-description">{docstring}</div>
                </div>
            """

        # Build plugins section HTML
        plugins_html = ""
        plugins = self.app.plugin_registry.get_all()
        if plugins:
            for plugin_name, plugin in plugins.items():
                plugins_html += f"""
                    <div class="plugin-card">
                        <h4>Plugin: {plugin_name}</h4>
                """

                # API endpoints
                if hasattr(plugin, "apis") and plugin.apis:
                    plugins_html += "<div class='plugin-apis'><strong>API Endpoints:</strong><ul>"
                    for route in plugin.apis:
                        plugins_html += f"<li><span class='api-badge'>API</span> /api/plugins/{plugin_name}{route}</li>"
                    plugins_html += "</ul></div>"

                # Web pages
                if hasattr(plugin, "pages") and plugin.pages:
                    plugins_html += "<div class='plugin-pages'><strong>Web Pages:</strong><ul>"
                    for route in plugin.pages:
                        page_route = (
                            f"/ui/plugins/{plugin_name}/" if route == "" else f"/ui/plugins/{plugin_name}/{route}"
                        )
                        plugins_html += f"<li><span class='ui-badge'>UI</span> {page_route}</li>"
                    plugins_html += "</ul></div>"

                plugins_html += "</div>"
        else:
            plugins_html = "<div class='no-data'>No plugins registered</div>"

        # Build application metrics
        event_count = (
            len(self.app.event_bus.handlers) if hasattr(self.app, "event_bus") and self.app.event_bus.handlers else 0
        )
        plugin_count = len(self.app.plugin_registry.get_all())
        web_status = "Enabled" if hasattr(self.app, "web_server") else "Disabled"
        db_status = "Connected" if hasattr(self.app, "database") else "Not Connected"

        return f"""
<!DOCTYPE html>
<html>
<head>
    <title>Pantainos API Documentation</title>
    <style>
        body {{
            font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
            font-size: 13px;
            margin: 0;
            padding: 0;
            background-color: #1e1e1e;
            color: #d4d4d4;
            line-height: 1.4;
        }}
        .container {{
            max-width: 1400px;
            margin: 0 auto;
            padding: 10px;
        }}
        h1 {{
            color: #4ec9b0;
            font-size: 20px;
            border-bottom: 1px solid #3e3e3e;
            padding-bottom: 8px;
            margin-bottom: 15px;
            font-weight: normal;
            text-transform: uppercase;
            letter-spacing: 2px;
        }}
        h2 {{
            color: #569cd6;
            font-size: 14px;
            margin-top: 20px;
            margin-bottom: 10px;
            text-transform: uppercase;
            letter-spacing: 1px;
            border-bottom: 1px solid #3e3e3e;
            padding-bottom: 5px;
        }}
        h4 {{
            color: #dcdcaa;
            margin: 0 0 5px 0;
            font-size: 13px;
            font-weight: bold;
        }}
        .section {{
            background: #252526;
            border: 1px solid #3e3e3e;
            padding: 10px;
            margin-bottom: 10px;
        }}
        .handler-card, .plugin-card {{
            border: 1px solid #3e3e3e;
            padding: 8px;
            margin-bottom: 5px;
            background-color: #1e1e1e;
            transition: all 0.1s;
        }}
        .handler-card:hover, .plugin-card:hover {{
            background-color: #2a2a2a;
            border-color: #4ec9b0;
        }}
        .event-type {{
            color: #9cdcfe;
            font-size: 11px;
            margin-bottom: 5px;
        }}
        .handler-description {{
            color: #808080;
            font-size: 11px;
            line-height: 1.3;
        }}
        .api-badge {{
            background-color: #0d7a44;
            color: #4af626;
            padding: 1px 4px;
            font-size: 10px;
            font-weight: bold;
            margin-right: 5px;
            text-transform: uppercase;
        }}
        .ui-badge {{
            background-color: #7a440d;
            color: #f6a64a;
            padding: 1px 4px;
            font-size: 10px;
            font-weight: bold;
            margin-right: 5px;
            text-transform: uppercase;
        }}
        .metrics-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 5px;
            margin-top: 10px;
        }}
        .metric-card {{
            background: #1e1e1e;
            padding: 10px;
            border: 1px solid #3e3e3e;
            text-align: center;
        }}
        .metric-value {{
            font-size: 18px;
            font-weight: bold;
            color: #4ec9b0;
            display: block;
        }}
        .metric-label {{
            color: #808080;
            font-size: 10px;
            text-transform: uppercase;
            letter-spacing: 1px;
            margin-top: 3px;
        }}
        .no-data {{
            color: #606060;
            font-size: 11px;
            padding: 10px;
            text-align: center;
            background: #1e1e1e;
            border: 1px dashed #3e3e3e;
        }}
        ul {{
            margin: 5px 0;
            padding-left: 15px;
            list-style-type: none;
        }}
        li {{
            margin-bottom: 3px;
            font-size: 11px;
        }}
        li:before {{
            content: "▸ ";
            color: #608b4e;
            margin-right: 3px;
        }}
        .plugin-apis, .plugin-pages {{
            margin-top: 5px;
            font-size: 11px;
        }}
        strong {{
            color: #c586c0;
            font-weight: normal;
            text-transform: uppercase;
            font-size: 10px;
            letter-spacing: 1px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>PANTAINOS://API_DOCUMENTATION</h1>

        <div class="section">
            <h2>[EVENT_HANDLERS]</h2>
            {handlers_html if handlers_html else '<div class="no-data">// No event handlers registered</div>'}
        </div>

        <div class="section">
            <h2>[LOADED_PLUGINS]</h2>
            {plugins_html}
        </div>

        <div class="section">
            <h2>[SYSTEM_METRICS]</h2>
            <div class="metrics-grid">
                <div class="metric-card">
                    <span class="metric-value">{event_count}</span>
                    <div class="metric-label">Events</div>
                </div>
                <div class="metric-card">
                    <span class="metric-value">{plugin_count}</span>
                    <div class="metric-label">Plugins</div>
                </div>
                <div class="metric-card">
                    <span class="metric-value">{web_status}</span>
                    <div class="metric-label">Web API</div>
                </div>
                <div class="metric-card">
                    <span class="metric-value">{db_status}</span>
                    <div class="metric-label">Database</div>
                </div>
            </div>
        </div>
    </div>
</body>
</html>
        """
