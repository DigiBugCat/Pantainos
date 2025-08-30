"""
Tests for the modern dashboard hub interface
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# Mock NiceGUI and psutil before import
mock_psutil_module = MagicMock()
mock_psutil_module.cpu_percent = MagicMock(return_value=0)
mock_psutil_module.virtual_memory = MagicMock(return_value=MagicMock(percent=0))

with patch.dict("sys.modules", {"nicegui": MagicMock(), "nicegui.events": MagicMock(), "psutil": mock_psutil_module}):
    from pantainos.web.dashboard import DashboardHub


@pytest.fixture
def mock_app():
    """Mock Pantainos application"""
    app = MagicMock()
    app.event_bus = MagicMock()
    app.event_bus.handlers = {"test.event": [{"name": "handler1"}], "hello": [{"name": "handler2"}]}
    app.event_bus.emit = AsyncMock()
    app.plugins = {"plugin1": MagicMock(), "plugin2": MagicMock()}
    return app


@pytest.fixture
def dashboard_hub(mock_app):
    """Create a dashboard hub instance"""
    return DashboardHub(mock_app)


def test_dashboard_can_be_created(dashboard_hub):
    """Test that DashboardHub can be instantiated"""
    assert dashboard_hub is not None
    assert dashboard_hub.app is not None
    assert dashboard_hub.total_events == 0
    assert dashboard_hub.events_per_second == 0


def test_dashboard_tracks_events(dashboard_hub):
    """Test that dashboard tracks events when they're added"""
    # Add an event to history
    dashboard_hub.event_history.append(
        {"type": "test.event", "data": {"key": "value"}, "source": "test", "timestamp": "2024-01-01T10:00:00"}
    )

    assert len(dashboard_hub.event_history) == 1
    tracked_event = dashboard_hub.event_history[0]
    assert tracked_event["type"] == "test.event"
    assert tracked_event["data"] == {"key": "value"}
    assert tracked_event["source"] == "test"


def test_dashboard_limits_event_history(dashboard_hub):
    """Test that event history is limited to prevent memory issues"""
    # Add more than the max limit (100)
    for i in range(150):
        dashboard_hub.event_history.append(
            {"type": f"test.event.{i}", "data": {}, "source": "test", "timestamp": "2024-01-01T10:00:00"}
        )

    # Should be limited to 100 (deque maxlen)
    assert len(dashboard_hub.event_history) == 100
    # Should have the most recent events (50-149)
    assert dashboard_hub.event_history[-1]["type"] == "test.event.149"


def test_dashboard_initialization_metrics(dashboard_hub, mock_app):
    """Test dashboard initializes with correct metrics"""
    assert dashboard_hub.total_events == 0
    assert dashboard_hub.events_per_second == 0
    assert dashboard_hub.active_handlers == 0
    assert dashboard_hub.plugin_count == 0
    assert len(dashboard_hub.cpu_history) == 0
    assert len(dashboard_hub.memory_history) == 0


@pytest.mark.asyncio
async def test_update_metrics(dashboard_hub, mock_app):
    """Test that metrics are updated correctly"""
    from datetime import datetime

    # Add events to history
    now = datetime.now().isoformat()
    dashboard_hub.event_history.append({"type": "test.event", "source": "test", "timestamp": now})
    dashboard_hub.event_history.append({"type": "test.event2", "source": "test", "timestamp": now})

    # Update metrics
    await dashboard_hub._update_metrics()

    assert dashboard_hub.total_events == 2
    assert dashboard_hub.active_handlers == 2  # Two event types in mock_app
    assert dashboard_hub.plugin_count == 2  # Two plugins in mock_app


def test_format_time(dashboard_hub):
    """Test time formatting utility"""
    # Test valid ISO timestamp
    result = dashboard_hub._format_time("2024-01-01T15:30:45")
    assert result == "15:30:45"

    # Test invalid timestamp
    result = dashboard_hub._format_time("invalid")
    assert result == "just now"


def test_get_uptime(dashboard_hub):
    """Test uptime calculation"""
    from datetime import datetime, timedelta

    # Set start time to 1 hour ago
    dashboard_hub.start_time = datetime.now() - timedelta(hours=1, minutes=30, seconds=45)

    uptime = dashboard_hub._get_uptime()
    # Should be approximately "01:30:45" (may vary by a few seconds)
    assert uptime.startswith("01:30:")


@pytest.mark.asyncio
async def test_emit_test_event(dashboard_hub, mock_app):
    """Test emitting test events through dashboard"""
    # Since ui is None (mocked at import), just test the event emission
    await dashboard_hub._emit_test_event()

    # Should emit event through event bus
    mock_app.event_bus.emit.assert_called_once()
    # Check that a GenericEvent was passed with correct properties
    call_args = mock_app.event_bus.emit.call_args[0][0]  # First positional argument
    assert call_args.event_type == "test.event"
    assert call_args.data == {"message": "Test from dashboard"}
    assert call_args.source == "dashboard"
    # ui.notify won't be called since ui is None in test environment


@pytest.mark.asyncio
async def test_clear_history(dashboard_hub):
    """Test clearing event history"""
    # Add some events
    dashboard_hub.event_history.append({"type": "test1"})
    dashboard_hub.event_history.append({"type": "test2"})

    assert len(dashboard_hub.event_history) == 2

    # Clear history
    with patch("pantainos.web.dashboard.ui"):
        await dashboard_hub._clear_history()

    assert len(dashboard_hub.event_history) == 0


@pytest.mark.asyncio
async def test_system_health_updates_without_psutil(dashboard_hub):
    """Test system health metrics update when psutil returns default values"""
    # In test environment, psutil is mocked and returns 0 by default
    await dashboard_hub._update_system_health()

    # Should have 0 values from the mocked psutil
    assert dashboard_hub.cpu_usage == 0
    assert dashboard_hub.memory_usage == 0
    # History should have the 0 values added
    assert len(dashboard_hub.cpu_history) == 1
    assert len(dashboard_hub.memory_history) == 1
    assert dashboard_hub.cpu_history[0] == 0
    assert dashboard_hub.memory_history[0] == 0


@pytest.mark.asyncio
async def test_system_health_with_mock_psutil(dashboard_hub):
    """Test system health metrics update with mocked psutil"""
    # Configure the module-level mock that was set during import
    mock_psutil_module.cpu_percent.return_value = 25.5
    mock_psutil_module.virtual_memory.return_value = MagicMock(percent=60.0)

    # Patch PSUTIL_AVAILABLE to True and use the configured mock
    with (
        patch("pantainos.web.dashboard.PSUTIL_AVAILABLE", True),
        patch("pantainos.web.dashboard.psutil", mock_psutil_module),
    ):
        await dashboard_hub._update_system_health()

        # Check the values were set correctly
        assert dashboard_hub.cpu_usage == 25.5
        assert dashboard_hub.memory_usage == 60.0
        assert len(dashboard_hub.cpu_history) == 1
        assert len(dashboard_hub.memory_history) == 1
        assert dashboard_hub.cpu_history[0] == 25.5
        assert dashboard_hub.memory_history[0] == 60.0
