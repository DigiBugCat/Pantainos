"""
Tests for scheduler task models
"""

from unittest.mock import AsyncMock

import pytest

from pantainos.scheduler.schedules import Cron, Interval, Watch
from pantainos.scheduler.tasks import CronTask, IntervalTask, ScheduledTask, WatchTask


@pytest.fixture
def async_handler():
    """Create mock async handler"""
    return AsyncMock()


@pytest.fixture
def interval_schedule():
    """Create test interval schedule"""
    return Interval(seconds=30)


@pytest.fixture
def cron_schedule():
    """Create test cron schedule"""
    return Cron(expression="0 9 * * *")


@pytest.fixture
def watch_schedule():
    """Create test watch schedule"""
    return Watch(query="SELECT * FROM users", check_interval=60)


def test_scheduled_task_creation(async_handler, interval_schedule):
    """Test basic ScheduledTask creation"""
    task = ScheduledTask(handler=async_handler, schedule=interval_schedule)

    assert task.handler == async_handler
    assert task.schedule == interval_schedule
    assert task.execution_count == 0


def test_scheduled_task_execution_count_increment(async_handler, interval_schedule):
    """Test execution count can be incremented"""
    task = ScheduledTask(handler=async_handler, schedule=interval_schedule)

    task.execution_count += 1
    assert task.execution_count == 1

    task.execution_count += 5
    assert task.execution_count == 6


def test_interval_task_creation(async_handler, interval_schedule):
    """Test IntervalTask creation with defaults"""
    task = IntervalTask(handler=async_handler, schedule=interval_schedule)

    assert task.handler == async_handler
    assert task.schedule == interval_schedule
    assert task.type == "interval"
    assert task.execution_count == 0
    assert task.last_execution == 0.0


def test_interval_task_with_custom_values(async_handler, interval_schedule):
    """Test IntervalTask with custom execution count and last execution"""
    task = IntervalTask(handler=async_handler, schedule=interval_schedule, execution_count=5, last_execution=1234567.89)

    assert task.execution_count == 5
    assert task.last_execution == 1234567.89
    assert task.type == "interval"


def test_interval_task_schedule_validation(async_handler, cron_schedule):
    """Test IntervalTask requires Interval schedule"""
    # Should work with proper type
    interval = Interval(seconds=30)
    task = IntervalTask(handler=async_handler, schedule=interval)
    assert isinstance(task.schedule, Interval)

    # Pydantic v2 properly validates schedule type
    with pytest.raises(ValueError, match="Input should be a valid dictionary or instance of Interval"):
        IntervalTask(handler=async_handler, schedule=cron_schedule)


def test_cron_task_creation(async_handler, cron_schedule):
    """Test CronTask creation with required fields"""
    next_exec_time = 1234567890.0
    task = CronTask(handler=async_handler, schedule=cron_schedule, next_execution=next_exec_time)

    assert task.handler == async_handler
    assert task.schedule == cron_schedule
    assert task.type == "cron"
    assert task.execution_count == 0
    assert task.next_execution == next_exec_time


def test_cron_task_with_custom_values(async_handler, cron_schedule):
    """Test CronTask with custom execution count"""
    task = CronTask(handler=async_handler, schedule=cron_schedule, next_execution=1234567890.0, execution_count=10)

    assert task.execution_count == 10
    assert task.type == "cron"


def test_cron_task_requires_next_execution(async_handler, cron_schedule):
    """Test CronTask requires next_execution field"""
    with pytest.raises(ValueError):
        CronTask(handler=async_handler, schedule=cron_schedule)


def test_watch_task_creation(async_handler, watch_schedule):
    """Test WatchTask creation with defaults"""
    task = WatchTask(handler=async_handler, schedule=watch_schedule)

    assert task.handler == async_handler
    assert task.schedule == watch_schedule
    assert task.type == "watch"
    assert task.execution_count == 0
    assert task.last_check == 0.0
    assert task.previous_results == []
    assert task.current_results is None
    assert task.has_changes is False


