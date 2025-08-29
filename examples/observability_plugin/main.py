#!/usr/bin/env python
"""
Complete Observability Plugin Example with Web Interface

Demonstrates:
- Plugin with web dashboard pages
- REST API endpoints for receiving events
- Real-time metrics tracking via web interface
- Event submission via POST requests

Run this example:
    uv run python examples/observability_plugin/main.py

Then visit:
- http://localhost:8080 - Main web dashboard
- http://localhost:8080/ui/plugins/observability - Plugin dashboard
- http://localhost:8080/ui/plugins/observability/config - Plugin configuration

Submit events via:
    curl -X POST http://localhost:8080/api/observability/events \
      -H "Content-Type: application/json" \
      -d '{"event_type": "http.request", "data": {"path": "/api/test", "status": 200}}'
"""

import asyncio
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))


from plugin import observability_plugin

from pantainos.application import Pantainos


def create_app() -> Pantainos:
    """Create and configure the observability application with web interface"""

    # Create app with web dashboard enabled
    app = Pantainos(database_url="sqlite:///observability.db", debug=True, web_dashboard=True, web_port=8080)

    # Mount the observability plugin (using the decorated instance)
    app.mount(observability_plugin)

    # Add event handlers that work with the plugin
    @app.on("http.request")
    async def track_http_requests(event) -> None:
        """Track HTTP requests"""
        path = event.data.get("path", "unknown")
        status = event.data.get("status", 0)
        print(f"📊 HTTP Request: {path} -> {status}")

        # Update plugin metrics
        observability_plugin.metrics["http_requests"] += 1
        observability_plugin.metrics["event_history"].append(f"HTTP {status}: {path} at {event.timestamp}")

    @app.on("error")
    async def track_errors(event) -> None:
        """Track errors"""
        message = event.data.get("message", "Unknown error")
        component = event.data.get("component", "unknown")
        print(f"❌ Error: {message} in {component}")

        # Update plugin metrics
        observability_plugin.metrics["errors"] += 1
        observability_plugin.metrics["event_history"].append(f"ERROR: {message} in {component} at {event.timestamp}")

    @app.on("observability.event_received")
    async def handle_observability_events(event) -> None:
        """Handle events from the observability plugin itself"""
        count = event.data.get("count", 0)
        print(f"🔍 Observability: Total events received: {count}")

    @app.on("observability.metrics_reset")
    async def handle_metrics_reset(event) -> None:
        """Handle metrics reset events"""
        timestamp = event.data.get("timestamp")
        print(f"🔄 Metrics reset at {timestamp}")

    return app


async def main() -> None:
    """Main application entry point"""
    print("🚀 Starting Pantainos Observability Plugin Example")
    print("=" * 60)

    app = create_app()

    try:
        await app.start()

        print("\n✅ Application started successfully!")
        print("\n🌐 Web Interface Available:")
        print("   • Main Dashboard: http://localhost:8080")
        print("   • Plugin Dashboard: http://localhost:8080/ui/plugins/observability")
        print("   • Plugin Config: http://localhost:8080/ui/plugins/observability/config")

        print("\n📡 API Endpoints:")
        print("   • POST /api/observability/events - Submit events")
        print("   • GET /api/observability/metrics - Get metrics")
        print("   • POST /api/observability/metrics/reset - Reset metrics")

        print("\n💡 Try submitting events:")
        print("   curl -X POST http://localhost:8080/api/observability/events \\")
        print("     -H 'Content-Type: application/json' \\")
        print('     -d \'{"event_type": "http.request", "data": {"path": "/test", "status": 200}}\'')

        # Emit some test events to demonstrate functionality
        print("\n📊 Emitting test events...")

        test_events = [
            ("http.request", {"path": "/api/users", "status": 200}),
            ("http.request", {"path": "/api/orders", "status": 201}),
            ("error", {"message": "Database connection failed", "component": "database"}),
            ("http.request", {"path": "/api/metrics", "status": 200}),
            ("error", {"message": "Invalid API key", "component": "authentication"}),
        ]

        for i, (event_type, data) in enumerate(test_events, 1):
            print(f"   {i}. Emitting {event_type}: {data}")
            await app.emit(event_type, data, "example")
            await asyncio.sleep(0.5)

        print(f"\n🎯 {len(test_events)} test events emitted!")
        print("\n💻 Visit the web dashboard to see the results!")
        print("   Press Ctrl+C to stop the application...")

        # Keep the application running
        await asyncio.Event().wait()

    except KeyboardInterrupt:
        print("\n🛑 Shutting down...")
    except Exception as e:
        print(f"\n❌ Error: {e}")
    finally:
        await app.stop()
        print("✅ Application stopped")


if __name__ == "__main__":
    asyncio.run(main())
