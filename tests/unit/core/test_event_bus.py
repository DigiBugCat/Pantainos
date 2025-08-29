"""
Tests for EventBus - the core event routing system
"""

import asyncio

import pytest

from pantainos.runtime.types import Event


@pytest.mark.asyncio
async def test_basic_event_flow(event_bus):
    """Event emitted should trigger registered handler"""
    received = []

    async def handler(event, ctx):
        received.append(event.data)

    event_bus.register_handler("test.event", handler)

    await event_bus.emit("test.event", {"value": 42})

    # Wait for handlers to complete
    await asyncio.sleep(0.01)

    assert len(received) == 1
    assert received[0]["value"] == 42


@pytest.mark.asyncio
async def test_multiple_handlers(event_bus):
    """Multiple handlers should all receive the same event"""
    results = []

    async def handler1(event, ctx):
        results.append("handler1")

    async def handler2(event, ctx):
        results.append("handler2")

    event_bus.register_handler("test.event", handler1)
    event_bus.register_handler("test.event", handler2)

    await event_bus.emit("test.event", {})
    await asyncio.sleep(0.01)

    assert "handler1" in results
    assert "handler2" in results


@pytest.mark.asyncio
async def test_filter_function(event_bus):
    """Handler should only execute if filter passes"""
    # Bus is provided by fixture
    received = []

    async def handler(event, ctx):
        received.append(event.data["value"])

    def filter_even(event):
        return event.data["value"] % 2 == 0

    event_bus.register_handler("test.event", handler, filters=[filter_even])

    await event_bus.emit("test.event", {"value": 1})  # Odd - filtered
    await event_bus.emit("test.event", {"value": 2})  # Even - passes
    await event_bus.emit("test.event", {"value": 3})  # Odd - filtered
    await asyncio.sleep(0.01)

    assert received == [2]


@pytest.mark.asyncio
async def test_multiple_filters(event_bus):
    """All filters must pass for handler to execute"""
    # Bus is provided by fixture
    received = []

    async def handler(event, ctx):
        received.append(event.data["value"])

    def greater_than_10(event):
        return event.data["value"] > 10

    def less_than_20(event):
        return event.data["value"] < 20

    def is_even(event):
        return event.data["value"] % 2 == 0

    event_bus.register_handler("test.event", handler, filters=[greater_than_10, less_than_20, is_even])

    # Test various values
    for value in [5, 10, 11, 12, 15, 18, 20, 22]:
        await event_bus.emit("test.event", {"value": value})

    await asyncio.sleep(0.01)

    # Only 12 and 18 pass all filters (>10, <20, even)
    assert received == [12, 18]


@pytest.mark.asyncio
async def test_priority_ordering(event_bus):
    """Handlers should execute in priority order"""
    # Bus is provided by fixture
    order = []

    async def high_priority(event, ctx):
        order.append("high")

    async def medium_priority(event, ctx):
        order.append("medium")

    async def low_priority(event, ctx):
        order.append("low")

    # Register in reverse priority order to test sorting
    event_bus.register_handler("test.event", low_priority, priority=10)
    event_bus.register_handler("test.event", medium_priority, priority=5)
    event_bus.register_handler("test.event", high_priority, priority=1)

    await event_bus.emit("test.event", {})
    await asyncio.sleep(0.01)

    # Should execute in priority order (lower number = higher priority)
    assert order == ["high", "medium", "low"]


@pytest.mark.asyncio
async def test_error_isolation(event_bus):
    """Error in one handler shouldn't affect others"""
    # Bus is provided by fixture
    results = []

    async def failing_handler(event, ctx):
        raise Exception("I fail!")

    async def working_handler(event, ctx):
        results.append("success")

    event_bus.register_handler("test.event", failing_handler)
    event_bus.register_handler("test.event", working_handler)

    await event_bus.emit("test.event", {})
    await asyncio.sleep(0.01)

    assert "success" in results


@pytest.mark.asyncio
async def test_unregister_handler(event_bus):
    """Unregistered handler should not receive events"""
    # Bus is provided by fixture
    received = []

    async def handler(event, ctx):
        received.append(event.data)

    event_bus.register_handler("test.event", handler)

    await event_bus.emit("test.event", {"count": 1})
    await asyncio.sleep(0.01)

    event_bus.unregister_handler("test.event", handler)

    await event_bus.emit("test.event", {"count": 2})
    await asyncio.sleep(0.01)

    assert len(received) == 1
    assert received[0]["count"] == 1


