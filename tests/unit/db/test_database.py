"""
Tests for database functionality
"""

import tempfile
from pathlib import Path

import pytest

from pantainos.db.database import Database, get_database, init_database


class TestDatabase:
    """Test Database functionality"""

    @pytest.fixture
    async def temp_db(self):
        """Create a temporary database for testing"""
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "test.db"
            db = Database(db_path)
            yield db
            await db.close()

    async def test_database_initialization(self, temp_db):
        """Test database initialization creates file and tables"""
        db = temp_db

        # Database should not be initialized yet
        assert not db._initialized

        # Initialize should create the file and tables
        await db.initialize()

        assert db._initialized
        assert db.db_path.exists()
        assert db.connection is not None

    async def test_connection_management(self, temp_db):
        """Test connection opening and closing"""
        db = temp_db

        # Initialize to open connection
        await db.initialize()
        assert db.connection is not None

        # Close connection
        await db.close()
        assert db.connection is None
        assert not db._initialized

    async def test_execute_methods(self, temp_db):
        """Test query execution methods"""
        db = temp_db
        await db.initialize()

        # Test execute
        cursor = await db.execute("SELECT 1 as test_value")
        assert cursor is not None

        # Test fetchone
        result = await db.fetchone("SELECT 1 as test_value")
        assert result is not None
        assert result[0] == 1

        # Test fetchall
        results = await db.fetchall("SELECT 1 as test_value UNION SELECT 2")
        assert len(results) == 2

        # Test fetchval
        value = await db.fetchval("SELECT 42")
        assert value == 42

    async def test_get_stats(self, temp_db):
        """Test statistics collection"""
        db = temp_db
        await db.initialize()

        stats = await db.get_stats()

        # Should have counts for all expected tables
        expected_tables = [
            "users",
            "user_identities",
            "events",
            "chat_messages",
            "commands",
            "persistent_variables",
            "session_variables",
        ]

        for table in expected_tables:
            assert f"{table}_count" in stats
            assert isinstance(stats[f"{table}_count"], int)

        # Should have file and database info
        assert "file_size_bytes" in stats
        assert "total_pages" in stats
        assert "page_size" in stats

    async def test_vacuum_operation(self, temp_db):
        """Test vacuum operation executes without error"""
        db = temp_db
        await db.initialize()

        # Should not raise an exception
        await db.vacuum()

    async def test_backup_functionality(self, temp_db):
        """Test database backup creation"""
        db = temp_db
        await db.initialize()

        with tempfile.TemporaryDirectory() as backup_dir:
            backup_path = Path(backup_dir) / "backup.db"

            # Should not raise an exception
            await db.backup(backup_path)

            # Backup file should exist
            assert backup_path.exists()
            assert backup_path.stat().st_size > 0

    async def test_async_context_manager(self):
        """Test async context manager behavior"""
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "context_test.db"

            async with Database(db_path) as db:
                assert db._initialized
                assert db.connection is not None

            # Connection should be closed after context
            assert db.connection is None
            assert not db._initialized

    def test_sync_context_manager(self):
        """Test sync context manager behavior"""
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "sync_context_test.db"

            # Should not raise an exception
            with Database(db_path) as db:
                assert isinstance(db, Database)

    def test_global_database_functions_exist(self):
        """Test that global database functions work"""
        # Test get_database returns a Database instance
        db1 = get_database()
        assert isinstance(db1, Database)

        # Test get_database returns the same instance (singleton behavior)
        db2 = get_database()
        assert db1 is db2

    async def test_init_database_function(self):
        """Test global database initialization function"""
        with tempfile.TemporaryDirectory() as temp_dir:
            custom_path = Path(temp_dir) / "init_test.db"

            # Reset global state for test
            import pantainos.db.database

            pantainos.db.database._database = None

            db = await init_database(custom_path)
            assert isinstance(db, Database)
            assert db._initialized
            assert db.db_path == custom_path

            await db.close()

    async def test_transaction_handling(self, temp_db):
        """Test commit and rollback functionality"""
        db = temp_db
        await db.initialize()

        # Test commit - should not raise exception
        await db.commit()

        # Test rollback - should not raise exception
        await db.rollback()

    async def test_error_handling_closed_connection(self):
        """Test behavior with closed/missing connection"""
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "error_test.db"
            db = Database(db_path)

            # Should auto-initialize when needed
            result = await db.fetchval("SELECT 1")
            assert result == 1

            await db.close()
