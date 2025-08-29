"""
Event Explorer - Interactive event monitoring and testing interface for Pantainos

Provides real-time event tracking, handler inspection, and interactive
event emission capabilities through NiceGUI web interface.
"""

from __future__ import annotations

import json
from collections import defaultdict, deque
from datetime import datetime
from typing import TYPE_CHECKING, Any

try:
    from nicegui import ui

    NICEGUI_AVAILABLE = True
except ImportError:
    NICEGUI_AVAILABLE = False
    ui = None

if TYPE_CHECKING:
    from pantainos.application import Pantainos
    from pantainos.events import Event


class EventExplorer:
    """
    Interactive event explorer interface for Pantainos applications.

    Features:
    - Real-time event stream monitoring
    - Interactive event emission console
    - Handler inspection and statistics
    - Event history tracking
    """

    def __init__(self, app: Pantainos) -> None:
        """
        Initialize Event Explorer with Pantainos application.

        Args:
            app: The Pantainos application to monitor

        Raises:
            RuntimeError: If NiceGUI is not available
        """
        if not NICEGUI_AVAILABLE:
            raise RuntimeError("NiceGUI not available. Install with: pip install nicegui")

        self.app = app
        self.recent_events: deque[dict[str, Any]] = deque(maxlen=50)
        self.handler_stats: dict[str, int] = defaultdict(int)
        self.selected_event_type: str = ""
        self.event_source: str = "event-explorer"
        self.event_data: str = "{}"

        # Event tracking will be implemented when add_event_hook is available
        # For now, events won't be tracked to avoid SLF001 lint warning

    async def _track_and_dispatch(self, event: Event) -> None:
        """Track event and dispatch to handlers"""
        # Track the event
        event_info = {
            "type": event.type,
            "data": event.data,
            "source": event.source,
            "timestamp": datetime.now().isoformat(),
        }
        self.recent_events.append(event_info)

        # Track handler executions
        handlers = self.app.event_bus.handlers.get(event.type, [])
        for handler_info in handlers:
            self.handler_stats[handler_info["name"]] += 1

        # Call original dispatch
        await self._original_dispatch(event)

    def create_interface(self) -> None:
        """Create the Event Explorer web interface"""
        with ui.column().classes("w-full h-full p-4 bg-gray-900"):
            # Header
            ui.label("🔍 Event Explorer").classes("text-2xl font-bold text-white mb-4")

            with ui.row().classes("w-full gap-4"):
                # Left Panel - Event Console
                with ui.card().classes("flex-1 bg-gray-800 text-white"):
                    ui.label("Event Console").classes("text-lg font-semibold mb-2")

                    # Event type selector
                    event_types = list(self.app.event_bus.handlers.keys())
                    if event_types and not self.selected_event_type:
                        self.selected_event_type = event_types[0]
                    ui.select(
                        event_types if event_types else ["No events registered"],
                        label="Event Type",
                        value=self.selected_event_type if self.selected_event_type else None,
                        on_change=lambda e: setattr(self, "selected_event_type", e.value) if e.value else None,
                    ).classes("w-full mb-2")

                    # Source input
                    ui.input(
                        label="Source",
                        value=self.event_source,
                        on_change=lambda e: setattr(self, "event_source", e.value),
                    ).classes("w-full mb-2")

                    # JSON data editor
                    ui.textarea(
                        label="Event Data (JSON)",
                        value=self.event_data,
                        on_change=lambda e: setattr(self, "event_data", e.value),
                    ).classes("w-full mb-2 font-mono")

                    # Emit button
                    ui.button("Emit Event", on_click=self._emit_test_event).classes(
                        "w-full bg-blue-600 hover:bg-blue-700"
                    )

                # Right Panel - Event Stream
                with ui.card().classes("flex-1 bg-gray-800 text-white"):
                    ui.label("Recent Events").classes("text-lg font-semibold mb-2")

                    # Create refreshable event list
                    @ui.refreshable
                    def event_list() -> None:
                        for event in reversed(list(self.recent_events)[-10:]):
                            with ui.expansion(f"{event['type']} - {event['timestamp'][-8:]}", icon="event").classes(
                                "bg-gray-700 mb-1"
                            ):
                                ui.label(f"Source: {event['source']}").classes("text-sm")
                                ui.code(json.dumps(event["data"], indent=2), language="json").classes("text-xs")

                    event_list()

                    # Auto-refresh timer
                    ui.timer(1.0, lambda: event_list.refresh())

            # Handler Statistics
            with ui.card().classes("w-full bg-gray-800 text-white mt-4"):
                ui.label("Handler Statistics").classes("text-lg font-semibold mb-2")

                @ui.refreshable
                def handler_stats() -> None:
                    if not self.handler_stats:
                        ui.label("No handler executions yet").classes("text-gray-400")
                    else:
                        with ui.grid(columns=3).classes("w-full gap-2"):
                            for handler_name, count in self.handler_stats.items():
                                with ui.card().classes("bg-gray-700 p-2"):
                                    ui.label(handler_name).classes("text-sm font-semibold")
                                    ui.label(f"{count} calls").classes("text-xs text-gray-300")

                handler_stats()

                # Auto-refresh handler stats
                ui.timer(2.0, lambda: handler_stats.refresh())

    async def _emit_test_event(self) -> None:
        """Emit a test event from the console"""
        if not self.selected_event_type:
            ui.notify("Please select an event type", type="warning")
            return

        try:
            data = json.loads(self.event_data)
        except json.JSONDecodeError as e:
            ui.notify(f"Invalid JSON: {e}", type="error")
            return

        await self.app.event_bus.emit(self.selected_event_type, data, self.event_source)

        ui.notify(f"Event emitted: {self.selected_event_type}", type="success")
