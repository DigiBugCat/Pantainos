"""
Tests for LifecycleManager
"""

from unittest.mock import AsyncMock, MagicMock

import pytest

from pantainos.core.lifecycle import LifecycleManager


@pytest.fixture
def mock_components():
    """Create mocked components for testing."""
    return {
        "container": MagicMock(),
        "event_bus": AsyncMock(),
        "schedule_manager": AsyncMock(),
        "plugin_registry": AsyncMock(),
        "db_initializer": AsyncMock(),
    }


@pytest.fixture
def lifecycle_manager(mock_components):
    """Create LifecycleManager with mocked dependencies."""
    return LifecycleManager(
        container=mock_components["container"],
        event_bus=mock_components["event_bus"],
        schedule_manager=mock_components["schedule_manager"],
        plugin_registry=mock_components["plugin_registry"],
        db_initializer=mock_components["db_initializer"],
    )


@pytest.mark.asyncio
async def test_start_with_database(lifecycle_manager, mock_components):
    """Test application start with database initialization."""
    database_url = "sqlite:///test.db"
    master_key = "test_key"

    await lifecycle_manager.start(
        database_url=database_url,
        master_key=master_key,
        emit_startup_event=True,
    )

    # Verify startup sequence
    mock_components["db_initializer"].initialize.assert_called_once_with(database_url, master_key)
    mock_components["event_bus"].start.assert_called_once()
    mock_components["schedule_manager"].start.assert_called_once()
    mock_components["plugin_registry"].start_all.assert_called_once()
    mock_components["event_bus"].emit.assert_called_once()


@pytest.mark.asyncio
async def test_start_without_database(lifecycle_manager, mock_components):
    """Test application start without database initialization."""
    await lifecycle_manager.start(
        database_url=":memory:",
        emit_startup_event=False,
    )

    # Database should not be initialized for memory URLs
    mock_components["db_initializer"].initialize.assert_not_called()
    mock_components["event_bus"].start.assert_called_once()
    mock_components["schedule_manager"].start.assert_called_once()
    mock_components["plugin_registry"].start_all.assert_called_once()
    # No startup event emitted
    mock_components["event_bus"].emit.assert_not_called()


@pytest.mark.asyncio
async def test_stop(lifecycle_manager, mock_components):
    """Test application stop sequence."""
    await lifecycle_manager.stop()

    # Verify shutdown sequence
    mock_components["schedule_manager"].stop.assert_called_once()
    mock_components["event_bus"].stop.assert_called_once()
    mock_components["plugin_registry"].stop_all.assert_called_once()
    mock_components["db_initializer"].close.assert_called_once()
