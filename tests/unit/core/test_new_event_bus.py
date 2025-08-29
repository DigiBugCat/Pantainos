"""
Tests for the new EventBus architecture
"""

import asyncio

import pytest

from pantainos.conditions import equals
from pantainos.core.di.container import ServiceContainer
from pantainos.core.event_bus import EventBus


@pytest.mark.asyncio
async def test_eventbus_basic_registration():
    """Test that handlers can be registered and called"""
    container = ServiceContainer()
    event_bus = EventBus(container)

    results = []

    async def handler(event):
        results.append(event.data["value"])

    event_bus.register("test.event", handler)

    await event_bus.start()
    await event_bus.emit("test.event", {"value": "test"})
    await asyncio.sleep(0.1)  # Allow event processing
    await event_bus.stop()

    assert len(results) == 1
    assert results[0] == "test"


@pytest.mark.asyncio
async def test_eventbus_with_condition():
    """Test that conditions filter events correctly"""
    container = ServiceContainer()
    event_bus = EventBus(container)

    results = []

    async def handler(event):
        results.append(event.data["value"])

    condition = equals("status", "active")
    event_bus.register("test.event", handler, condition)

    await event_bus.start()

    # Event that doesn't match condition
    await event_bus.emit("test.event", {"value": "filtered", "status": "inactive"})
    await asyncio.sleep(0.1)

    # Event that matches condition
    await event_bus.emit("test.event", {"value": "passed", "status": "active"})
    await asyncio.sleep(0.1)

    await event_bus.stop()

    assert len(results) == 1
    assert results[0] == "passed"


@pytest.mark.asyncio
async def test_eventbus_multiple_handlers():
    """Test that multiple handlers can be registered for the same event"""
    container = ServiceContainer()
    event_bus = EventBus(container)

    results = []

    async def handler1(event):
        results.append("handler1")

    async def handler2(event):
        results.append("handler2")

    event_bus.register("test.event", handler1)
    event_bus.register("test.event", handler2)

    await event_bus.start()
    await event_bus.emit("test.event", {"value": "test"})
    await asyncio.sleep(0.1)
    await event_bus.stop()

    assert len(results) == 2
    assert "handler1" in results
    assert "handler2" in results


@pytest.mark.asyncio
async def test_eventbus_dependency_injection():
    """Test that dependency injection works for handlers"""
    container = ServiceContainer()

    # Register a test service
    class TestService:
        def get_data(self):
            return "injected_data"

    test_service = TestService()
    container.register_singleton(TestService, test_service)

    event_bus = EventBus(container)
    results = []

    async def handler(event, service: TestService):
        results.append(service.get_data())

    event_bus.register("test.event", handler)

    await event_bus.start()
    await event_bus.emit("test.event", {"value": "test"})
    await asyncio.sleep(0.1)
    await event_bus.stop()

    assert len(results) == 1
    assert results[0] == "injected_data"


@pytest.mark.asyncio
async def test_eventbus_no_handlers():
    """Test that events with no handlers don't cause errors"""
    container = ServiceContainer()
    event_bus = EventBus(container)

    await event_bus.start()
    await event_bus.emit("nonexistent.event", {"value": "test"})
    await asyncio.sleep(0.1)
    await event_bus.stop()

    # Should complete without errors
