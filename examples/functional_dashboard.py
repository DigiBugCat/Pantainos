#!/usr/bin/env python
"""
Functional Dashboard - Actually works, less pretty
"""

import asyncio
import sys
from collections import deque
from datetime import datetime
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from pantainos import Pantainos

try:
    from nicegui import ui
except ImportError:
    print("Install NiceGUI: pip install nicegui")
    sys.exit(1)


class FunctionalDashboard:
    def __init__(self, app: Pantainos):
        self.app = app
        self.events = deque(maxlen=100)
        self.event_container = None
        self.plugin_container = None
        self.stats_container = None
        self.event_count = 0
        self.filter_text = ""

    def setup_event_listener(self):
        """Listen to ALL events"""
        # Override the event bus emit to capture everything
        original_emit = self.app.event_bus.emit

        async def capture_emit(event_type, data=None, source=None):
            # Capture the event
            event_info = {
                "type": event_type,
                "data": data,
                "source": source,
                "timestamp": datetime.now().strftime("%H:%M:%S"),
            }
            self.events.appendleft(event_info)
            self.event_count += 1

            # Update UI if container exists
            if self.event_container:
                self.update_events()
            if self.stats_container:
                self.update_stats()

            # Call original emit
            return await original_emit(event_type, data, source)

        self.app.event_bus.emit = capture_emit

    def update_events(self):
        """Update event display"""
        self.event_container.clear()

        # Filter events
        filtered_events = self.events
        if self.filter_text:
            filtered_events = [e for e in self.events if self.filter_text.lower() in str(e).lower()]

        with self.event_container:
            if not filtered_events:
                ui.label("No events yet...").classes("text-gray-500")
            else:
                for event in list(filtered_events)[:20]:  # Show last 20
                    with ui.card().classes("w-full p-2 mb-1"):
                        with ui.row().classes("w-full items-center"):
                            ui.label(event["timestamp"]).classes("text-xs text-gray-500 mr-2")
                            ui.label(event["type"]).classes("font-mono text-sm font-bold")
                            if event["source"]:
                                ui.label(f"from {event['source']}").classes("text-xs text-gray-400 ml-2")
                        if event["data"]:
                            ui.label(str(event["data"])[:100]).classes("text-xs text-gray-600")

    def update_stats(self):
        """Update statistics"""
        self.stats_container.clear()
        with self.stats_container:
            ui.label(f"Total Events: {self.event_count}").classes("text-lg font-bold")
            ui.label(f"Events in Buffer: {len(self.events)}")
            ui.label(f"Handlers Registered: {len(self.app.handler_registry._handlers)}")
            ui.label(f"Services Registered: {len(self.app.container._services)}")

    def create_dashboard(self):
        """Create the main dashboard"""
        with ui.column().classes("w-full p-4"):
            ui.label("Pantainos Functional Dashboard").classes("text-2xl font-bold mb-4")

            # Control Panel
            with ui.card().classes("w-full p-4 mb-4"):
                ui.label("Control Panel").classes("text-lg font-bold mb-2")

                with ui.row().classes("gap-2 flex-wrap"):
                    # Event emitters
                    ui.button(
                        "Emit Test Event",
                        on_click=lambda: asyncio.create_task(
                            self.app.event_bus.emit("test.event", {"message": "Hello!"}, "dashboard")
                        ),
                    )

                    ui.button(
                        "Emit Error",
                        on_click=lambda: asyncio.create_task(
                            self.app.event_bus.emit("error", {"error": "Test error"}, "dashboard")
                        ),
                    )

                    ui.button(
                        "Emit Metric",
                        on_click=lambda: asyncio.create_task(
                            self.app.event_bus.emit("metric.update", {"cpu": 50, "mem": 75}, "dashboard")
                        ),
                    )

                    # Bulk emit
                    async def emit_bulk():
                        for i in range(10):
                            await self.app.event_bus.emit(f"bulk.event.{i}", {"index": i}, "bulk")
                            await asyncio.sleep(0.1)

                    ui.button("Emit 10 Events", on_click=lambda: asyncio.create_task(emit_bulk()))

                    # Clear events
                    def clear_events():
                        self.events.clear()
                        self.event_count = 0
                        self.update_events()
                        self.update_stats()

                    ui.button("Clear Events", on_click=clear_events).classes("bg-red-500")

            # Main content grid
            with ui.grid(columns=2).classes("w-full gap-4"):
                # Left: Events
                with ui.card().classes("p-4"):
                    ui.label("Event Stream").classes("text-lg font-bold mb-2")

                    # Filter
                    ui.input("Filter events...", on_change=lambda e: self.set_filter(e.value)).classes("w-full mb-2")

                    # Event list
                    self.event_container = ui.column().classes("w-full max-h-96 overflow-y-auto")
                    self.update_events()

                # Right: System Info
                with ui.column().classes("gap-4"):
                    # Stats
                    with ui.card().classes("p-4"):
                        ui.label("Statistics").classes("text-lg font-bold mb-2")
                        self.stats_container = ui.column()
                        self.update_stats()

                    # Plugins
                    with ui.card().classes("p-4"):
                        ui.label("Registered Plugins").classes("text-lg font-bold mb-2")
                        self.plugin_container = ui.column()
                        self.update_plugins()

            # Auto-refresh
            ui.timer(2.0, self.refresh_all)

    def set_filter(self, text):
        """Set event filter"""
        self.filter_text = text
        self.update_events()

    def update_plugins(self):
        """Update plugin list"""
        if self.plugin_container:
            self.plugin_container.clear()
            with self.plugin_container:
                if self.app.plugins:
                    for name, plugin in self.app.plugins.items():
                        with ui.row().classes("items-center"):
                            ui.icon("extension").classes("text-green-500")
                            ui.label(name).classes("font-mono")
                            ui.label(f"v{plugin.version}").classes("text-xs text-gray-500")
                else:
                    ui.label("No plugins registered").classes("text-gray-500")

    def refresh_all(self):
        """Refresh all displays"""
        self.update_events()
        self.update_stats()
        self.update_plugins()


