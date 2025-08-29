#!/usr/bin/env python
"""
Event Explorer Demo - Interactive event monitoring and testing

This example demonstrates the Event Explorer interface for Pantainos,
allowing real-time event monitoring and interactive testing.
"""

import asyncio
import sys
from pathlib import Path

# Add src to path for development
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from pantainos import Pantainos
from pantainos.web.event_explorer import EventExplorer

# Try to import nicegui for the interface
try:
    from nicegui import ui

    NICEGUI_AVAILABLE = True
except ImportError:
    NICEGUI_AVAILABLE = False
    print("NiceGUI not installed. Install with: pip install nicegui")
    sys.exit(1)

# Create Pantainos application
app = Pantainos(database_url="sqlite:///:memory:", debug=True)

# Create Event Explorer
explorer = EventExplorer(app)


# Register some example event handlers
@app.on("user.login")
async def handle_login(event):
    print(f"User logged in: {event.data}")


@app.on("user.logout")
async def handle_logout(event):
    print(f"User logged out: {event.data}")


@app.on("message.sent")
async def handle_message(event):
    print(f"Message sent: {event.data}")


@app.on("system.error")
async def handle_error(event):
    print(f"System error: {event.data}")


# Create NiceGUI pages
@ui.page("/")
async def index():
    # Start event bus if not running
    if not app.event_bus.running:
        await app.event_bus.start()

        # Emit some initial events for demonstration
        await app.event_bus.emit("user.login", {"username": "alice", "timestamp": "2024-01-01T10:00:00"})
        await app.event_bus.emit("message.sent", {"from": "alice", "to": "bob", "message": "Hello!"})
        await app.event_bus.emit("user.login", {"username": "bob", "timestamp": "2024-01-01T10:05:00"})

        # Give events time to process
        await asyncio.sleep(0.1)

    ui.label("Pantainos Event Explorer Demo").classes("text-3xl font-bold mb-4")
    ui.label("Navigate to /events to see the Event Explorer").classes("text-lg")
    ui.button("Open Event Explorer", on_click=lambda: ui.navigate.to("/events")).classes("mt-4")


@ui.page("/events")
def events_page():
    explorer.create_interface()


if __name__ in {"__main__", "__mp_main__"}:
    if NICEGUI_AVAILABLE:
        print("Starting Event Explorer Demo...")
        print("Open http://localhost:8080 in your browser")
        print("Navigate to /events to see the Event Explorer interface")

        ui.run(port=8080, title="Pantainos Event Explorer", reload=False, show=False)
    else:
        print("Please install NiceGUI to run this demo: pip install nicegui")
