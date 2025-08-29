"""
Variable repository for managing persistent and session variables

This provides a robust variable system with:
- Persistent variables (survive restarts)
- Session variables (cleared on restart)
- Type-safe storage and retrieval
"""

import json
import logging
from typing import Any, TypeVar

from pantainos.db.database import Database

logger = logging.getLogger(__name__)

T = TypeVar("T")


class VariableRepository:
    """
    Repository for managing application-level variables

    This repository handles general-purpose variables for storing application state,
    game data, counters, and other runtime information. It provides both persistent
    variables (survive restarts) and session variables (cleared on startup).

    NOT for authentication tokens - use AuthRepository instead.

    Variable Types:
    - Persistent: Stored permanently (e.g., total followers, game high scores)
    - Session: Temporary, cleared on restart (e.g., current game state, temp counters)

    Supported Data Types:
    - strings: Simple text values
    - numbers: Integers or floats
    - booleans: True/False values
    - JSON: Complex objects/arrays

    Usage:
        var_repo = VariableRepository(database)
        await var_repo.set("high_score", 1000, persistent=True)
        score = await var_repo.get("high_score", default=0)
    """

    def __init__(self, database: Database) -> None:
        self.db = database

    async def get(
        self,
        name: str,
        default: T | None = None,
        persistent: bool = True,
    ) -> T | Any | None:
        """
        Get a variable value

        Args:
            name: Variable name
            default: Default value if variable doesn't exist
            persistent: True for persistent variables, False for session variables

        Returns:
            Variable value converted to proper type, or default if not found
        """
        table = "persistent_variables" if persistent else "session_variables"

        row = await self.db.fetchone(
            f"SELECT value, data_type FROM {table} WHERE name = ?",  # noqa: S608
            (name,),
        )

        if row is None:
            return default

        value, data_type = row
        return self.convert_value(value, data_type)

    async def set(
        self,
        name: str,
        value: Any,
        persistent: bool = True,
        description: str = "",
    ) -> None:
        """
        Set a variable value

        Args:
            name: Variable name
            value: Value to store (will be converted to appropriate string representation)
            persistent: True for persistent variables, False for session variables
            description: Optional description for persistent variables
        """
        # Convert value to storage format
        if isinstance(value, bool):
            str_value = str(value).lower()
            data_type = "boolean"
        elif isinstance(value, int | float):
            str_value = str(value)
            data_type = "number"
        elif isinstance(value, dict | list):
            str_value = json.dumps(value)
            data_type = "json"
        else:
            str_value = str(value)
            data_type = "string"

        if persistent:
            # Upsert persistent variable
            await self.db.execute(
                """
                INSERT INTO persistent_variables (name, value, data_type, description, created_at, updated_at)
                VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                ON CONFLICT(name) DO UPDATE SET
                    value = excluded.value,
                    data_type = excluded.data_type,
                    description = excluded.description,
                    updated_at = CURRENT_TIMESTAMP
                """,
                (name, str_value, data_type, description),
            )
        else:
            # Upsert session variable
            await self.db.execute(
                """
                INSERT INTO session_variables (name, value, data_type, created_at)
                VALUES (?, ?, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(name) DO UPDATE SET
                    value = excluded.value,
                    data_type = excluded.data_type,
                    created_at = CURRENT_TIMESTAMP
                """,
                (name, str_value, data_type),
            )

        await self.db.commit()
        logger.debug(f"Set {'persistent' if persistent else 'session'} variable '{name}' = {value}")

    async def delete(self, name: str, persistent: bool = True) -> bool:
        """
        Delete a variable

        Args:
            name: Variable name
            persistent: True for persistent variables, False for session variables

        Returns:
            True if variable was deleted, False if it didn't exist
        """
        table = "persistent_variables" if persistent else "session_variables"

        cursor = await self.db.execute(
            f"DELETE FROM {table} WHERE name = ?",  # noqa: S608
            (name,),
        )
        await self.db.commit()

        deleted = cursor.rowcount > 0
        if deleted:
            logger.debug(f"Deleted {'persistent' if persistent else 'session'} variable '{name}'")
        return deleted

    async def exists(self, name: str, persistent: bool = True) -> bool:
        """
        Check if a variable exists

        Args:
            name: Variable name
            persistent: True for persistent variables, False for session variables

        Returns:
            True if variable exists
        """
        table = "persistent_variables" if persistent else "session_variables"

        count = await self.db.fetchval(
            f"SELECT COUNT(*) FROM {table} WHERE name = ?",  # noqa: S608
            (name,),
        )
        return bool(count > 0)

    async def list_variables(self, persistent: bool = True) -> list[dict[str, Any]]:
        """
        List all variables

        Args:
            persistent: True for persistent variables, False for session variables

        Returns:
            List of variable info dictionaries
        """
        if persistent:
            rows = await self.db.fetchall(
                "SELECT name, value, data_type, description, created_at, updated_at FROM persistent_variables"
            )
            return [
                {
                    "name": row[0],
                    "value": self.convert_value(row[1], row[2]),
                    "data_type": row[2],
                    "description": row[3],
                    "created_at": row[4],
                    "updated_at": row[5],
                }
                for row in rows
            ]
        rows = await self.db.fetchall("SELECT name, value, data_type, created_at FROM session_variables")
        return [
            {
                "name": row[0],
                "value": self.convert_value(row[1], row[2]),
                "data_type": row[2],
                "created_at": row[3],
            }
            for row in rows
        ]

    async def clear_session_variables(self) -> int:
        """
        Clear all session variables

        Returns:
            Number of variables cleared
        """
        cursor = await self.db.execute("DELETE FROM session_variables")
        await self.db.commit()
        count = cursor.rowcount
        logger.info(f"Cleared {count} session variables")
        return count

    async def increment(
        self,
        name: str,
        amount: float = 1,
        default: float = 0,
        persistent: bool = True,
    ) -> int | float:
        """
        Increment a numeric variable

        Args:
            name: Variable name
            amount: Amount to increment by
            default: Default value if variable doesn't exist
            persistent: True for persistent variables, False for session variables

        Returns:
            New value after increment

        Raises:
            ValueError: If variable exists but is not numeric
        """
        current = await self.get(name, default, persistent)

        if not isinstance(current, int | float):
            msg = f"Cannot increment non-numeric variable '{name}' (current type: {type(current)})"
            raise ValueError(msg)

        new_value = current + amount
        await self.set(name, new_value, persistent)
        return new_value

    async def append_to_list(
        self,
        name: str,
        item: Any,
        max_length: int | None = None,
        persistent: bool = True,
    ) -> list[Any]:
        """
        Append an item to a list variable

        Args:
            name: Variable name
            item: Item to append
            max_length: Maximum list length (oldest items removed if exceeded)
            persistent: True for persistent variables, False for session variables

        Returns:
            Updated list
        """
        current: Any = await self.get(name, [], persistent)

        if not isinstance(current, list):
            msg = f"Cannot append to non-list variable '{name}' (current type: {type(current)})"
            raise ValueError(msg)

        current.append(item)

        # Trim list if max_length specified
        if max_length is not None and len(current) > max_length:
            current = current[-max_length:]

        await self.set(name, current, persistent)
        return list(current)

    def convert_value(self, value: str, data_type: str) -> Any:
        """Convert stored string value to proper Python type"""
        if data_type == "number":
            try:
                return float(value) if "." in value else int(value)
            except ValueError:
                return 0
        elif data_type == "boolean":
            return value.lower() in ("true", "1", "yes", "on")
        elif data_type == "json":
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                return {}
        else:
            return value

    async def get_stats(self) -> dict[str, Any]:
        """Get variable usage statistics"""
        persistent_count = await self.db.fetchval("SELECT COUNT(*) FROM persistent_variables")
        session_count = await self.db.fetchval("SELECT COUNT(*) FROM session_variables")

        # Get data type breakdown for persistent variables
        type_breakdown = {}
        rows = await self.db.fetchall("SELECT data_type, COUNT(*) FROM persistent_variables GROUP BY data_type")
        for row in rows:
            type_breakdown[row[0]] = row[1]

        return {
            "persistent_variables": persistent_count,
            "session_variables": session_count,
            "total_variables": persistent_count + session_count,
            "persistent_type_breakdown": type_breakdown,
        }
