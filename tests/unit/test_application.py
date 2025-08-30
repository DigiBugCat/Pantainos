"""
Tests for Pantainos Application class - New Architecture
"""

import asyncio
from unittest.mock import AsyncMock, MagicMock

import pytest

from pantainos.events import GenericEvent


@pytest.mark.asyncio
async def test_application_event_handler_registration():
    """Test that @app.on() decorator registers handlers"""
    from pantainos.application import Pantainos

    app = Pantainos()
    handler_called = []

    @app.on("test.event")
    async def test_handler(event):
        handler_called.append(event)

    # Start event bus
    await app.event_bus.start()

    # Emit event
    from pantainos.events import GenericEvent

    await app.emit(GenericEvent(type="test.event", data={"test": "data"}))

    # Give event bus time to process
    import asyncio

    await asyncio.sleep(0.1)

    # Handler should have been called
    assert len(handler_called) == 1
    assert handler_called[0].type == "test.event"
    assert handler_called[0].data == {"test": "data"}

    await app.event_bus.stop()


@pytest.mark.asyncio
async def test_application_plugin_mounting():
    """Test that plugins can be mounted"""
    from pantainos.application import Pantainos

    app = Pantainos()

    # Create mock plugin
    mock_plugin = MagicMock()
    mock_plugin.name = "test_plugin"

    # Mount plugin
    app.mount(mock_plugin)

    # Plugin should be stored
    plugins = app.plugin_registry.get_all()
    assert "test_plugin" in plugins
    assert plugins["test_plugin"] == mock_plugin

    # Plugin should be registered in container
    registered = app.container.resolve(type(mock_plugin))
    assert registered == mock_plugin


@pytest.mark.asyncio
async def test_application_start_stop():
    """Test that application can start and stop"""
    from pantainos.application import Pantainos

    app = Pantainos(database_url=":memory:")

    # Mock database initialization to avoid file system
    app._initialize_database = AsyncMock()

    # Should start successfully
    await app.start()

    # Event bus should be running
    assert app.event_bus.running is True

    # Should stop successfully
    await app.stop()

    # Event bus should be stopped
    assert app.event_bus.running is False


@pytest.mark.asyncio
async def test_application_with_conditions():
    """Test that event handlers work with conditions"""
    from pantainos.application import Pantainos
    from pantainos.events import equals

    app = Pantainos()
    handler_called = []

    @app.on("test.event", when=equals("value", "match"))
    async def test_handler(event):
        handler_called.append(event)

    await app.event_bus.start()

    # Emit event that doesn't match condition
    await app.emit(GenericEvent(type="test.event", data={"value": "nomatch"}))
    await asyncio.sleep(0.1)

    # Handler should not be called
    assert len(handler_called) == 0

    # Emit event that matches condition
    await app.emit(GenericEvent(type="test.event", data={"value": "match"}))
    await asyncio.sleep(0.1)

    # Handler should be called
    assert len(handler_called) == 1

    await app.event_bus.stop()


@pytest.mark.asyncio
async def test_application_scheduled_events():
    """Test that application supports scheduled events"""
    from pantainos.application import Pantainos
    from pantainos.scheduler import Cron, Interval, Watch

    app = Pantainos()
    handler_called = []

    @app.on(Interval(seconds=30))
    async def interval_handler(event):
        handler_called.append(("interval", event))

    @app.on(Cron(expression="0 9 * * *"))
    async def cron_handler(event):
        handler_called.append(("cron", event))

    @app.on(Watch(query="SELECT * FROM test"))
    async def watch_handler(event):
        handler_called.append(("watch", event))

    # Should have schedule manager
    assert hasattr(app, "schedule_manager")
    assert app.schedule_manager is not None

    # Should have registered scheduled tasks
    assert len(app.schedule_manager.scheduled_tasks) == 3

    task_types = [task.type for task in app.schedule_manager.scheduled_tasks]
    assert "interval" in task_types
    assert "cron" in task_types
    assert "watch" in task_types


@pytest.mark.asyncio
async def test_application_schedule_manager_lifecycle():
    """Test that schedule manager starts and stops with application"""
    from pantainos.application import Pantainos
    from pantainos.scheduler import Interval

    app = Pantainos(database_url=":memory:")

    # Mock database initialization
    app._initialize_database = AsyncMock()

    @app.on(Interval(seconds=60))
    async def test_handler(event):
        pass

    # Schedule manager should exist but not be running
    assert hasattr(app, "schedule_manager")
    assert not app.schedule_manager.running

    # Start application
    await app.start()

    # Schedule manager should be running
    assert app.schedule_manager.running

    # Stop application
    await app.stop()

    # Schedule manager should be stopped
    assert not app.schedule_manager.running


@pytest.mark.asyncio
async def test_application_mixed_event_types():
    """Test that application handles both regular and scheduled events"""
    from pantainos.application import Pantainos
    from pantainos.scheduler import Interval

    app = Pantainos()
    handlers_called = []

    @app.on("regular.event")
    async def regular_handler(event):
        handlers_called.append("regular")

    @app.on(Interval(seconds=30))
    async def scheduled_handler(event):
        handlers_called.append("scheduled")

    # Should have both regular event handlers and scheduled tasks
    assert len(app.event_bus.handlers) >= 1  # Regular event handler
    assert len(app.schedule_manager.scheduled_tasks) == 1  # Scheduled task

    await app.event_bus.start()

    # Test regular event
    await app.emit(GenericEvent(type="regular.event", data={}))
    await asyncio.sleep(0.1)

    # Should have called regular handler
    assert "regular" in handlers_called

    await app.event_bus.stop()
