"""
Tests for minimal hello world example
"""

import asyncio

import pytest

from pantainos import Pantainos


@pytest.mark.asyncio
async def test_hello_world_app_can_be_created():
    """Test that hello world app can be instantiated"""
    from examples.minimal.hello_world import create_hello_world_app

    app = create_hello_world_app()
    assert app is not None
    assert isinstance(app, Pantainos)


@pytest.mark.asyncio
async def test_hello_world_example_integration():
    """Test hello world example integration"""
    from examples.minimal.hello_world import create_hello_world_app

    app = create_hello_world_app()

    # Should be able to start and stop without errors
    await app.start()

    # Emit test events
    await app.emit("hello", {"name": "Test"})
    await app.emit("timer.tick", {})

    # Give time for event processing
    await asyncio.sleep(0.1)

    await app.stop()

    # Test passed if no exceptions were raised
