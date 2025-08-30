"""
Scheduled Events - Timer, Cron, and Database Watch triggers

This module provides event models for scheduled and reactive triggers,
enabling advanced users to create periodic tasks, cron-like scheduling,
and database-reactive handlers while maintaining the clean @app.on() API.
"""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Any, ClassVar, Self

from pydantic import Field, field_validator

from pantainos.events import EventModel

if TYPE_CHECKING:
    from pantainos.events import Condition


class Schedule(EventModel):
    """
    Base class for all scheduled events.

    Scheduled events are emitted by the application's schedule manager
    rather than external sources, enabling periodic and reactive handlers.
    """

    event_type: ClassVar[str] = "@schedule"

    # Execution metadata added by scheduler
    execution_time: datetime = Field(default_factory=datetime.now, description="When this scheduled event was fired")
    scheduled_time: datetime | None = Field(default=None, description="When this event was originally scheduled")
    execution_count: int = Field(default=0, description="How many times this schedule has executed")

    @classmethod
    def during_hours(cls, start_hour: int, end_hour: int) -> Condition[Self]:
        """Check if execution time falls within specified hours (24h format)"""

        def check(event: Self) -> bool:
            hour = event.execution_time.hour
            if start_hour <= end_hour:
                return start_hour <= hour < end_hour
            # Handle overnight range (e.g., 22-6)
            return hour >= start_hour or hour < end_hour

        return cls.condition(check, f"during_hours({start_hour}-{end_hour})")

    @classmethod
    def on_weekdays(cls) -> Condition[Self]:
        """Check if execution time falls on weekdays (Monday-Friday)"""

        def check(event: Self) -> bool:
            return event.execution_time.weekday() < 5  # 0-4 are weekdays

        return cls.condition(check, "on_weekdays")

    @classmethod
    def on_weekends(cls) -> Condition[Self]:
        """Check if execution time falls on weekends (Saturday-Sunday)"""

        def check(event: Self) -> bool:
            return event.execution_time.weekday() >= 5  # 5-6 are weekends

        return cls.condition(check, "on_weekends")


class Interval(Schedule):
    """
    Execute on a regular interval.
    """

    event_type: ClassVar[str] = "@interval"

    seconds: float = Field(gt=0, description="Interval in seconds between executions")
    start_immediately: bool = Field(default=False, description="Execute immediately on start")
    align_to_minute: bool = Field(default=False, description="Align executions to minute boundaries")

    @classmethod
    def every_seconds(cls, seconds: float, **kwargs: Any) -> Interval:
        """Convenience method to create an interval"""
        return cls(seconds=seconds, **kwargs)

    @classmethod
    def every_minutes(cls, minutes: float, **kwargs: Any) -> Interval:
        """Convenience method to create a minute-based interval"""
        return cls(seconds=minutes * 60, **kwargs)

    @classmethod
    def every_hours(cls, hours: float, **kwargs: Any) -> Interval:
        """Convenience method to create an hour-based interval"""
        return cls(seconds=hours * 3600, **kwargs)


class Cron(Schedule):
    """
    Execute based on cron-like expressions.
    """

    event_type: ClassVar[str] = "@cron"

    expression: str = Field(description="Cron expression (minute hour day month weekday)")
    timezone: str | None = Field(default=None, description="Timezone for cron execution")

    @field_validator("expression")
    @classmethod
    def validate_cron_expression(cls, v: str) -> str:
        """Validate cron expression format"""
        # Basic validation - 5 parts separated by spaces
        parts = v.strip().split()
        if len(parts) != 5:
            raise ValueError("Cron expression must have 5 parts: minute hour day month weekday")
        return v

    @classmethod
    def daily_at(cls, hour: int, minute: int = 0) -> Cron:
        """Convenience method for daily execution at specific time"""
        return cls(expression=f"{minute} {hour} * * *")

    @classmethod
    def weekly_at(cls, weekday: int, hour: int, minute: int = 0) -> Cron:
        """Convenience method for weekly execution (0=Monday, 6=Sunday)"""
        return cls(expression=f"{minute} {hour} * * {weekday}")


class Watch(Schedule):
    """
    Execute when database query results change.
    """

    event_type: ClassVar[str] = "@watch"

    query: str = Field(description="SQL query to monitor")
    params: list[Any] = Field(default_factory=list, description="Query parameters")
    check_interval: float = Field(default=60.0, gt=0, description="Seconds between checks")
    detect_changes: bool = Field(default=False, description="Only execute when results change")

    # Results populated by scheduler
    results: list[dict[str, Any]] = Field(default_factory=list, description="Current query results")
    previous_results: list[dict[str, Any]] = Field(
        default_factory=list, description="Previous query results (if detect_changes=True)"
    )
    has_changes: bool = Field(default=False, description="True if results changed from previous check")
    results_count: int = Field(default=0, description="Number of results returned")

    @classmethod
    def has_results(cls) -> Condition[Self]:
        """Check if query returned any results"""

        def check(event: Self) -> bool:
            return len(event.results) > 0

        return cls.condition(check, "has_results")

    @classmethod
    def min_results(cls, count: int) -> Condition[Self]:
        """Check if query returned at least N results"""

        def check(event: Self) -> bool:
            return len(event.results) >= count

        return cls.condition(check, f"min_results({count})")

    @classmethod
    def result_equals(cls, field: str, value: Any) -> Condition[Self]:
        """Check if a field in the first result equals a value"""

        def check(event: Self) -> bool:
            if not event.results:
                return False
            return bool(event.results[0].get(field) == value)

        return cls.condition(check, f"result_equals({field}, {value})")


# Convenience functions for creating schedules
def every(seconds: float, **kwargs: Any) -> Interval:
    """Create an interval schedule - every(30) for every 30 seconds"""
    return Interval(seconds=seconds, **kwargs)


def daily(hour: int, minute: int = 0, **kwargs: Any) -> Cron:
    """Create a daily schedule - daily(9, 30) for 9:30 AM daily"""
    return Cron.daily_at(hour, minute, **kwargs)


def hourly(minute: int = 0, **kwargs: Any) -> Cron:
    """Create an hourly schedule - hourly(15) for 15 minutes past every hour"""
    return Cron(expression=f"{minute} * * * *", **kwargs)


def watch(query: str, check_interval: float = 60.0, **kwargs: Any) -> Watch:
    """Create a database watch - watch("SELECT * FROM users") to monitor users table"""
    return Watch(query=query, check_interval=check_interval, **kwargs)
