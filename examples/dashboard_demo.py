#!/usr/bin/env python
"""
Dashboard Demo - Launch the beautiful Pantainos web interface

This example demonstrates the new dashboard with real-time metrics,
navigation system, and unified theme.
"""

import asyncio
import sys
from pathlib import Path

# Add src to path for development
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from pantainos import Pantainos

# Try to import nicegui for the interface
try:
    from nicegui import ui

    NICEGUI_AVAILABLE = True
except ImportError:
    NICEGUI_AVAILABLE = False
    print("NiceGUI not installed. Install with: pip install nicegui psutil")
    sys.exit(1)

from pantainos.web.components.navigation import NavigationSystem
from pantainos.web.components.theme import ThemeManager
from pantainos.web.dashboard import DashboardHub


def create_demo_app() -> Pantainos:
    """Create and configure the demo application"""
    app = Pantainos(database_url="sqlite:///dashboard_demo.db", debug=True, web_dashboard=True, web_port=8080)

    # Register some demo event handlers
    @app.on("user.action")
    async def handle_user_action(event):
        print(f"User action: {event.data}")

    @app.on("system.metric")
    async def handle_metric(event):
        print(f"System metric: {event.data}")

    @app.on("test.event")
    async def handle_test(event):
        print(f"Test event: {event.data}")

    return app


# Create Pantainos application
app = create_demo_app()

# Create dashboard and navigation
dashboard = DashboardHub(app)
navigation = NavigationSystem(app)
theme_manager = ThemeManager()


@ui.page("/")
async def main_page():
    """Main dashboard page"""
    # Apply dark theme
    ui.dark_mode().enable()

    # Add custom CSS for beautiful styling
    ui.add_css(
        """
        body {
            font-family: 'Inter', system-ui, -apple-system, sans-serif;
        }
        .nicegui-content {
            padding: 0;
            background: linear-gradient(135deg, #1e1b4b 0%, #7c3aed 50%, #1e1b4b 100%);
            min-height: 100vh;
        }
    """
    )

    # Create the main layout
    with ui.column().classes("w-full h-screen relative"):
        # Navigation sidebar
        navigation.create_sidebar()

        # Main content area with padding for sidebar
        with ui.element("div").classes("ml-64 h-full"):
            # Top bar
            navigation.create_topbar()

            # Dashboard content with padding for topbar
            with ui.element("div").classes("mt-16 p-6"):
                dashboard.create_dashboard()

    # Start the event bus if not running
    if not app.event_bus.running:
        await app.event_bus.start()

        # Emit some demo events for activity
        demo_events = [
            ("user.action", {"action": "login", "user": "admin"}),
            ("system.metric", {"cpu": 45.2, "memory": 62.8}),
            ("test.event", {"message": "Dashboard initialized"}),
            ("user.action", {"action": "view_dashboard", "user": "admin"}),
            ("system.metric", {"requests_per_sec": 150}),
        ]

        for event_type, data in demo_events:
            await app.event_bus.emit(event_type, data, "dashboard_demo")
            await asyncio.sleep(0.5)


@ui.page("/events")
def events_page():
    """Events page"""
    ui.dark_mode().enable()

    with ui.column().classes("w-full h-screen bg-gray-900"):
        # Navigation
        navigation.create_sidebar()

        with ui.element("div").classes("ml-64 h-full"):
            navigation.create_topbar()

            # Events content
            with ui.element("div").classes("mt-16 p-6"):
                with ui.card().classes("bg-gray-800 text-white"):
                    ui.label("Event Explorer").classes("text-2xl font-bold mb-4")
                    ui.label("View and manage system events").classes("text-gray-400")

                    # Event list placeholder
                    with ui.column().classes("mt-6 gap-2"):
                        for i in range(5):
                            with ui.card().classes("bg-gray-700 p-3"):
                                ui.label(f"Event {i+1}").classes("text-sm font-medium")
                                ui.label("example.event").classes("text-xs text-gray-400")


@ui.page("/plugins")
def plugins_page():
    """Plugins page"""
    ui.dark_mode().enable()

    with ui.column().classes("w-full h-screen bg-gray-900"):
        # Navigation
        navigation.create_sidebar()

        with ui.element("div").classes("ml-64 h-full"):
            navigation.create_topbar()

            # Plugins content
            with ui.element("div").classes("mt-16 p-6"):
                ui.label("Plugin Manager").classes("text-2xl font-bold text-white mb-4")

                # Plugin grid
                with ui.grid(columns=3).classes("gap-6"):
                    for plugin_name in ["Observability", "Database", "WebHooks", "Analytics", "Logging", "Monitoring"]:
                        with ui.card().classes("bg-gradient-to-br from-purple-600 to-pink-600 text-white"):
                            with ui.column().classes("p-4"):
                                ui.icon("extension", size="xl")
                                ui.label(plugin_name).classes("text-lg font-bold mt-2")
                                ui.label("Active").classes("text-sm opacity-80")
                                ui.button("Configure", icon="settings").props("flat").classes("mt-4 w-full")


