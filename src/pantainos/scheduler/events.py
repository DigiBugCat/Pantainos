"""
Scheduler-specific event models.

This module provides strongly-typed event models for scheduler executions,
replacing generic events with specific typed models.
"""

from __future__ import annotations

from datetime import datetime
from typing import ClassVar

from pydantic import Field

from pantainos.events import EventModel


class IntervalExecutedEvent(EventModel):
    """Event emitted when an interval schedule executes."""

    event_type: ClassVar[str] = "@interval"

    execution_time: datetime = Field(description="When this execution occurred")
    execution_count: int = Field(description="Number of times this task has executed")
    seconds: float = Field(description="Interval duration in seconds")
    start_immediately: bool = Field(description="Whether task starts immediately on first run")
    align_to_minute: bool = Field(description="Whether execution aligns to minute boundaries")


class CronTriggeredEvent(EventModel):
    """Event emitted when a cron schedule triggers."""

    event_type: ClassVar[str] = "@cron"

    execution_time: datetime = Field(description="When this execution occurred")
    execution_count: int = Field(description="Number of times this task has executed")
    expression: str = Field(description="Cron expression that triggered this execution")
    timezone: str | None = Field(description="Timezone for cron evaluation")
    scheduled_time: datetime = Field(description="Originally scheduled execution time")


class WatchChangedEvent(EventModel):
    """Event emitted when a watch schedule detects changes."""

    event_type: ClassVar[str] = "@watch"

    execution_time: datetime = Field(description="When this execution occurred")
    execution_count: int = Field(description="Number of times this task has executed")
    query: str = Field(description="The query that was executed")
    check_interval: float = Field(description="Interval between checks in seconds")
    detect_changes: bool = Field(description="Whether change detection is enabled")
    has_changes: bool = Field(description="Whether changes were detected this execution")
    current_result_count: int = Field(description="Number of results in current execution")
    previous_result_count: int | None = Field(description="Number of results in previous execution")
