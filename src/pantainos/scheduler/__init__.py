"""
Scheduler module for Pantainos.

This module provides task scheduling capabilities with type-safe models
and strongly-typed event emissions.
"""

from .events import CronTriggeredEvent, IntervalExecutedEvent, WatchChangedEvent
from .scheduler import ScheduleManager
from .schedules import Cron, Interval, Schedule, Watch
from .tasks import CronTask, IntervalTask, ScheduledTask, WatchTask

__all__ = [
    "Cron",
    "CronTask",
    "CronTriggeredEvent",
    "Interval",
    "IntervalExecutedEvent",
    "IntervalTask",
    "Schedule",
    "ScheduleManager",
    "ScheduledTask",
    "Watch",
    "WatchChangedEvent",
    "WatchTask",
]
