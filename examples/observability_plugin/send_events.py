#!/usr/bin/env python
"""
Event submission script for testing the Observability Plugin

Demonstrates how to submit events to the observability plugin via POST requests.
This script sends various types of events to test the plugin's functionality.

Usage:
    # Start the main app first:
    uv run python examples/observability_plugin/main.py

    # Then in another terminal:
    uv run python examples/observability_plugin/send_events.py
"""

import asyncio
import json
from datetime import datetime
from typing import Any

import aiohttp


class EventSubmitter:
    """Helper class for submitting events to the observability plugin"""

    def __init__(self, base_url: str = "http://localhost:8080") -> None:
        self.base_url = base_url
        self.api_base = f"{base_url}/api/observability"

    async def send_event(self, event_type: str, data: dict[str, Any]) -> dict[str, Any]:
        """Send a single event via POST request"""
        payload = {"event_type": event_type, "data": data, "timestamp": datetime.now().isoformat()}

        async with aiohttp.ClientSession() as session:
            try:
                async with session.post(
                    f"{self.api_base}/events", json=payload, headers={"Content-Type": "application/json"}
                ) as response:
                    result = await response.json()
                    print(f"✅ Sent {event_type}: {data} -> {result}")
                    return result
            except Exception as e:
                print(f"❌ Failed to send {event_type}: {e}")
                return {"error": str(e)}

    async def get_metrics(self) -> dict[str, Any]:
        """Get current metrics from the plugin"""
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(f"{self.api_base}/metrics") as response:
                    result = await response.json()
                    print(f"📊 Current metrics: {json.dumps(result, indent=2)}")
                    return result
            except Exception as e:
                print(f"❌ Failed to get metrics: {e}")
                return {"error": str(e)}

    async def reset_metrics(self) -> dict[str, Any]:
        """Reset all metrics"""
        async with aiohttp.ClientSession() as session:
            try:
                async with session.post(f"{self.api_base}/metrics/reset") as response:
                    result = await response.json()
                    print(f"🔄 Reset metrics: {result}")
                    return result
            except Exception as e:
                print(f"❌ Failed to reset metrics: {e}")
                return {"error": str(e)}


async def main() -> None:
    """Main function that sends various test events"""
    print("📡 Event Submission Example")
    print("=" * 40)

    submitter = EventSubmitter()

    try:
        # Test events to demonstrate different scenarios
        test_events = [
            # HTTP requests
            ("http.request", {"path": "/api/users", "method": "GET", "status": 200}),
            ("http.request", {"path": "/api/users", "method": "POST", "status": 201}),
            ("http.request", {"path": "/api/orders", "method": "GET", "status": 200}),
            ("http.request", {"path": "/api/invalid", "method": "GET", "status": 404}),
            # Errors
            ("error", {"message": "Database timeout", "component": "database", "severity": "high"}),
            ("error", {"message": "Invalid API key", "component": "authentication", "severity": "medium"}),
            ("error", {"message": "Rate limit exceeded", "component": "rate_limiter", "severity": "low"}),
            # Custom metrics
            ("metric.update", {"name": "cpu_usage", "value": 75.2, "unit": "%"}),
            ("metric.update", {"name": "memory_usage", "value": 1024, "unit": "MB"}),
            ("metric.update", {"name": "active_users", "value": 42, "unit": "count"}),
            # Application events
            ("user.login", {"user_id": "user123", "ip": "192.168.1.100"}),
            ("user.logout", {"user_id": "user123", "session_duration": 3600}),
            ("order.created", {"order_id": "ord456", "amount": 99.99, "customer": "customer789"}),
        ]

        print(f"🚀 Sending {len(test_events)} test events...")
        print()

        # Send events with delays
        for i, (event_type, data) in enumerate(test_events, 1):
            print(f"📤 {i}/{len(test_events)} - Sending {event_type}")
            await submitter.send_event(event_type, data)
            await asyncio.sleep(0.3)  # Small delay between events

        print("\n📊 Getting current metrics...")
        await submitter.get_metrics()

        print("\n💡 Demo complete! Visit the web dashboard to see the results:")
        print("   • Main Dashboard: http://localhost:8080")
        print("   • Plugin Dashboard: http://localhost:8080/ui/plugins/observability")
        print("   • Plugin Config: http://localhost:8080/ui/plugins/observability/config")

        # Optional: Ask if user wants to reset metrics
        print("\n❓ Reset metrics? (y/N): ", end="")
        # For demo purposes, we'll skip interactive input
        # In a real script, you could add: response = input().strip().lower()
        print("Skipping reset for demo")

    except Exception as e:
        print(f"❌ Error during event submission: {e}")
        print("💡 Make sure the observability plugin is running:")
        print("   uv run python examples/observability_plugin/main.py")


if __name__ == "__main__":
    asyncio.run(main())