@pytest.mark.asyncio
async def test_event_source_tracking(event_bus):
    """Events should track their source"""
    # Bus is provided by fixture
    received_events = []

    async def handler(event, ctx):
        received_events.append(event)

    event_bus.register_handler("test.event", handler)

    await event_bus.emit("test.event", {"data": "test"}, source="twitch")
    await asyncio.sleep(0.01)

    assert len(received_events) == 1
    assert received_events[0].source == "twitch"


@pytest.mark.asyncio
async def test_no_handlers(event_bus):
    """Events with no handlers should be silently dropped"""
    # Bus is provided by fixture

    # Should not raise any errors
    await event_bus.emit("unhandled.event", {"data": "test"})
    await asyncio.sleep(0.01)

    # Test passes if no exception was raised


@pytest.mark.asyncio
async def test_concurrent_handlers(event_bus):
    """Handlers should execute concurrently"""
    # Bus is provided by fixture
    execution_times = []

    async def slow_handler1(event, ctx):
        start = asyncio.get_event_loop().time()
        await asyncio.sleep(0.01)
        execution_times.append(("handler1", start))

    async def slow_handler2(event, ctx):
        start = asyncio.get_event_loop().time()
        await asyncio.sleep(0.01)
        execution_times.append(("handler2", start))

    event_bus.register_handler("test.event", slow_handler1)
    event_bus.register_handler("test.event", slow_handler2)

    start_time = asyncio.get_event_loop().time()
    await event_bus.emit("test.event", {})
    await asyncio.sleep(0.02)  # Wait for both to complete (they sleep 0.1s concurrently)
    end_time = asyncio.get_event_loop().time()

    # If handlers ran concurrently, total time should be ~0.02s, not ~0.2s
    total_time = end_time - start_time
    assert total_time < 0.05  # Some buffer for execution overhead

    # Both handlers should have started at roughly the same time
    assert len(execution_times) == 2
    time_diff = abs(execution_times[0][1] - execution_times[1][1])
    assert time_diff < 0.02  # Started within 20ms of each other


@pytest.mark.asyncio
async def test_middleware(event_bus):
    """Middleware should be able to modify events"""
    # Bus is provided by fixture
    received = []

    async def handler(event, ctx):
        received.append(event.data)

    async def add_timestamp_middleware(event):
        event.data["processed_at"] = "2024-01-01"
        return event

    async def filter_middleware(event):
        # Filter out events with blocked flag
        if event.data.get("blocked", False):
            return None
        return event

    event_bus.add_middleware(add_timestamp_middleware)
    event_bus.add_middleware(filter_middleware)
    event_bus.register_handler("test.event", handler)

    await event_bus.emit("test.event", {"value": 1})
    await event_bus.emit("test.event", {"value": 2, "blocked": True})
    await asyncio.sleep(0.01)

    assert len(received) == 1
    assert received[0]["value"] == 1
    assert received[0]["processed_at"] == "2024-01-01"


@pytest.mark.asyncio
async def test_error_handler(event_bus):
    """Global error handlers should be called on handler errors"""
    # Bus is provided by fixture
    errors_caught = []

    async def failing_handler(event, ctx):
        raise ValueError("Test error")

    async def error_handler(error, handler_name):
        errors_caught.append((type(error).__name__, handler_name))

    event_bus.add_error_handler(error_handler)
    event_bus.register_handler("test.event", failing_handler)

    await event_bus.emit("test.event", {})
    await asyncio.sleep(0.01)

    assert len(errors_caught) == 1
    assert errors_caught[0][0] == "ValueError"
    assert errors_caught[0][1] == "failing_handler"


@pytest.mark.asyncio
async def test_get_stats(event_bus):
    """get_stats should return bus statistics"""
    # Bus is provided by fixture

    async def handler1(event, ctx):
        pass

    async def handler2(event, ctx):
        pass

    event_bus.register_handler("event.one", handler1)
    event_bus.register_handler("event.one", handler2)
    event_bus.register_handler("event.two", handler1)

    stats = event_bus.get_stats()

    assert stats["running"]
    assert "event.one" in stats["registered_events"]
    assert "event.two" in stats["registered_events"]
    assert stats["handler_counts"]["event.one"] == 2
    assert stats["handler_counts"]["event.two"] == 1

    # Bus should remain running throughout test (managed by fixture)
    stats = event_bus.get_stats()
    assert stats["running"]


