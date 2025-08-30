"""
Scheduled task models for type-safe task management in the scheduler.

This module provides strongly-typed models for scheduled tasks,
replacing the previous dict[str, Any] approach.
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Any, Literal

from pydantic import BaseModel, Field

from .schedules import Cron, Interval, Schedule, Watch


class ScheduledTask(BaseModel):
    """Base model for all scheduled tasks."""

    handler: Callable[..., Awaitable[Any]] = Field(description="The async handler function to execute")
    schedule: Schedule = Field(description="The schedule configuration")
    execution_count: int = Field(default=0, description="Number of times this task has executed")

    class Config:
        arbitrary_types_allowed = True


class IntervalTask(ScheduledTask):
    """Task that runs on a fixed interval."""

    schedule: Interval = Field(description="Interval schedule configuration")
    type: Literal["interval"] = Field(default="interval", description="Task type identifier")
    last_execution: float = Field(default=0.0, description="Timestamp of last execution")


class CronTask(ScheduledTask):
    """Task that runs on a cron schedule."""

    schedule: Cron = Field(description="Cron schedule configuration")
    type: Literal["cron"] = Field(default="cron", description="Task type identifier")
    next_execution: float = Field(description="Timestamp of next scheduled execution")


class WatchTask(ScheduledTask):
    """Task that watches for changes in query results."""

    schedule: Watch = Field(description="Watch schedule configuration")
    type: Literal["watch"] = Field(default="watch", description="Task type identifier")
    last_check: float = Field(default=0.0, description="Timestamp of last check")
    previous_results: list[dict[str, Any]] = Field(
        default_factory=list, description="Previous query results for comparison"
    )
    current_results: list[dict[str, Any]] | None = Field(default=None, description="Current query results")
    has_changes: bool = Field(default=False, description="Whether changes were detected")