def test_watch_task_with_results(async_handler, watch_schedule):
    """Test WatchTask with query results and changes"""
    previous_results = [{"id": 1, "name": "test1"}]
    current_results = [{"id": 1, "name": "test1"}, {"id": 2, "name": "test2"}]

    task = WatchTask(
        handler=async_handler,
        schedule=watch_schedule,
        previous_results=previous_results,
        current_results=current_results,
        has_changes=True,
        last_check=1234567890.0,
    )

    assert task.previous_results == previous_results
    assert task.current_results == current_results
    assert task.has_changes is True
    assert task.last_check == 1234567890.0


def test_watch_task_change_detection(async_handler, watch_schedule):
    """Test WatchTask change detection logic"""
    task = WatchTask(handler=async_handler, schedule=watch_schedule)

    # Initially no changes
    assert task.has_changes is False
    assert task.previous_results == []
    assert task.current_results is None

    # Simulate detecting changes
    task.current_results = [{"id": 1, "count": 5}]
    task.has_changes = len(task.current_results) != len(task.previous_results)
    assert task.has_changes is True

    # Update previous results for next check
    task.previous_results = task.current_results.copy()
    task.current_results = [{"id": 1, "count": 5}]  # Same results
    task.has_changes = task.current_results != task.previous_results
    assert task.has_changes is False


def test_scheduled_task_pydantic_validation():
    """Test Pydantic validation on task models"""
    # Test missing required field
    with pytest.raises(ValueError):
        IntervalTask()  # Missing handler and schedule

    # Test invalid handler type (Pydantic v2 properly validates callables)
    handler = "not_a_function"  # Invalid handler type
    schedule = Interval(seconds=30)
    with pytest.raises(ValueError, match="Input should be callable"):
        IntervalTask(handler=handler, schedule=schedule)


def test_task_model_inheritance():
    """Test that task models properly inherit from ScheduledTask"""
    handler = AsyncMock()

    interval_task = IntervalTask(handler=handler, schedule=Interval(seconds=30))
    cron_task = CronTask(handler=handler, schedule=Cron(expression="0 9 * * *"), next_execution=123.0)
    watch_task = WatchTask(handler=handler, schedule=Watch(query="SELECT 1", check_interval=60))

    # All should be instances of ScheduledTask
    assert isinstance(interval_task, ScheduledTask)
    assert isinstance(cron_task, ScheduledTask)
    assert isinstance(watch_task, ScheduledTask)

    # All should have common ScheduledTask fields
    for task in [interval_task, cron_task, watch_task]:
        assert hasattr(task, "handler")
        assert hasattr(task, "schedule")
        assert hasattr(task, "execution_count")


def test_task_field_descriptions():
    """Test that task models have proper field descriptions"""
    handler = AsyncMock()
    interval = Interval(seconds=30)
    task = IntervalTask(handler=handler, schedule=interval)

    # Check that fields have descriptions (from Pydantic Field) using v2 API
    fields = task.model_fields
    assert fields["handler"].description is not None
    assert fields["schedule"].description is not None
    assert fields["execution_count"].description is not None


def test_task_serialization():
    """Test that task models can be serialized (excluding handler)"""
    handler = AsyncMock()
    interval = Interval(seconds=30)
    task = IntervalTask(handler=handler, schedule=interval, execution_count=5)

    # Get dict representation (handler won't serialize properly but that's expected)
    task_dict = task.dict()
    assert task_dict["execution_count"] == 5
    assert task_dict["type"] == "interval"
    assert task_dict["last_execution"] == 0.0


def test_task_type_literals():
    """Test that task type fields are properly typed as literals"""
    handler = AsyncMock()

    interval_task = IntervalTask(handler=handler, schedule=Interval(seconds=30))
    cron_task = CronTask(handler=handler, schedule=Cron(expression="0 9 * * *"), next_execution=123.0)
    watch_task = WatchTask(handler=handler, schedule=Watch(query="SELECT 1", check_interval=60))

    assert interval_task.type == "interval"
    assert cron_task.type == "cron"
    assert watch_task.type == "watch"

    # Type should be readonly (though Pydantic doesn't enforce this at runtime)
    interval_task.type = "wrong"  # This will work but defeats the purpose
    assert interval_task.type == "wrong"  # Shows limitation of runtime typing
