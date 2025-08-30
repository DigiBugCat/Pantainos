"""
Tests for DatabaseInitializer
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from pantainos.db.initializer import DatabaseInitializer


@pytest.fixture
def mock_container():
    """Create mock service container."""
    return MagicMock()


@pytest.fixture
def db_initializer(mock_container):
    """Create DatabaseInitializer with mock container."""
    return DatabaseInitializer(mock_container)


@pytest.mark.asyncio
async def test_initialize_success(db_initializer, mock_container):
    """Test successful database initialization."""
    mock_database = MagicMock()
    mock_database.initialize = AsyncMock()

    with (
        patch("pantainos.db.database.Database") as mock_db_class,
        patch("pantainos.db.repositories.secure_storage_repository.SecureStorageRepository") as mock_secure_repo,
        patch("pantainos.db.repositories.auth_repository.AuthRepository") as mock_auth_repo,
        patch("pantainos.db.repositories.event_repository.EventRepository") as mock_event_repo,
        patch("pantainos.db.repositories.user_repository.UserRepository") as mock_user_repo,
        patch("pantainos.db.repositories.variable_repository.VariableRepository") as mock_var_repo,
    ):
        # Setup database mock
        mock_db_class.return_value = mock_database

        result = await db_initializer.initialize("sqlite:///test.db", "test_key")

        assert result == mock_database
        assert db_initializer.database == mock_database
        mock_database.initialize.assert_called_once()
        mock_container.register_singleton.assert_called()
        mock_container.register_factory.assert_called()


@pytest.mark.asyncio
async def test_initialize_import_error(db_initializer):
    """Test handling of import errors."""
    # Mock the specific Database import to raise ImportError
    with patch("pantainos.db.database.Database", side_effect=ImportError("No database module")):
        with pytest.raises(ImportError):
            await db_initializer.initialize("sqlite:///test.db")


@pytest.mark.asyncio
async def test_close(db_initializer):
    """Test closing database connection."""
    mock_database = AsyncMock()
    db_initializer.database = mock_database

    await db_initializer.close()

    mock_database.close.assert_called_once()


@pytest.mark.asyncio
async def test_close_no_database(db_initializer):
    """Test closing when no database exists."""
    db_initializer.database = None

    # Should not raise an exception
    await db_initializer.close()


@pytest.mark.asyncio
async def test_close_database_without_close_method(db_initializer):
    """Test closing database that doesn't have close method."""
    mock_database = MagicMock()
    # Remove close method
    del mock_database.close
    db_initializer.database = mock_database

    # Should not raise an exception
    await db_initializer.close()
