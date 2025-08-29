"""
Event repository for logging and querying events
"""

import json
import logging
from typing import Any

from pantainos.db.database import Database

logger = logging.getLogger(__name__)


class EventRepository:
    """
    Repository for managing event logging and history

    Provides methods to log events from various sources (Twitch, OBS, etc.)
    and query event history for analytics and debugging.
    """

    def __init__(self, database: Database) -> None:
        self.db = database

    async def log_event(
        self,
        event_type: str,
        data: dict[str, Any],
        user_id: int | None = None,
    ) -> int:
        """
        Log an event to the database

        Args:
            event_type: Type of event (e.g., "twitch.chat.message", "twitch.follow")
            data: Event data dictionary
            user_id: Optional user ID if event is associated with a user

        Returns:
            Event ID of the logged event
        """
        # Convert data to JSON string for storage
        json_data = json.dumps(data) if data else "{}"

        cursor = await self.db.execute(
            "INSERT INTO events (type, user_id, data, created_at) VALUES (?, ?, ?, CURRENT_TIMESTAMP)",
            (event_type, user_id, json_data),
        )
        await self.db.commit()

        event_id = cursor.lastrowid or 0
        logger.debug(f"Logged event {event_type} with ID {event_id}")
        return event_id

    async def get_events(
        self,
        event_type: str | None = None,
        user_id: int | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[dict[str, Any]]:
        """
        Get events with optional filtering

        Args:
            event_type: Optional event type filter
            user_id: Optional user ID filter
            limit: Maximum number of events to return
            offset: Number of events to skip

        Returns:
            List of event dictionaries
        """
        query = "SELECT id, type, user_id, data, created_at FROM events WHERE 1=1"
        params: list[Any] = []

        if event_type:
            query += " AND type = ?"
            params.append(event_type)

        if user_id:
            query += " AND user_id = ?"
            params.append(user_id)

        query += " ORDER BY created_at DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])

        rows = await self.db.fetchall(query, tuple(params))

        events = []
        for row in rows:
            event_data: dict[str, Any] = {}
            try:
                event_data = json.loads(row[3]) if row[3] else {}
            except json.JSONDecodeError:
                logger.warning(f"Failed to parse event data for event ID {row[0]}")

            events.append(
                {
                    "id": row[0],
                    "type": row[1],
                    "user_id": row[2],
                    "data": event_data,
                    "created_at": row[4],
                }
            )

        return events

    async def get_event_by_id(self, event_id: int) -> dict[str, Any] | None:
        """
        Get a specific event by ID

        Args:
            event_id: Event ID to retrieve

        Returns:
            Event dictionary or None if not found
        """
        row = await self.db.fetchone(
            "SELECT id, type, user_id, data, created_at FROM events WHERE id = ?",
            (event_id,),
        )

        if not row:
            return None

        event_data: dict[str, Any] = {}
        try:
            event_data = json.loads(row[3]) if row[3] else {}
        except json.JSONDecodeError:
            logger.warning(f"Failed to parse event data for event ID {event_id}")

        return {
            "id": row[0],
            "type": row[1],
            "user_id": row[2],
            "data": event_data,
            "created_at": row[4],
        }

    async def get_event_types(self) -> list[str]:
        """
        Get all unique event types in the database

        Returns:
            List of event type strings
        """
        rows = await self.db.fetchall("SELECT DISTINCT type FROM events ORDER BY type")
        return [row[0] for row in rows]

    async def count_events(
        self,
        event_type: str | None = None,
        user_id: int | None = None,
    ) -> int:
        """
        Count events with optional filtering

        Args:
            event_type: Optional event type filter
            user_id: Optional user ID filter

        Returns:
            Number of matching events
        """
        query = "SELECT COUNT(*) FROM events WHERE 1=1"
        params: list[Any] = []

        if event_type:
            query += " AND type = ?"
            params.append(event_type)

        if user_id:
            query += " AND user_id = ?"
            params.append(user_id)

        count = await self.db.fetchval(query, tuple(params))
        return count or 0

    async def delete_old_events(self, days_old: int = 30) -> int:
        """
        Delete events older than specified days

        Args:
            days_old: Delete events older than this many days

        Returns:
            Number of events deleted
        """
        cursor = await self.db.execute(
            "DELETE FROM events WHERE created_at < datetime('now', '-' || ? || ' days')",
            (days_old,),
        )
        await self.db.commit()

        deleted_count = cursor.rowcount
        logger.info(f"Deleted {deleted_count} events older than {days_old} days")
        return deleted_count

    async def get_event_stats(self) -> dict[str, Any]:
        """
        Get event statistics

        Returns:
            Dictionary with event statistics
        """
        total_events = await self.db.fetchval("SELECT COUNT(*) FROM events")

        # Get event type breakdown
        type_rows = await self.db.fetchall("SELECT type, COUNT(*) FROM events GROUP BY type ORDER BY COUNT(*) DESC")
        type_breakdown = {row[0]: row[1] for row in type_rows}

        # Get events per day for last 7 days
        daily_rows = await self.db.fetchall(
            """
            SELECT DATE(created_at) as date, COUNT(*) as count
            FROM events
            WHERE created_at >= datetime('now', '-7 days')
            GROUP BY DATE(created_at)
            ORDER BY date DESC
            """
        )
        daily_stats = {row[0]: row[1] for row in daily_rows}

        return {
            "total_events": total_events,
            "event_type_breakdown": type_breakdown,
            "daily_events_last_7_days": daily_stats,
        }
