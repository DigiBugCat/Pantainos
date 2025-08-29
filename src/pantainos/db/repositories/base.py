"""
Base repository class providing common functionality for all repositories
"""

import logging
from dataclasses import asdict, fields
from typing import Any, TypeVar

from pantainos.db.database import Database

logger = logging.getLogger(__name__)

T = TypeVar("T")


class BaseRepository:
    """Base repository providing common database operations"""

    def __init__(self, db: Database) -> None:
        self.db = db
        self.logger = logging.getLogger(self.__class__.__name__)

    async def _row_to_model(self, row: Any, model_class: type[T]) -> T | None:
        """
        Convert database row to dataclass instance

        Args:
            row: Database row (from fetchone/fetchall)
            model_class: Target dataclass type

        Returns:
            Instance of model_class populated with row data
        """
        if row is None:
            return None

        # Convert row to dict - handle both aiosqlite.Row and dict
        if hasattr(row, "keys"):
            # SQLite Row object with keys() method
            row_dict = dict(row)
        elif isinstance(row, tuple | list):
            # Tuple or list - shouldn't happen with our repository pattern
            raise ValueError(f"Cannot convert tuple/list to model without column names: {row}")
        else:
            # Assume it's already a dict-like object
            row_dict = row

        # Get field names from dataclass
        field_names = {field.name for field in fields(model_class)}  # type: ignore[arg-type]

        # Filter row data to only include fields that exist in the dataclass
        filtered_data = {k: v for k, v in row_dict.items() if k in field_names}

        try:
            return model_class(**filtered_data)
        except Exception as e:
            self.logger.error(f"Failed to convert row to {model_class.__name__}: {e}")
            self.logger.error(f"Row data: {row_dict}")
            self.logger.error(f"Filtered data: {filtered_data}")
            raise

    def _model_to_dict(self, model: Any, exclude: set[str] | None = None) -> dict[str, Any]:
        """
        Convert dataclass to dict for database operations

        Args:
            model: Dataclass instance
            exclude: Set of field names to exclude

        Returns:
            Dictionary representation suitable for database operations
        """
        exclude = exclude or set()
        data = asdict(model)

        # Remove excluded fields
        for field_name in exclude:
            data.pop(field_name, None)

        # Remove None values from data dictionary
        return {k: v for k, v in data.items() if v is not None}

    async def _insert_model(self, table: str, model: Any, exclude: set[str] | None = None) -> int:
        """
        Insert a model into the database

        Args:
            table: Table name
            model: Dataclass instance
            exclude: Fields to exclude (typically 'id' for auto-increment)

        Returns:
            Last inserted row ID
        """
        data = self._model_to_dict(model, exclude)

        if not data:
            raise ValueError("No data to insert")

        fields_list = list(data.keys())
        placeholders = ["?" for _ in fields_list]
        values = [data[field] for field in fields_list]

        query = f"""
            INSERT INTO {table} ({", ".join(fields_list)})
            VALUES ({", ".join(placeholders)})
        """  # noqa: S608

        cursor = await self.db.execute(query, tuple(values))
        await self.db.commit()

        if cursor.lastrowid is None:
            raise RuntimeError("Failed to get lastrowid after insert")

        self.logger.debug(f"Inserted into {table}, new ID: {cursor.lastrowid}")
        return cursor.lastrowid

    async def _update_model(self, table: str, model: Any, where_field: str, exclude: set[str] | None = None) -> bool:
        """
        Update a model in the database

        Args:
            table: Table name
            model: Dataclass instance
            where_field: Field name for WHERE clause (e.g., 'id')
            exclude: Fields to exclude from update

        Returns:
            True if a row was updated, False otherwise
        """
        data = self._model_to_dict(model, exclude)
        where_value = getattr(model, where_field)

        if not data:
            raise ValueError("No data to update")

        if where_value is None:
            raise ValueError(f"WHERE field '{where_field}' cannot be None")

        # Remove where_field from update data
        data.pop(where_field, None)

        if not data:
            self.logger.debug(f"No fields to update for {table} where {where_field}={where_value}")
            return False

        set_clauses = [f"{field} = ?" for field in data]
        values = [*data.values(), where_value]

        query = f"""
            UPDATE {table}
            SET {", ".join(set_clauses)}
            WHERE {where_field} = ?
        """  # noqa: S608

        cursor = await self.db.execute(query, tuple(values))
        await self.db.commit()

        updated = cursor.rowcount > 0
        self.logger.debug(f"Updated {table} where {where_field}={where_value}: {updated}")
        return updated

    async def _delete_by_field(self, table: str, field: str, value: Any) -> bool:
        """
        Delete record(s) by field value

        Args:
            table: Table name
            field: Field name for WHERE clause
            value: Value to match

        Returns:
            True if any rows were deleted, False otherwise
        """
        query = f"DELETE FROM {table} WHERE {field} = ?"  # noqa: S608
        cursor = await self.db.execute(query, (value,))
        await self.db.commit()

        deleted = cursor.rowcount > 0
        self.logger.debug(f"Deleted from {table} where {field}={value}: {deleted}")
        return deleted

    async def _count_by_field(self, table: str, field: str, value: Any) -> int:
        """
        Count records by field value

        Args:
            table: Table name
            field: Field name for WHERE clause
            value: Value to match

        Returns:
            Number of matching records
        """
        query = f"SELECT COUNT(*) FROM {table} WHERE {field} = ?"  # noqa: S608
        row = await self.db.fetchone(query, (value,))
        return row[0] if row else 0
