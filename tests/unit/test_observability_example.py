"""
Tests for observability example
"""

import asyncio

import pytest

from pantainos import Pantainos


@pytest.mark.asyncio
async def test_observability_app_can_be_created():
    """Test that observability app can be instantiated"""
    from examples.observability.main import create_observability_app

    app = create_observability_app()
    assert app is not None
    assert isinstance(app, Pantainos)
    assert hasattr(app, "metrics")


@pytest.mark.asyncio
async def test_observability_example_integration():
    """Test observability example integration"""
    from examples.observability.main import create_observability_app

    app = create_observability_app()

    # Should be able to start and stop without errors
    await app.start()

    # Emit test events
    await app.emit("http.request", {"path": "/metrics", "status": 200})
    await app.emit("error", {"message": "Test error", "component": "database"})
    await app.emit("metric.update", {"name": "cpu_usage", "value": 75.2})

    # Give time for event processing
    await asyncio.sleep(0.1)

    await app.stop()

    # Test passed if no exceptions were raised
