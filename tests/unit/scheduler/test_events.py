"""
Tests for scheduler event models
"""

from datetime import datetime

import pytest

from pantainos.scheduler.events import CronTriggeredEvent, IntervalExecutedEvent, WatchChangedEvent


def test_interval_executed_event_creation():
    """Test IntervalExecutedEvent creation with all fields"""
    execution_time = datetime(2024, 3, 15, 14, 30, 0)
    event = IntervalExecutedEvent(
        source="scheduler",
        execution_time=execution_time,
        execution_count=5,
        seconds=30.0,
        start_immediately=True,
        align_to_minute=False,
    )

    assert event.event_type == "@interval"
    assert event.source == "scheduler"
    assert event.execution_time == execution_time
    assert event.execution_count == 5
    assert event.seconds == 30.0
    assert event.start_immediately is True
    assert event.align_to_minute is False


def test_interval_executed_event_default_values():
    """Test IntervalExecutedEvent with minimal required fields"""
    execution_time = datetime(2024, 3, 15, 14, 30, 0)
    event = IntervalExecutedEvent(
        source="scheduler",
        execution_time=execution_time,
        execution_count=1,
        seconds=60.0,
        start_immediately=False,
        align_to_minute=False,
    )

    assert event.event_type == "@interval"
    assert event.execution_count == 1
    assert event.seconds == 60.0
    assert event.start_immediately is False
    assert event.align_to_minute is False


def test_interval_executed_event_serialization():
    """Test IntervalExecutedEvent can be serialized"""
    execution_time = datetime(2024, 3, 15, 14, 30, 0)
    event = IntervalExecutedEvent(
        source="scheduler",
        execution_time=execution_time,
        execution_count=3,
        seconds=45.5,
        start_immediately=True,
        align_to_minute=True,
    )

    event_dict = event.model_dump()
    # event_type is a ClassVar so not included in serialization
    assert event.event_type == "@interval"  # Access from instance
    assert event_dict["execution_count"] == 3
    assert event_dict["seconds"] == 45.5
    assert event_dict["start_immediately"] is True
    assert event_dict["align_to_minute"] is True


def test_cron_triggered_event_creation():
    """Test CronTriggeredEvent creation with all fields"""
    execution_time = datetime(2024, 3, 15, 9, 0, 0)
    scheduled_time = datetime(2024, 3, 15, 9, 0, 0)
    event = CronTriggeredEvent(
        source="scheduler",
        execution_time=execution_time,
        execution_count=10,
        expression="0 9 * * *",
        timezone="UTC",
        scheduled_time=scheduled_time,
    )

    assert event.event_type == "@cron"
    assert event.source == "scheduler"
    assert event.execution_time == execution_time
    assert event.execution_count == 10
    assert event.expression == "0 9 * * *"
    assert event.timezone == "UTC"
    assert event.scheduled_time == scheduled_time


def test_cron_triggered_event_without_timezone():
    """Test CronTriggeredEvent without timezone specified"""
    execution_time = datetime(2024, 3, 15, 12, 0, 0)
    scheduled_time = datetime(2024, 3, 15, 12, 0, 0)
    event = CronTriggeredEvent(
        source="scheduler",
        execution_time=execution_time,
        execution_count=1,
        expression="0 12 * * *",
        timezone=None,
        scheduled_time=scheduled_time,
    )

    assert event.event_type == "@cron"
    assert event.timezone is None
    assert event.expression == "0 12 * * *"


def test_cron_triggered_event_serialization():
    """Test CronTriggeredEvent can be serialized"""
    execution_time = datetime(2024, 3, 15, 18, 30, 0)
    scheduled_time = datetime(2024, 3, 15, 18, 30, 0)
    event = CronTriggeredEvent(
        source="scheduler",
        execution_time=execution_time,
        execution_count=7,
        expression="30 18 * * *",
        timezone="America/New_York",
        scheduled_time=scheduled_time,
    )

    event_dict = event.model_dump()
    # event_type is a ClassVar so not included in serialization
    assert event.event_type == "@cron"  # Access from instance
    assert event_dict["execution_count"] == 7
    assert event_dict["expression"] == "30 18 * * *"
    assert event_dict["timezone"] == "America/New_York"


def test_watch_changed_event_creation():
    """Test WatchChangedEvent creation with all fields"""
    execution_time = datetime(2024, 3, 15, 16, 45, 0)
    event = WatchChangedEvent(
        source="scheduler",
        execution_time=execution_time,
        execution_count=15,
        query="SELECT * FROM users WHERE points > 1000",
        check_interval=120.0,
        detect_changes=True,
        has_changes=True,
        current_result_count=8,
        previous_result_count=5,
    )

    assert event.event_type == "@watch"
    assert event.source == "scheduler"
    assert event.execution_time == execution_time
    assert event.execution_count == 15
    assert event.query == "SELECT * FROM users WHERE points > 1000"
    assert event.check_interval == 120.0
    assert event.detect_changes is True
    assert event.has_changes is True
    assert event.current_result_count == 8
    assert event.previous_result_count == 5


def test_watch_changed_event_no_previous_results():
    """Test WatchChangedEvent without previous results (first run)"""
    execution_time = datetime(2024, 3, 15, 10, 0, 0)
    event = WatchChangedEvent(
        source="scheduler",
        execution_time=execution_time,
        execution_count=1,
        query="SELECT id FROM new_table",
        check_interval=60.0,
        detect_changes=False,
        has_changes=False,
        current_result_count=3,
        previous_result_count=None,
    )

    assert event.event_type == "@watch"
    assert event.execution_count == 1
    assert event.detect_changes is False
    assert event.has_changes is False
    assert event.current_result_count == 3
    assert event.previous_result_count is None