@pytest.mark.asyncio
async def test_filter_error_handling(event_bus):
    """Errors in filters should be caught and handler skipped"""
    # Bus is provided by fixture
    received = []

    async def handler(event, ctx):
        received.append(event.data)

    def broken_filter(event):
        raise RuntimeError("Filter is broken")

    def working_filter(event):
        return True

    event_bus.register_handler("test.event", handler, filters=[broken_filter, working_filter])

    await event_bus.emit("test.event", {"value": 1})
    await asyncio.sleep(0.01)

    # Handler should not have been called due to filter error
    assert len(received) == 0


@pytest.mark.asyncio
async def test_handler_timeout(event_bus):
    """Long-running handlers should not block the event bus"""
    # Bus is provided by fixture
    completed = []

    async def slow_handler(event, ctx):
        await asyncio.sleep(5)  # Very slow
        completed.append("slow")

    async def fast_handler(event, ctx):
        completed.append("fast")

    event_bus.register_handler("slow.event", slow_handler)
    event_bus.register_handler("fast.event", fast_handler)

    await event_bus.emit("slow.event", {})
    await event_bus.emit("fast.event", {})
    await asyncio.sleep(0.01)

    # Fast handler should complete even though slow is still running
    assert "fast" in completed
    assert "slow" not in completed


def test_event_creation():
    """Event should properly initialize with timestamp"""
    import time

    before = time.time()

    event = Event(type="test.event", data={"key": "value"}, source="test_source")

    after = time.time()

    assert event.type == "test.event"
    assert event.data == {"key": "value"}
    assert event.source == "test_source"
    assert before <= event.timestamp <= after


@pytest.mark.asyncio
async def test_unregister_module_handlers(event_bus):
    """Test that unregister_module_handlers removes all handlers from a module"""
    received = []

    async def chat_handler1(event, ctx):
        received.append("chat_handler1")

    async def chat_handler2(event, ctx):
        received.append("chat_handler2")

    async def alerts_handler(event, ctx):
        received.append("alerts_handler")

    # Manually track handlers by module to simulate module detection
    # In real usage, this would be done automatically by the registry
    event_bus.register_handler("test.message", chat_handler1)
    event_bus.register_handler("test.follow", chat_handler2)
    event_bus.register_handler("test.alert", alerts_handler)

    # Manually add to module tracking for testing
    event_bus.handler_registry.handlers_by_module["chat"] = [
        ("test.message", chat_handler1),
        ("test.follow", chat_handler2),
    ]
    event_bus.handler_registry.handlers_by_module["alerts"] = [
        ("test.alert", alerts_handler),
    ]

    # Test events before unregistering
    await event_bus.emit("test.message", {})
    await event_bus.emit("test.follow", {})
    await event_bus.emit("test.alert", {})
    await asyncio.sleep(0.01)

    assert len(received) == 3
    received.clear()

    # Unregister chat module handlers
    removed_count = event_bus.unregister_module_handlers("chat")
    assert removed_count == 2

    # Test events after unregistering chat handlers
    await event_bus.emit("test.message", {})
    await event_bus.emit("test.follow", {})
    await event_bus.emit("test.alert", {})
    await asyncio.sleep(0.01)

    # Only alerts handler should have executed
    assert received == ["alerts_handler"]
    assert "chat_handler1" not in received
    assert "chat_handler2" not in received


@pytest.mark.asyncio
async def test_add_event_hook(event_bus):
    """Test that we can add event hooks to track all events"""
    events_captured = []

    async def event_hook(event):
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

    async def event_hook(event):
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

    async def hook1(event):
        events_captured_1.append(event)

    async def hook2(event):
        events_captured_2.append(event)

    event_bus.add_event_hook(hook1)
    event_bus.add_event_hook(hook2)

    await event_bus.emit("test.event", {"data": "test"})
    await asyncio.sleep(0.1)

    # Both hooks should have captured the event
    assert len(events_captured_1) == 1
    assert len(events_captured_2) == 1
