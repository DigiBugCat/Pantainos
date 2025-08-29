#!/usr/bin/env python
"""
Simple observability example using Pantainos with metrics tracking
"""

from pantainos import Event, Pantainos


def create_observability_app() -> Pantainos:
    """Create and configure the observability application"""

    # Create the main app
    app = Pantainos(database_url="sqlite:///observability.db", debug=True)

    # Store metrics in app for demonstration
    app.metrics = {"events_received": 0, "http_requests": 0, "errors": 0}

    @app.on("http.request")
    async def track_http_requests(event: Event) -> None:
        """Track HTTP requests"""
        path = event.data.get("path", "unknown")
        status = event.data.get("status", 0)
        print(f"HTTP Request: {path} -> {status}")

    @app.on("error")
    async def track_errors(event: Event) -> None:
        """Track errors"""
        message = event.data.get("message", "Unknown error")
        component = event.data.get("component", "unknown")
        print(f"Error: {message} in {component}")

    @app.on("metric.update")
    async def handle_metric_update(event: Event) -> None:
        """Handle metric updates"""
        name = event.data.get("name")
        value = event.data.get("value")
        print(f"Metric Update: {name} = {value}")

    return app


if __name__ == "__main__":
    import asyncio

    async def main() -> None:
        print("🔍 Starting Pantainos Observability Example")

        app = create_observability_app()
        await app.start()

        # Emit test events
        test_events = [
            ("http.request", {"path": "/metrics", "status": 200}),
            ("error", {"message": "Test error", "component": "database"}),
            ("metric.update", {"name": "cpu_usage", "value": 75.2}),
        ]

        for event_type, data in test_events:
            await app.event_bus.emit(event_type, data, "observability_example")
            await asyncio.sleep(0.1)

        await asyncio.sleep(1)
        await app.stop()
        print("✅ Example completed")

    asyncio.run(main())
