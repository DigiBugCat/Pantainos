"""
Test event bus hooks functionality
"""

import asyncio

import pytest

from pantainos.core.di.container import ServiceContainer
from pantainos.core.event_bus import EventBus
from pantainos.events import Event


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
async def test_add_event_hook(event_bus):
    """Test that we can add event hooks to track all events"""
    events_captured = []

    async def event_hook(event: Event) -> None:
        events_captured.append(event)

    # This should work - adding an event hook
    event_bus.add_event_hook(event_hook)

    # Emit an event
    await event_bus.emit("test.event", {"data": "test"})
    await asyncio.sleep(0.1)  # Let event processing complete

    # Hook should have captured the event
    assert len(events_captured) == 1
    assert events_captured[0].type == "test.event"
    assert events_captured[0].data == {"data": "test"}


@pytest.mark.asyncio
async def test_remove_event_hook(event_bus):
    """Test that we can remove event hooks"""
    events_captured = []

    async def event_hook(event: Event) -> None:
        events_captured.append(event)

    # Add and then remove hook
    event_bus.add_event_hook(event_hook)
    event_bus.remove_event_hook(event_hook)

    # Emit an event
    await event_bus.emit("test.event", {"data": "test"})
    await asyncio.sleep(0.1)

    # Hook should not have captured anything
    assert len(events_captured) == 0


@pytest.mark.asyncio
async def test_multiple_event_hooks(event_bus):
    """Test that multiple hooks can be registered"""
    events_captured_1 = []
    events_captured_2 = []

    async def hook1(event: Event) -> None:
        events_captured_1.append(event)

    async def hook2(event: Event) -> None:
        events_captured_2.append(event)

    event_bus.add_event_hook(hook1)
    event_bus.add_event_hook(hook2)

    await event_bus.emit("test.event", {"data": "test"})
    await asyncio.sleep(0.1)

    # Both hooks should have captured the event
    assert len(events_captured_1) == 1
    assert len(events_captured_2) == 1
