"""
Modern Dashboard Hub for Pantainos Applications

Provides a beautiful, responsive dashboard with real-time metrics,
activity monitoring, and system health visualization.
"""

from __future__ import annotations

from collections import deque
from datetime import datetime, timedelta
from typing import TYPE_CHECKING, Any

try:
    from nicegui import ui

    NICEGUI_AVAILABLE = True
except ImportError:
    NICEGUI_AVAILABLE = False
    ui = None

try:
    import psutil

    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False
    psutil = None

if TYPE_CHECKING:
    from pantainos.application import Pantainos


class DashboardHub:
    """
    Modern dashboard interface for Pantainos applications.

    Features:
    - Real-time metrics and KPIs
    - Activity feed with live updates
    - System health monitoring
    - Plugin status overview
    - Beautiful, responsive design
    """

    def __init__(self, app: Pantainos) -> None:
        """Initialize dashboard with Pantainos application."""
        if not NICEGUI_AVAILABLE:
            raise RuntimeError("NiceGUI not available. Install with: pip install nicegui")

        self.app = app
        self.event_history: deque[dict[str, Any]] = deque(maxlen=100)
        self.event_rate_history: deque[tuple[datetime, int]] = deque(maxlen=60)
        self.last_event_count = 0
        self.start_time = datetime.now()

        # Track metrics
        self.total_events = 0
        self.events_per_second = 0
        self.active_handlers = 0
        self.plugin_count = 0

        # System metrics
        self.cpu_history: deque[float] = deque(maxlen=30)
        self.memory_history: deque[float] = deque(maxlen=30)
        self.cpu_usage = 0.0
        self.memory_usage = 0.0

    def create_dashboard(self) -> None:
        """Create the main dashboard interface."""
        # Guard against missing NiceGUI context
        if not ui or not getattr(ui.context, "slot_stack", []):
            return

        # Main container with gradient background
        with ui.element("div").classes("min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900"):
            # Top navigation bar
            with (
                ui.element("div").classes("bg-black/20 backdrop-blur-md border-b border-white/10"),
                ui.element("div").classes("max-w-7xl mx-auto px-4 sm:px-6 lg:px-8"),
                ui.row().classes("items-center justify-between h-16"),
            ):
                # Logo and title
                with ui.row().classes("items-center gap-3"):
                    ui.icon("dashboard", size="lg").classes("text-purple-400")
                    ui.label("Pantainos Dashboard").classes("text-xl font-bold text-white tracking-tight")

            # Main content area
            with ui.element("div").classes("max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8"):
                # Metrics and content would be rendered here
                ui.label("Dashboard content").classes("text-white")

        # Start update timers
        ui.timer(1.0, self._update_metrics)
        ui.timer(2.0, self._update_system_health)

    async def _update_metrics(self) -> None:
        """Update dashboard metrics."""
        # Update event metrics
        self.total_events = len(self.event_history)

        # Calculate events per second
        now = datetime.now()
        recent_events = [
            e for e in self.event_history if self._parse_timestamp(e.get("timestamp", "")) > now - timedelta(seconds=1)
        ]
        self.events_per_second = len(recent_events)

        # Update handler count
        self.active_handlers = sum(len(handlers) for handlers in self.app.event_bus.handlers.values())

        # Update plugin count
        self.plugin_count = len(self.app.plugins)

    async def _update_system_health(self) -> None:
        """Update system health metrics."""
        if PSUTIL_AVAILABLE:
            try:
                self.cpu_usage = psutil.cpu_percent(interval=0.1)
                self.memory_usage = psutil.virtual_memory().percent

                self.cpu_history.append(self.cpu_usage)
                self.memory_history.append(self.memory_usage)
            except (AttributeError, TypeError, OSError):
                self.cpu_usage = 0
                self.memory_usage = 0
        else:
            self.cpu_usage = 0
            self.memory_usage = 0

    def _get_uptime(self) -> str:
        """Get formatted uptime."""
        delta = datetime.now() - self.start_time
        hours, remainder = divmod(delta.seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"

    def _format_time(self, timestamp: str) -> str:
        """Format timestamp for display."""
        try:
            dt = datetime.fromisoformat(timestamp)
            return dt.strftime("%H:%M:%S")
        except (ValueError, AttributeError):
            return "just now"

    def _parse_timestamp(self, timestamp: str) -> datetime:
        """Parse ISO timestamp string."""
        try:
            return datetime.fromisoformat(timestamp)
        except (ValueError, AttributeError):
            return datetime.now()

    async def _emit_test_event(self) -> None:
        """Emit a test event."""
        await self.app.event_bus.emit("test.event", {"message": "Test from dashboard"})
        if ui:
            ui.notify("Test event emitted!", type="positive")

    async def _clear_history(self) -> None:
        """Clear event history."""
        self.event_history.clear()
        if ui:
            ui.notify("Event history cleared", type="info")
