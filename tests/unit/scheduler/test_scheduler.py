"""
Test schedule manager functionality
"""

import asyncio
from unittest.mock import AsyncMock, MagicMock

import pytest

from pantainos.core.di.container import ServiceContainer
from pantainos.core.event_bus import EventBus
from pantainos.scheduler import Cron, Interval, ScheduleManager, Watch
from pantainos.scheduler.events import IntervalExecutedEvent, WatchChangedEvent


@pytest.fixture
def mock_event_bus():
    """Create a mock event bus"""
    mock_bus = AsyncMock(spec=EventBus)
    return mock_bus


@pytest.fixture
def mock_container():
    """Create a mock service container"""
    mock_container = MagicMock(spec=ServiceContainer)
    return mock_container


@pytest.fixture
def schedule_manager(mock_event_bus, mock_container):
    """Create a schedule manager with mocked dependencies"""
    return ScheduleManager(mock_event_bus, mock_container)


@pytest.mark.asyncio
async def test_schedule_manager_creation(mock_event_bus, mock_container):
    """Test ScheduleManager can be created"""
    manager = ScheduleManager(mock_event_bus, mock_container)
    assert manager.event_bus is mock_event_bus
    assert manager.container is mock_container
    assert manager.running is False
    assert len(manager.scheduled_tasks) == 0


@pytest.mark.asyncio
async def test_add_interval_schedule(schedule_manager):
    """Test adding an interval schedule"""
    mock_handler = AsyncMock()
    interval = Interval(seconds=30)

    await schedule_manager.add_interval_schedule(mock_handler, interval)

    assert len(schedule_manager.scheduled_tasks) == 1
    task_info = schedule_manager.scheduled_tasks[0]
    assert task_info.handler is mock_handler
    assert task_info.schedule is interval
    assert task_info.type == "interval"


@pytest.mark.asyncio
async def test_add_cron_schedule(schedule_manager):
    """Test adding a cron schedule"""
    mock_handler = AsyncMock()
    cron = Cron(expression="0 9 * * *")

    await schedule_manager.add_cron_schedule(mock_handler, cron)

    assert len(schedule_manager.scheduled_tasks) == 1
    task_info = schedule_manager.scheduled_tasks[0]
    assert task_info.handler is mock_handler
    assert task_info.schedule is cron
    assert task_info.type == "cron"


@pytest.mark.asyncio
async def test_add_watch_schedule(schedule_manager):
    """Test adding a database watch schedule"""
    mock_handler = AsyncMock()
    watch = Watch(query="SELECT * FROM users", check_interval=60)

    await schedule_manager.add_watch_schedule(mock_handler, watch)

    assert len(schedule_manager.scheduled_tasks) == 1
    task_info = schedule_manager.scheduled_tasks[0]
    assert task_info.handler is mock_handler
    assert task_info.schedule is watch
    assert task_info.type == "watch"


@pytest.mark.asyncio
async def test_start_stop_manager(schedule_manager):
    """Test starting and stopping the schedule manager"""
    # Add a simple interval task
    mock_handler = AsyncMock()
    interval = Interval(seconds=1)
    await schedule_manager.add_interval_schedule(mock_handler, interval)

    # Start the manager
    await schedule_manager.start()
    assert schedule_manager.running is True
    assert len(schedule_manager.background_tasks) == 1

    # Stop the manager
    await schedule_manager.stop()
    assert schedule_manager.running is False


@pytest.mark.asyncio
async def test_interval_execution(schedule_manager, mock_event_bus):
    """Test that interval schedules execute correctly"""
    mock_handler = AsyncMock()
    interval = Interval(seconds=0.1, start_immediately=True)  # Very short interval for testing

    await schedule_manager.add_interval_schedule(mock_handler, interval)
    await schedule_manager.start()

    # Wait a bit for execution
    await asyncio.sleep(0.2)

    # Check that event was emitted
    assert mock_event_bus.emit.called
    call_args = mock_event_bus.emit.call_args[0]
    event = call_args[0]  # First argument should be IntervalExecutedEvent
    assert isinstance(event, IntervalExecutedEvent)
    assert event.event_type == "@interval"
    assert event.seconds == 0.1  # event should contain interval info

    await schedule_manager.stop()


@pytest.mark.asyncio
async def test_watch_execution_with_results(schedule_manager, mock_event_bus):
    """Test that database watch executes when query returns results"""
    mock_handler = AsyncMock()
    watch = Watch(query="SELECT * FROM users", check_interval=0.1)  # Short interval for testing

    # Mock database query to return results
    mock_db = AsyncMock()
    mock_db.execute_query = AsyncMock(return_value=[{"id": 1, "name": "test"}])
    schedule_manager.container.resolve = MagicMock(return_value=mock_db)

    await schedule_manager.add_watch_schedule(mock_handler, watch)
    await schedule_manager.start()

    # Wait for execution
    await asyncio.sleep(0.2)

    # Check that event was emitted with results
    assert mock_event_bus.emit.called
    call_args = mock_event_bus.emit.call_args[0]
    event = call_args[0]  # First argument should be WatchChangedEvent
    assert isinstance(event, WatchChangedEvent)
    assert event.event_type == "@watch"
    assert event.query == "SELECT * FROM users"  # event should contain watch info

    await schedule_manager.stop()


@pytest.mark.asyncio
async def test_execution_count_increments(schedule_manager, mock_event_bus):
    """Test that execution count increments properly"""
    mock_handler = AsyncMock()
    interval = Interval(seconds=0.05, start_immediately=True)

    await schedule_manager.add_interval_schedule(mock_handler, interval)
    await schedule_manager.start()

    # Wait for multiple executions
    await asyncio.sleep(0.2)

    # Should have multiple calls with increasing execution count
    assert mock_event_bus.emit.call_count >= 2

    # Check first and last calls have different execution counts
    first_call_event = mock_event_bus.emit.call_args_list[0][0][0]  # First IntervalExecutedEvent
    last_call_event = mock_event_bus.emit.call_args_list[-1][0][0]  # Last IntervalExecutedEvent
    assert last_call_event.execution_count > first_call_event.execution_count

    await schedule_manager.stop()


@pytest.mark.asyncio
async def test_error_handling_in_schedule_execution(schedule_manager, mock_event_bus):
    """Test that errors in schedule execution don't crash the manager"""
    mock_handler = AsyncMock()
    interval = Interval(seconds=0.1)

    # Make emit raise an exception
    mock_event_bus.emit.side_effect = Exception("Test error")

    await schedule_manager.add_interval_schedule(mock_handler, interval)
    await schedule_manager.start()

    # Wait a bit - manager should still be running despite error
    await asyncio.sleep(0.2)
    assert schedule_manager.running is True

    await schedule_manager.stop()


@pytest.mark.asyncio
async def test_multiple_schedules(schedule_manager, mock_event_bus):
    """Test managing multiple different schedule types"""
    # Add multiple schedule types
    interval_handler = AsyncMock()
    cron_handler = AsyncMock()
    watch_handler = AsyncMock()

    interval = Interval(seconds=0.1)
    cron = Cron(expression="* * * * *")
    watch = Watch(query="SELECT 1", check_interval=0.1)

    await schedule_manager.add_interval_schedule(interval_handler, interval)
    await schedule_manager.add_cron_schedule(cron_handler, cron)
    await schedule_manager.add_watch_schedule(watch_handler, watch)

    assert len(schedule_manager.scheduled_tasks) == 3

    await schedule_manager.start()
    assert len(schedule_manager.background_tasks) == 3

    await schedule_manager.stop()
    assert schedule_manager.running is False