@ui.page("/settings")
def settings_page():
    """Settings page"""
    ui.dark_mode().enable()

    with ui.column().classes("w-full h-screen bg-gray-900"):
        # Navigation
        navigation.create_sidebar()

        with ui.element("div").classes("ml-64 h-full"):
            navigation.create_topbar()

            # Settings content
            with ui.element("div").classes("mt-16 p-6"):
                ui.label("Settings").classes("text-2xl font-bold text-white mb-6")

                with ui.tabs().classes("w-full text-white") as tabs:
                    ui.tab("General", icon="settings")
                    ui.tab("Appearance", icon="palette")
                    ui.tab("Database", icon="storage")
                    ui.tab("Advanced", icon="tune")

                with ui.tab_panels(tabs, value="General").classes("w-full mt-4"):
                    with ui.tab_panel("General"):
                        with ui.card().classes("bg-gray-800 text-white p-6"):
                            ui.label("General Settings").classes("text-lg font-semibold mb-4")

                            ui.input("Application Name", value="Pantainos Dashboard").classes("w-full mb-4")
                            ui.input("Debug Level", value="INFO").classes("w-full mb-4")
                            ui.switch("Enable Debug Mode").classes("mb-4")
                            ui.switch("Auto-save Configuration").classes("mb-4")

                            ui.button("Save Changes", icon="save").classes("bg-purple-600 hover:bg-purple-700")

                    with ui.tab_panel("Appearance"):
                        with ui.card().classes("bg-gray-800 text-white p-6"):
                            ui.label("Theme Settings").classes("text-lg font-semibold mb-4")

                            with ui.row().classes("gap-4 mb-4"):
                                ui.button("Dark Theme", icon="dark_mode").classes("bg-gray-700")
                                ui.button("Light Theme", icon="light_mode").classes("bg-gray-600")

                            ui.label("Accent Color").classes("mt-4 mb-2")
                            ui.color_input(value="#8B5CF6").classes("mb-4")

                            ui.switch("Enable Animations").classes("mb-2")
                            ui.switch("Show Tooltips").classes("mb-2")
                            ui.switch("Compact Mode")

                    with ui.tab_panel("Database"):
                        with ui.card().classes("bg-gray-800 text-white p-6"):
                            ui.label("Database Configuration").classes("text-lg font-semibold mb-4")

                            ui.input("Database URL", value="sqlite:///dashboard_demo.db").classes("w-full mb-4")
                            ui.input("Connection Pool Size", value="10").classes("w-full mb-4")
                            ui.switch("Enable Query Logging").classes("mb-4")

                            with ui.row().classes("gap-2"):
                                ui.button("Test Connection", icon="sync").classes("bg-green-600")
                                ui.button("Reset Database", icon="refresh").classes("bg-red-600")

                    with ui.tab_panel("Advanced"):
                        with ui.card().classes("bg-gray-800 text-white p-6"):
                            ui.label("Advanced Settings").classes("text-lg font-semibold mb-4")
                            ui.label("⚠️ Modify these settings with caution").classes("text-yellow-400 text-sm mb-4")

                            ui.textarea("Custom CSS", value="").classes("w-full mb-4 font-mono")
                            ui.input("API Rate Limit", value="100").classes("w-full mb-4")
                            ui.switch("Enable Experimental Features").classes("mb-4")


if __name__ in {"__main__", "__mp_main__"}:
    if NICEGUI_AVAILABLE:
        print("🚀 Starting Pantainos Dashboard Demo")
        print("📊 Open http://localhost:8080 in your browser")
        print("")
        print("Available pages:")
        print("  • Dashboard: http://localhost:8080/")
        print("  • Events:    http://localhost:8080/events")
        print("  • Plugins:   http://localhost:8080/plugins")
        print("  • Settings:  http://localhost:8080/settings")
        print("")
        print("Press Ctrl+C to stop the server")

        ui.run(port=8080, title="Pantainos Dashboard", favicon="🎯", dark=True, reload=False, show=False)
    else:
        print("Please install NiceGUI to run this demo: pip install nicegui psutil")
