"""
Observability Plugin - Complete example with web interface

Demonstrates:
- Plugin with web dashboard pages
- REST API endpoints for receiving events
- Real-time metrics tracking
- Event submission via POST requests
"""

from datetime import datetime
from typing import Any

from pantainos.plugin.base import Plugin


class ObservabilityPlugin(Plugin):
    """
    Complete observability plugin with web interface.

    Features:
    - Tracks events, HTTP requests, and errors
    - Provides web dashboard at /ui/plugins/observability
    - REST API at /api/observability/* for event submission
    - Real-time metrics display
    """

    def __init__(self, **config: Any) -> None:
        super().__init__(**config)

        # Initialize metrics storage
        self.metrics: dict[str, Any] = {
            "events_received": 0,
            "http_requests": 0,
            "errors": 0,
            "last_event_time": None,
            "event_history": [],
            "status": "active",
        }

    @property
    def name(self) -> str:
        return "observability"

    async def start(self) -> None:
        """Initialize the observability plugin"""
        self.metrics["status"] = "active"
        self.metrics["start_time"] = datetime.now().isoformat()
        print("🔍 Observability Plugin started")

    async def stop(self) -> None:
        """Cleanup the observability plugin"""
        self.metrics["status"] = "stopped"
        print("🔍 Observability Plugin stopped")

    # Web Dashboard Pages

    @property
    def page(self):
        """Page decorator for web interface"""

        def decorator(route: str = ""):
            def wrapper(func):
                if not hasattr(self, "pages"):
                    self.pages = {}
                self.pages[route] = {"handler": func, "type": "page"}
                return func

            return wrapper

        return decorator

    @property
    def api(self):
        """API decorator for REST endpoints"""

        def decorator(route: str):
            def wrapper(func):
                if not hasattr(self, "apis"):
                    self.apis = {}
                self.apis[route] = {"handler": func, "type": "api"}
                return func

            return wrapper

        return decorator


# Create the plugin instance and register pages/APIs
observability_plugin = ObservabilityPlugin()


@observability_plugin.page("")
async def dashboard():
    """Main observability dashboard"""
    return f"""
    <div class="container">
        <h1>🔍 Observability Dashboard</h1>
        <div class="metrics-grid">
            <div class="metric-card">
                <h3>Events Received</h3>
                <span class="metric-value">{observability_plugin.metrics['events_received']}</span>
            </div>
            <div class="metric-card">
                <h3>HTTP Requests</h3>
                <span class="metric-value">{observability_plugin.metrics['http_requests']}</span>
            </div>
            <div class="metric-card">
                <h3>Errors</h3>
                <span class="metric-value">{observability_plugin.metrics['errors']}</span>
            </div>
            <div class="metric-card">
                <h3>Status</h3>
                <span class="metric-status">{observability_plugin.metrics['status']}</span>
            </div>
        </div>

        <div class="recent-events">
            <h2>Recent Events</h2>
            <ul>
                {"".join([f"<li>{event}</li>" for event in observability_plugin.metrics['event_history'][-10:]])}
            </ul>
        </div>
    </div>

    <style>
        .container {{ padding: 20px; }}
        .metrics-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; margin: 20px 0; }}
        .metric-card {{ background: #f5f5f5; padding: 15px; border-radius: 8px; text-align: center; }}
        .metric-value {{ font-size: 2em; font-weight: bold; color: #2196F3; }}
        .metric-status {{ font-size: 1.2em; color: #4CAF50; }}
        .recent-events {{ margin-top: 30px; }}
        ul {{ max-height: 300px; overflow-y: auto; }}
    </style>
    """


@observability_plugin.page("config")
async def config_page():
    """Configuration page"""
    return f"""
    <div class="container">
        <h1>⚙️ Observability Configuration</h1>

        <div class="config-section">
            <h2>Current Settings</h2>
            <ul>
                <li><strong>Plugin Status:</strong> {observability_plugin.metrics['status']}</li>
                <li><strong>Start Time:</strong> {observability_plugin.metrics.get('start_time', 'N/A')}</li>
                <li><strong>Event History Size:</strong> {len(observability_plugin.metrics['event_history'])}</li>
            </ul>
        </div>

        <div class="config-section">
            <h2>API Endpoints</h2>
            <ul>
                <li><code>POST /api/observability/events</code> - Submit events</li>
                <li><code>GET /api/observability/metrics</code> - Get current metrics</li>
                <li><code>POST /api/observability/metrics/reset</code> - Reset metrics</li>
            </ul>
        </div>

        <div class="config-section">
            <h2>Event Submission Example</h2>
            <pre><code>curl -X POST http://localhost:8080/api/observability/events \\
  -H "Content-Type: application/json" \\
  -d '{{"event_type": "http.request", "data": {{"path": "/api/test", "status": 200}}}}'</code></pre>
        </div>
    </div>

    <style>
        .container {{ padding: 20px; }}
        .config-section {{ margin: 30px 0; padding: 20px; background: #f9f9f9; border-radius: 8px; }}
        code {{ background: #e1e1e1; padding: 2px 4px; border-radius: 3px; }}
        pre {{ background: #2d2d2d; color: #f8f8f8; padding: 15px; border-radius: 5px; overflow-x: auto; }}
    </style>
    """


# REST API Endpoints


@observability_plugin.api("/events")
async def receive_events():
    """
    Receive events via POST request

    Expected JSON payload:
    {
        "event_type": "http.request",
        "data": {"path": "/api/test", "status": 200}
    }
    """
    # This would normally be handled by FastAPI with request parsing
    # For demonstration, we'll track that an event was received
    observability_plugin.metrics["events_received"] += 1
    observability_plugin.metrics["last_event_time"] = datetime.now().isoformat()

    event_info = f"Event received at {observability_plugin.metrics['last_event_time']}"
    observability_plugin.metrics["event_history"].append(event_info)

    # Keep only last 50 events
    if len(observability_plugin.metrics["event_history"]) > 50:
        observability_plugin.metrics["event_history"] = observability_plugin.metrics["event_history"][-50:]

    # Emit internal event for tracking
    if hasattr(observability_plugin, "app") and observability_plugin.app:
        await observability_plugin.emit(
            "observability.event_received",
            {
                "timestamp": observability_plugin.metrics["last_event_time"],
                "count": observability_plugin.metrics["events_received"],
            },
        )

    return {"status": "success", "event_count": observability_plugin.metrics["events_received"]}


@observability_plugin.api("/metrics")
async def get_metrics():
    """Get current metrics"""
    return observability_plugin.metrics


@observability_plugin.api("/metrics/reset")
async def reset_metrics():
    """Reset all metrics to zero"""
    observability_plugin.metrics.update(
        {
            "events_received": 0,
            "http_requests": 0,
            "errors": 0,
            "last_event_time": None,
            "event_history": [],
            "reset_time": datetime.now().isoformat(),
        }
    )

    if hasattr(observability_plugin, "app") and observability_plugin.app:
        await observability_plugin.emit(
            "observability.metrics_reset", {"timestamp": observability_plugin.metrics["reset_time"]}
        )

    return {"status": "metrics reset", "timestamp": observability_plugin.metrics["reset_time"]}


# Make the plugin instance available for import
__all__ = ["ObservabilityPlugin", "observability_plugin"]
