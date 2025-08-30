"""
EventBus tests - Core event routing functionality
"""

import asyncio

import pytest

from pantainos.core.di.container import ServiceContainer
from pantainos.core.event_bus import EventBus
from pantainos.events import EventModel, GenericEvent, equals


@pytest.fixture
def container():
    """Create a service container for testing"""
    return ServiceContainer()


@pytest.fixture
async def event_bus(container):
    """Create an event bus for testing"""
    bus = EventBus(container)
    await bus.start()
    yield bus
    await bus.stop()


@pytest.mark.asyncio
async def test_basic_registration(event_bus):
    """Test that handlers can be registered and called"""
    results = []

    async def handler(event):
        results.append(event.data["value"])

    event_bus.register("test.event", handler)

    event = GenericEvent(type="test.event", data={"value": "test"}, source="test")
    await event_bus.emit(event)
    await asyncio.sleep(0.1)  # Allow event processing

    assert len(results) == 1
    assert results[0] == "test"


@pytest.mark.asyncio
async def test_conditions_filter_events(event_bus):
    """Test that conditions filter events correctly"""
    results = []

    async def handler(event):
        results.append(event.data["value"])

    condition = equals("status", "active")
    event_bus.register("test.event", handler, condition)

    # Event that doesn't match condition
    event1 = GenericEvent(type="test.event", data={"value": "filtered", "status": "inactive"}, source="test")
    await event_bus.emit(event1)
    await asyncio.sleep(0.1)

    # Event that matches condition
    event2 = GenericEvent(type="test.event", data={"value": "passed", "status": "active"}, source="test")
    await event_bus.emit(event2)
    await asyncio.sleep(0.1)

    assert len(results) == 1
    assert results[0] == "passed"


@pytest.mark.asyncio
async def test_multiple_handlers(event_bus):
    """Test that multiple handlers can be registered for the same event"""
    results = []

    async def handler1(event):
        results.append("handler1")

    async def handler2(event):
        results.append("handler2")

    event_bus.register("test.event", handler1)
    event_bus.register("test.event", handler2)

    event = GenericEvent(type="test.event", data={"value": "test"}, source="test")
    await event_bus.emit(event)
    await asyncio.sleep(0.1)

    assert len(results) == 2
    assert "handler1" in results
    assert "handler2" in results


@pytest.mark.asyncio
async def test_dependency_injection(event_bus):
    """Test that dependency injection works for handlers"""

    # Register a test service
    class TestService:
        def get_data(self):
            return "injected_data"

    test_service = TestService()
    event_bus.container.register_singleton(TestService, test_service)

    results = []

    async def handler(event, service: TestService):
        results.append(service.get_data())

    event_bus.register("test.event", handler)

    event = GenericEvent(type="test.event", data={"value": "test"}, source="test")
    await event_bus.emit(event)
    await asyncio.sleep(0.1)

    assert len(results) == 1
    assert results[0] == "injected_data"


@pytest.mark.asyncio
async def test_no_handlers_no_errors(event_bus):
    """Test that events with no handlers don't cause errors"""
    event = GenericEvent(type="nonexistent.event", data={"value": "test"}, source="test")
    await event_bus.emit(event)
    await asyncio.sleep(0.1)

    # Should complete without errors


@pytest.mark.asyncio
async def test_add_event_hook(event_bus):
    """Test that we can add event hooks to track all events"""
    events_captured = []

    async def event_hook(event: EventModel) -> None:
        events_captured.append(event)

    # This should work - adding an event hook
    event_bus.add_event_hook(event_hook)

    # Emit an event
    event = GenericEvent(type="test.event", data={"data": "test"}, source="test")
    await event_bus.emit(event)
    await asyncio.sleep(0.1)  # Let event processing complete

    # Hook should have captured the event
    assert len(events_captured) == 1
    assert events_captured[0].type == "test.event"
    assert events_captured[0].data == {"data": "test"}


@pytest.mark.asyncio
async def test_remove_event_hook(event_bus):
    """Test that we can remove event hooks"""
    events_captured = []

    async def event_hook(event: EventModel) -> None:
        events_captured.append(event)

    # Add and then remove hook
    event_bus.add_event_hook(event_hook)
    event_bus.remove_event_hook(event_hook)

    # Emit an event
    event = GenericEvent(type="test.event", data={"data": "test"}, source="test")
    await event_bus.emit(event)
    await asyncio.sleep(0.1)

    # Hook should not have captured anything
    assert len(events_captured) == 0


@pytest.mark.asyncio
async def test_multiple_event_hooks(event_bus):
    """Test that multiple hooks can be registered"""
    events_captured_1 = []
    events_captured_2 = []

    async def hook1(event: EventModel) -> None:
        events_captured_1.append(event)

    async def hook2(event: EventModel) -> None:
        events_captured_2.append(event)

    event_bus.add_event_hook(hook1)
    event_bus.add_event_hook(hook2)

    event = GenericEvent(type="test.event", data={"data": "test"}, source="test")
    await event_bus.emit(event)
    await asyncio.sleep(0.1)

    # Both hooks should have captured the event
    assert len(events_captured_1) == 1
    assert len(events_captured_2) == 1
