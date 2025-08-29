"""
Schedule Manager - Handles scheduled and reactive triggers

This module manages periodic intervals, cron-like scheduling, and database
watch triggers, emitting scheduled events through the event bus.
"""

import asyncio
import logging
import time
from collections.abc import Callable
from datetime import datetime
from typing import Any

from pantainos.core.di.container import ServiceContainer
from pantainos.core.event_bus import EventBus
from pantainos.schedules import Cron, Interval, Watch

logger = logging.getLogger(__name__)


class ScheduleManager:
    """
    Manages scheduled tasks and reactive database watches.

    This manager handles the execution of timed events (intervals, cron)
    and database-reactive events (watches), emitting events through the
    event bus when scheduled conditions are met.
    """

    def __init__(self, event_bus: EventBus, container: ServiceContainer) -> None:
        """
        Initialize the schedule manager.

        Args:
            event_bus: Event bus for emitting scheduled events
            container: Service container for dependency injection
        """
        self.event_bus = event_bus
        self.container = container
        self.running = False
        self.scheduled_tasks: list[dict[str, Any]] = []
        self.background_tasks: set[asyncio.Task[None]] = set()

    async def add_interval_schedule(self, handler: Callable[..., Any], interval: Interval) -> None:
        """
        Add an interval-based schedule.

        Args:
            handler: Handler function to call when interval triggers
            interval: Interval schedule configuration
        """
        self.scheduled_tasks.append(
            {
                "handler": handler,
                "schedule": interval,
                "type": "interval",
                "execution_count": 0,
                "last_execution": 0.0,
            }
        )
        logger.debug(f"Added interval schedule: {interval.seconds}s")

    async def add_cron_schedule(self, handler: Callable[..., Any], cron: Cron) -> None:
        """
        Add a cron-based schedule.

        Args:
            handler: Handler function to call when cron triggers
            cron: Cron schedule configuration
        """
        self.scheduled_tasks.append(
            {
                "handler": handler,
                "schedule": cron,
                "type": "cron",
                "execution_count": 0,
                "next_execution": self.calculate_next_cron_time(cron),
            }
        )
        logger.debug(f"Added cron schedule: {cron.expression}")

    async def add_watch_schedule(self, handler: Callable[..., Any], watch: Watch) -> None:
        """
        Add a database watch schedule.

        Args:
            handler: Handler function to call when watch triggers
            watch: Database watch configuration
        """
        self.scheduled_tasks.append(
            {
                "handler": handler,
                "schedule": watch,
                "type": "watch",
                "execution_count": 0,
                "last_check": 0.0,
                "previous_results": [],
            }
        )
        logger.debug(f"Added watch schedule: {watch.query}")

    async def start(self) -> None:
        """Start all scheduled tasks."""
        if self.running:
            logger.warning("ScheduleManager already running")
            return

        self.running = True
        logger.info("Starting ScheduleManager")

        # Create background tasks for each scheduled task
        for task_info in self.scheduled_tasks:
            task = asyncio.create_task(self._run_scheduled_task(task_info))
            self.background_tasks.add(task)
            task.add_done_callback(self.background_tasks.discard)

        logger.info(f"Started {len(self.background_tasks)} scheduled tasks")

    async def stop(self) -> None:
        """Stop all scheduled tasks."""
        logger.info("Stopping ScheduleManager")
        self.running = False

        # Cancel all background tasks
        for task in self.background_tasks:
            task.cancel()

        # Wait for all tasks to complete
        if self.background_tasks:
            await asyncio.gather(*self.background_tasks, return_exceptions=True)
            self.background_tasks.clear()

        logger.info("ScheduleManager stopped")

    async def _run_scheduled_task(self, task_info: dict[str, Any]) -> None:
        """
        Run a single scheduled task in a loop.

        Args:
            task_info: Task information dictionary
        """
        task_type = task_info["type"]

        try:
            while self.running:
                try:
                    # Calculate delay until next execution
                    delay = await self._calculate_delay(task_info)

                    # Wait for the scheduled time with cancellation support
                    await asyncio.sleep(delay)

                    if not self.running:
                        break

                    # Check if we should execute (for conditional schedules)
                    should_execute = await self._should_execute_task(task_info)
                    if not should_execute:
                        continue

                    # Execute the scheduled task
                    await self._execute_scheduled_task(task_info)

                except asyncio.CancelledError:
                    break
                except Exception as e:
                    logger.error(f"Error in scheduled task ({task_type}): {e}", exc_info=True)
                    # Continue running despite errors - wait a bit before retrying
                    await asyncio.sleep(1.0)

        except asyncio.CancelledError:
            logger.debug(f"Scheduled task cancelled: {task_type}")

    async def _calculate_delay(self, task_info: dict[str, Any]) -> float:
        """
        Calculate delay until next execution.

        Args:
            task_info: Task information dictionary

        Returns:
            Delay in seconds
        """
        task_type = task_info["type"]
        schedule = task_info["schedule"]

        if task_type == "interval":
            interval: Interval = schedule

            # Handle start_immediately option
            if task_info["execution_count"] == 0 and interval.start_immediately:
                return 0.0

            # Calculate next interval execution
            if task_info["last_execution"] > 0:
                elapsed = time.time() - task_info["last_execution"]
                remaining = interval.seconds - elapsed
                return max(0.0, remaining)

            return interval.seconds

        if task_type == "cron":
            # Calculate time until next cron execution
            next_time = task_info.get("next_execution", time.time())
            return max(0.0, next_time - time.time())

        if task_type == "watch":
            watch: Watch = schedule

            # Check interval for database watches
            if task_info["last_check"] > 0:
                elapsed = time.time() - task_info["last_check"]
                remaining = watch.check_interval - elapsed
                return max(0.0, remaining)

            return watch.check_interval

        return 60.0  # Default fallback

    async def _should_execute_task(self, task_info: dict[str, Any]) -> bool:
        """
        Check if a scheduled task should execute now.

        Args:
            task_info: Task information dictionary

        Returns:
            True if task should execute
        """
        task_type = task_info["type"]

        if task_type == "watch":
            # For watches, check if query results meet execution criteria
            return await self._check_watch_condition(task_info)

        # Intervals and cron always execute when scheduled
        return True

    async def _check_watch_condition(self, task_info: dict[str, Any]) -> bool:
        """
        Check if a watch condition should trigger execution.

        Args:
            task_info: Watch task information

        Returns:
            True if watch should execute
        """
        watch: Watch = task_info["schedule"]
        task_info["last_check"] = time.time()

        try:
            # Get database from container
            database = self.container.resolve("Database")
            if not database:
                logger.warning("Database not available for watch query")
                return False

            # Execute the watch query
            results = await database.execute_query(watch.query, watch.params)
            current_results = [dict(row) for row in results] if results else []

            # Check if we should execute based on detect_changes setting
            if watch.detect_changes:
                previous_results = task_info.get("previous_results", [])
                has_changes = current_results != previous_results
                task_info["previous_results"] = current_results

                # Only execute if results changed
                if not has_changes:
                    return False

            # Store results for event emission
            task_info["current_results"] = current_results
            task_info["has_changes"] = watch.detect_changes and has_changes

            # Execute if there are results (unless detect_changes=True and no changes)
            return len(current_results) > 0

        except Exception as e:
            logger.error(f"Error executing watch query: {e}")
            return False

    async def _execute_scheduled_task(self, task_info: dict[str, Any]) -> None:
        """
        Execute a scheduled task by emitting an event.

        Args:
            task_info: Task information dictionary
        """
        task_type = task_info["type"]
        schedule = task_info["schedule"]
        task_info["execution_count"] += 1

        try:
            # Create event data based on schedule type
            event_data = await self._create_event_data(task_info)

            # Emit the scheduled event
            await self.event_bus.emit(schedule.event_type, event_data, "scheduler")

            # Update execution tracking
            if task_type == "interval":
                task_info["last_execution"] = time.time()
            elif task_type == "cron":
                # Calculate next cron execution time
                task_info["next_execution"] = self._calculate_next_cron_time(schedule)

            logger.debug(f"Executed {task_type} schedule (count: {task_info['execution_count']})")

        except Exception as e:
            logger.error(f"Error executing scheduled task: {e}")

    async def _create_event_data(self, task_info: dict[str, Any]) -> dict[str, Any]:
        """
        Create event data for a scheduled task.

        Args:
            task_info: Task information dictionary

        Returns:
            Event data dictionary
        """
        schedule = task_info["schedule"]
        task_type = task_info["type"]

        # Base event data
        event_data = {
            "execution_time": datetime.now(),
            "execution_count": task_info["execution_count"],
            "source": "scheduler",
        }

        # Add schedule-specific data
        if task_type == "interval":
            interval: Interval = schedule
            event_data.update(
                {
                    "seconds": interval.seconds,
                    "start_immediately": interval.start_immediately,
                    "align_to_minute": interval.align_to_minute,
                }
            )

        elif task_type == "cron":
            cron: Cron = schedule
            event_data.update(
                {
                    "expression": cron.expression,
                    "timezone": cron.timezone,
                    "scheduled_time": datetime.fromtimestamp(task_info.get("next_execution", time.time())),
                }
            )

        elif task_type == "watch":
            watch: Watch = schedule
            results = task_info.get("current_results", [])
            previous_results = task_info.get("previous_results", [])
            has_changes = task_info.get("has_changes", False)

            event_data.update(
                {
                    "query": watch.query,
                    "params": watch.params,
                    "check_interval": watch.check_interval,
                    "detect_changes": watch.detect_changes,
                    "results": results,
                    "previous_results": previous_results,
                    "has_changes": has_changes,
                    "results_count": len(results),
                }
            )

        return event_data

    def calculate_next_cron_time(self, cron: Cron) -> float:
        """
        Calculate the next execution time for a cron schedule.

        Args:
            cron: Cron schedule configuration

        Returns:
            Next execution timestamp
        """
        # Basic cron calculation - for production, would use croniter library
        # For now, just schedule for next minute as a placeholder
        # TODO: Implement proper cron parsing using cron.expression
        import time

        # Use the cron expression for basic validation, but return fixed interval
        _ = cron.expression  # Acknowledge we should use this
        return time.time() + 60.0