# Create app
app = Pantainos(database_url="sqlite:///functional_dashboard.db", debug=True)


# Register some event handlers to show they work
@app.on("test.event")
async def handle_test(event):
    print(f"Handler received: {event.data}")
    # Emit a response event
    await app.event_bus.emit("test.response", {"handled": True}, "handler")


@app.on("metric.update")
async def handle_metric(event):
    print(f"Metric update: {event.data}")


# Create dashboard
dashboard = FunctionalDashboard(app)


@ui.page("/")
async def main_page():
    """Main dashboard page"""
    # Simple dark theme
    ui.dark_mode().enable()

    # Start event bus if needed
    if not app.event_bus.running:
        await app.event_bus.start()
        dashboard.setup_event_listener()

        # Emit initial event
        await app.event_bus.emit("dashboard.started", {"time": datetime.now().isoformat()}, "system")

    # Create dashboard
    dashboard.create_dashboard()


@ui.page("/raw")
async def raw_page():
    """Raw event data page"""
    ui.dark_mode().enable()

    with ui.column().classes("p-4"):
        ui.label("Raw Event Data").classes("text-xl font-bold mb-4")

        # JSON display
        ui.code(str(list(dashboard.events)[:10]), language="json").classes("w-full")

        ui.button("Back to Dashboard", on_click=lambda: ui.open("/"))


if __name__ in {"__main__", "__mp_main__"}:
    print("🚀 Starting Functional Dashboard")
    print("📊 Open http://localhost:8081")
    print("")
    print("This dashboard actually works:")
    print("  • Click buttons to emit events")
    print("  • Filter events in real-time")
    print("  • See actual handler counts")
    print("  • View raw data at /raw")

    ui.run(port=8081, title="Functional Dashboard", dark=True, reload=False, show=False)