def test_watch_changed_event_no_changes():
    """Test WatchChangedEvent when no changes detected"""
    execution_time = datetime(2024, 3, 15, 11, 30, 0)
    event = WatchChangedEvent(
        source="scheduler",
        execution_time=execution_time,
        execution_count=20,
        query="SELECT COUNT(*) FROM stable_table",
        check_interval=300.0,
        detect_changes=True,
        has_changes=False,
        current_result_count=100,
        previous_result_count=100,
    )

    assert event.event_type == "@watch"
    assert event.detect_changes is True
    assert event.has_changes is False
    assert event.current_result_count == 100
    assert event.previous_result_count == 100


def test_watch_changed_event_serialization():
    """Test WatchChangedEvent can be serialized"""
    execution_time = datetime(2024, 3, 15, 13, 15, 0)
    event = WatchChangedEvent(
        source="scheduler",
        execution_time=execution_time,
        execution_count=42,
        query="SELECT * FROM orders WHERE status = 'pending'",
        check_interval=30.0,
        detect_changes=True,
        has_changes=True,
        current_result_count=12,
        previous_result_count=8,
    )

    event_dict = event.model_dump()
    # event_type is a ClassVar so not included in serialization
    assert event.event_type == "@watch"  # Access from instance
    assert event_dict["execution_count"] == 42
    assert event_dict["query"] == "SELECT * FROM orders WHERE status = 'pending'"
    assert event_dict["check_interval"] == 30.0
    assert event_dict["detect_changes"] is True
    assert event_dict["has_changes"] is True
    assert event_dict["current_result_count"] == 12
    assert event_dict["previous_result_count"] == 8


def test_event_type_class_variables():
    """Test that event types are properly set as class variables"""
    # These should be accessible without instantiation
    assert IntervalExecutedEvent.event_type == "@interval"
    assert CronTriggeredEvent.event_type == "@cron"
    assert WatchChangedEvent.event_type == "@watch"


def test_event_inheritance_from_event_model():
    """Test that all events inherit from EventModel"""
    execution_time = datetime.now()

    interval_event = IntervalExecutedEvent(
        source="test",
        execution_time=execution_time,
        execution_count=1,
        seconds=30.0,
        start_immediately=False,
        align_to_minute=False,
    )

    cron_event = CronTriggeredEvent(
        source="test",
        execution_time=execution_time,
        execution_count=1,
        expression="0 * * * *",
        timezone=None,
        scheduled_time=execution_time,
    )

    watch_event = WatchChangedEvent(
        source="test",
        execution_time=execution_time,
        execution_count=1,
        query="SELECT 1",
        check_interval=60.0,
        detect_changes=False,
        has_changes=False,
        current_result_count=1,
        previous_result_count=None,
    )

    # All should have common EventModel fields
    for event in [interval_event, cron_event, watch_event]:
        assert hasattr(event, "source")
        assert hasattr(event, "execution_time")
        assert hasattr(event, "execution_count")
        assert hasattr(event, "event_type")


def test_event_validation():
    """Test that events properly validate required fields"""
    with pytest.raises(ValueError):
        IntervalExecutedEvent()  # Missing required fields

    with pytest.raises(ValueError):
        CronTriggeredEvent()  # Missing required fields

    with pytest.raises(ValueError):
        WatchChangedEvent()  # Missing required fields


def test_event_field_descriptions():
    """Test that event models have field descriptions"""
    execution_time = datetime.now()

    interval_event = IntervalExecutedEvent(
        source="test",
        execution_time=execution_time,
        execution_count=1,
        seconds=30.0,
        start_immediately=False,
        align_to_minute=False,
    )

    # Check that fields have descriptions using v2 API (access from class)
    fields = IntervalExecutedEvent.model_fields
    assert fields["execution_time"].description is not None
    assert fields["execution_count"].description is not None
    assert fields["seconds"].description is not None
    assert fields["start_immediately"].description is not None
    assert fields["align_to_minute"].description is not None


def test_event_timestamps():
    """Test that events properly handle datetime fields"""
    execution_time = datetime(2024, 12, 25, 15, 30, 45, 123456)
    scheduled_time = datetime(2024, 12, 25, 15, 30, 0)

    cron_event = CronTriggeredEvent(
        source="test",
        execution_time=execution_time,
        execution_count=1,
        expression="30 15 25 12 *",
        timezone="UTC",
        scheduled_time=scheduled_time,
    )

    # Should preserve exact datetime values
    assert cron_event.execution_time == execution_time
    assert cron_event.scheduled_time == scheduled_time

    # Should handle microseconds
    assert cron_event.execution_time.microsecond == 123456


def test_event_numeric_fields():
    """Test that events properly handle numeric field types"""
    execution_time = datetime.now()

    # Test various numeric types
    interval_event = IntervalExecutedEvent(
        source="test",
        execution_time=execution_time,
        execution_count=999999,  # Large int
        seconds=0.001,  # Small float
        start_immediately=True,
        align_to_minute=False,
    )

    assert interval_event.execution_count == 999999
    assert interval_event.seconds == 0.001

    watch_event = WatchChangedEvent(
        source="test",
        execution_time=execution_time,
        execution_count=0,  # Zero
        query="SELECT 1",
        check_interval=1.5,  # Float
        detect_changes=True,
        has_changes=True,
        current_result_count=0,  # Zero results
        previous_result_count=10000,  # Large count
    )

    assert watch_event.execution_count == 0
    assert watch_event.check_interval == 1.5
    assert watch_event.current_result_count == 0
    assert watch_event.previous_result_count == 10000
