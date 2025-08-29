"""
Database connection and management
"""

import logging
import types
from pathlib import Path
from typing import Any

import aiosqlite

from .models import SCHEMA_SQL

logger = logging.getLogger(__name__)


class Database:
    """
    SQLite database manager with async support

    Handles database initialization, connection management, and provides
    a simple interface for database operations.
    """

    def __init__(self, db_path: str | Path = "data/stream.db") -> None:
        self.db_path = Path(db_path)
        self.connection: aiosqlite.Connection | None = None
        self._initialized = False

    async def initialize(self) -> None:
        """
        Initialize database connection and schema

        Creates the database file and tables if they don't exist.
        Optimizes SQLite settings for streaming workload.
        """
        if self._initialized:
            return

        # Ensure data directory exists
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        # Connect to database
        self.connection = await aiosqlite.connect(
            self.db_path,
            isolation_level=None,  # Autocommit mode enabled
        )

        # Set row factory to return Row objects with column names
        self.connection.row_factory = aiosqlite.Row

        # Enable foreign keys
        await self.connection.execute("PRAGMA foreign_keys = ON")

        # Optimize SQLite for streaming workload
        await self.connection.execute("PRAGMA journal_mode = WAL")  # Write-Ahead Logging mode
        await self.connection.execute("PRAGMA synchronous = NORMAL")  # Faster writes
        await self.connection.execute("PRAGMA cache_size = -16000")  # 16MB cache
        await self.connection.execute("PRAGMA temp_store = memory")  # Use memory for temp tables

        # Create schema
        await self.connection.executescript(SCHEMA_SQL)

        # Clear session variables on startup (they don't persist)
        await self.connection.execute("DELETE FROM session_variables")
        await self.connection.commit()

        self._initialized = True
        logger.info(f"Database initialized: {self.db_path}")

    async def close(self) -> None:
        """Close database connection"""
        if self.connection:
            await self.connection.close()
            self.connection = None
            self._initialized = False
            logger.info("Database connection closed")

    async def execute(self, query: str, parameters: tuple[Any, ...] | None = None) -> aiosqlite.Cursor:
        """Execute a query and return cursor"""
        if not self.connection:
            await self.initialize()

        if self.connection is None:
            raise RuntimeError("Database connection could not be established")
        return await self.connection.execute(query, parameters or ())

    async def executemany(self, query: str, parameters: list[tuple[Any, ...]]) -> aiosqlite.Cursor:
        """Execute a query with multiple parameter sets"""
        if not self.connection:
            await self.initialize()

        if self.connection is None:
            raise RuntimeError("Database connection could not be established")
        return await self.connection.executemany(query, parameters)

    async def fetchone(self, query: str, parameters: tuple[Any, ...] | None = None) -> aiosqlite.Row | None:
        """Execute query and fetch one row"""
        cursor = await self.execute(query, parameters)
        return await cursor.fetchone()

    async def fetchall(self, query: str, parameters: tuple[Any, ...] | None = None) -> list[aiosqlite.Row]:
        """Execute query and fetch all rows"""
        cursor = await self.execute(query, parameters)
        rows = await cursor.fetchall()
        return list(rows)

    async def fetchval(self, query: str, parameters: tuple[Any, ...] | None = None) -> Any:
        """Execute query and fetch single value from first row"""
        row = await self.fetchone(query, parameters)
        return row[0] if row else None

    async def commit(self) -> None:
        """Commit current transaction"""
        if self.connection:
            await self.connection.commit()

    async def rollback(self) -> None:
        """Rollback current transaction"""
        if self.connection:
            await self.connection.rollback()

    async def get_stats(self) -> dict[str, Any]:
        """Get database statistics"""
        if not self.connection:
            return {}

        stats = {}

        # Table row counts (safe table names - no SQL injection risk)
        tables = {
            "users": "users",
            "user_identities": "user_identities",
            "events": "events",
            "chat_messages": "chat_messages",
            "commands": "commands",
            "persistent_variables": "persistent_variables",
            "session_variables": "session_variables",
        }
        for table_key, table_name in tables.items():
            # Safe: table_name is from controlled whitelist, not user input
            count = await self.fetchval(f"SELECT COUNT(*) FROM {table_name}")  # noqa: S608
            stats[f"{table_key}_count"] = count

        # Database file size
        try:
            stats["file_size_bytes"] = self.db_path.stat().st_size
        except FileNotFoundError:
            stats["file_size_bytes"] = 0

        # SQLite specific stats
        page_count = await self.fetchval("PRAGMA page_count")
        page_size = await self.fetchval("PRAGMA page_size")
        if page_count and page_size:
            stats["total_pages"] = page_count
            stats["page_size"] = page_size

        return stats

    async def vacuum(self) -> None:
        """Vacuum database to reclaim space and optimize"""
        if self.connection:
            await self.connection.execute("VACUUM")
            logger.info("Database vacuumed")

    async def backup(self, backup_path: str | Path) -> None:
        """Create a backup of the database"""
        backup_path = Path(backup_path)
        backup_path.parent.mkdir(parents=True, exist_ok=True)

        if not self.connection:
            await self.initialize()

        # Use SQLite backup API for safe backup
        backup_conn = await aiosqlite.connect(backup_path)
        try:
            if self.connection is None:
                raise RuntimeError("Database connection could not be established for backup")
            await self.connection.backup(backup_conn)
            logger.info(f"Database backed up to: {backup_path}")
        finally:
            await backup_conn.close()

    def __enter__(self) -> "Database":
        """Context manager support (not async)"""
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: types.TracebackType | None,
    ) -> None:
        """Context manager cleanup (not async)"""
        # Note: This is not async, so we can't properly close the connection
        # Use async context manager instead when possible
        pass

    async def __aenter__(self) -> "Database":
        """Async context manager entry"""
        await self.initialize()
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: types.TracebackType | None,
    ) -> None:
        """Async context manager cleanup"""
        await self.close()


# Global database instance
_database: Database | None = None


def get_database(db_path: str | Path | None = None) -> Database:
    """Get global database instance"""
    global _database
    if _database is None:
        path = db_path or "data/stream.db"
        _database = Database(path)
    return _database


async def init_database(db_path: str | Path | None = None) -> Database:
    """Initialize global database instance"""
    db = get_database(db_path)
    await db.initialize()
    return db
