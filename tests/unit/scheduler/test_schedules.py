"""
Test schedule event models and conditions
"""

from datetime import datetime

import pytest

from pantainos.scheduler import Cron, Interval, Schedule, Watch
from pantainos.scheduler.schedules import daily, every, hourly, watch


def test_schedule_base_class():
    """Test Schedule base class creation and conditions"""
    schedule = Schedule()
    assert schedule.event_type == "@schedule"
    assert isinstance(schedule.execution_time, datetime)
    assert schedule.execution_count == 0


def test_interval_creation():
    """Test Interval schedule creation"""
    interval = Interval(seconds=30)
    assert interval.event_type == "@interval"
    assert interval.seconds == 30
    assert not interval.start_immediately
    assert not interval.align_to_minute


def test_interval_convenience_methods():
    """Test Interval convenience methods"""
    # Test every_seconds
    interval1 = Interval.every_seconds(45)
    assert interval1.seconds == 45

    # Test every_minutes
    interval2 = Interval.every_minutes(5)
    assert interval2.seconds == 300  # 5 * 60

    # Test every_hours
    interval3 = Interval.every_hours(2)
    assert interval3.seconds == 7200  # 2 * 3600


def test_cron_creation():
    """Test Cron schedule creation"""
    cron = Cron(expression="0 9 * * *")
    assert cron.event_type == "@cron"
    assert cron.expression == "0 9 * * *"


def test_cron_convenience_methods():
    """Test Cron convenience methods"""
    # Test daily_at
    daily_cron = Cron.daily_at(9, 30)
    assert daily_cron.expression == "30 9 * * *"

    # Test weekly_at
    weekly_cron = Cron.weekly_at(1, 14)  # Tuesday at 2 PM
    assert weekly_cron.expression == "0 14 * * 1"


def test_watch_creation():
    """Test Watch database monitor creation"""
    watch_event = Watch(query="SELECT * FROM users WHERE points > 1000", check_interval=60)
    assert watch_event.event_type == "@watch"
    assert watch_event.query == "SELECT * FROM users WHERE points > 1000"
    assert watch_event.check_interval == 60
    assert not watch_event.detect_changes


def test_convenience_functions():
    """Test module-level convenience functions"""
    # Test every()
    interval = every(30)
    assert isinstance(interval, Interval)
    assert interval.seconds == 30

    # Test daily()
    cron = daily(9, 30)
    assert isinstance(cron, Cron)
    assert cron.expression == "30 9 * * *"

    # Test hourly()
    hourly_cron = hourly(15)
    assert isinstance(hourly_cron, Cron)
    assert hourly_cron.expression == "15 * * * *"

    # Test watch()
    watch_obj = watch("SELECT * FROM test")
    assert isinstance(watch_obj, Watch)
    assert watch_obj.query == "SELECT * FROM test"


def test_schedule_conditions():
    """Test Schedule base conditions"""
    # Create a schedule with specific execution time
    schedule = Schedule(execution_time=datetime(2024, 3, 15, 14, 30))  # Friday 2:30 PM

    # Test during_hours condition
    business_hours = Schedule.during_hours(9, 17)
    assert business_hours(schedule) is True  # 2:30 PM is within 9-17

    after_hours = Schedule.during_hours(18, 22)
    assert after_hours(schedule) is False  # 2:30 PM is not within 18-22

    # Test weekday condition
    weekday_condition = Schedule.on_weekdays()
    assert weekday_condition(schedule) is True  # Friday is a weekday

    # Test weekend condition
    weekend_condition = Schedule.on_weekends()
    assert weekend_condition(schedule) is False  # Friday is not a weekend


def test_watch_conditions():
    """Test Watch-specific conditions"""
    # Create watch with results
    watch_with_results = Watch(
        query="SELECT * FROM users", results=[{"id": 1, "points": 1500}, {"id": 2, "points": 800}]
    )

    # Test has_results condition
    has_results = Watch.has_results()
    assert has_results(watch_with_results) is True

    # Test min_results condition
    min_two = Watch.min_results(2)
    assert min_two(watch_with_results) is True

    min_three = Watch.min_results(3)
    assert min_three(watch_with_results) is False

    # Test result_equals condition
    points_check = Watch.result_equals("points", 1500)
    assert points_check(watch_with_results) is True


@pytest.mark.parametrize(
    "invalid_expression",
    [
        "* * * *",  # Only 4 parts
        "* * * * * *",  # 6 parts
        "",  # Empty
    ],
)
def test_cron_invalid_expressions(invalid_expression):
    """Test that invalid cron expressions are rejected"""
    with pytest.raises(ValueError):
        Cron(expression=invalid_expression)
