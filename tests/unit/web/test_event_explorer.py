"""
Tests for Event Explorer interface
"""

import asyncio
from unittest.mock import MagicMock, patch

import pytest

from pantainos.application import Pantainos
from pantainos.events import GenericEvent


@pytest.mark.asyncio
async def test_event_explorer_creation_requires_nicegui():
    """Test that EventExplorer raises error when NiceGUI not available"""
    app = Pantainos(database_url="sqlite:///:memory:")

    with patch("pantainos.web.event_explorer.NICEGUI_AVAILABLE", False):
        from pantainos.web.event_explorer import EventExplorer

        with pytest.raises(RuntimeError, match="NiceGUI not available"):
            EventExplorer(app)


@pytest.mark.asyncio
async def test_event_explorer_creation_with_nicegui():
    """Test that EventExplorer can be created when NiceGUI is available"""
    app = Pantainos(database_url="sqlite:///:memory:")

    with patch("pantainos.web.event_explorer.NICEGUI_AVAILABLE", True):
        from pantainos.web.event_explorer import EventExplorer

        explorer = EventExplorer(app)
        assert explorer.app is app
        assert explorer.recent_events is not None
        assert explorer.handler_stats is not None


@pytest.mark.asyncio
async def test_event_explorer_tracks_events():
    """Test that EventExplorer tracks events passing through event bus"""
    app = Pantainos(database_url="sqlite:///:memory:")

    with patch("pantainos.web.event_explorer.NICEGUI_AVAILABLE", True):
        from pantainos.web.event_explorer import EventExplorer

        explorer = EventExplorer(app)

        # Start the event bus to process events
        await app.event_bus.start()

        # Emit an event
        event = GenericEvent(type="test.event", data={"data": "test"}, source="test-source")
        await app.event_bus.emit(event)

        # Give event time to be processed
        await asyncio.sleep(0.1)

        # Check that event was tracked
        assert len(explorer.recent_events) == 1
        event = explorer.recent_events[0]
        assert event["type"] == "test.event"
        assert event["data"] == {"data": "test"}
        assert event["source"] == "test-source"
        assert "timestamp" in event

        # Stop the event bus
        await app.event_bus.stop()


@pytest.mark.asyncio
async def test_event_explorer_creates_interface_components():
    """Test that EventExplorer creates the required interface components"""
    app = Pantainos(database_url="sqlite:///:memory:")

    with patch("pantainos.web.event_explorer.NICEGUI_AVAILABLE", True):
        # Mock ui module
        mock_ui = MagicMock()

        with patch("pantainos.web.event_explorer.ui", mock_ui):
            from pantainos.web.event_explorer import EventExplorer

            explorer = EventExplorer(app)
            explorer.create_interface()

            # Should create main components
            mock_ui.column.assert_called()
            mock_ui.row.assert_called()
            mock_ui.card.assert_called()
            mock_ui.label.assert_called()

            # Should have event console elements
            mock_ui.select.assert_called()  # Event type selector
            mock_ui.input.assert_called()  # Source input
            mock_ui.textarea.assert_called()  # JSON data editor
            mock_ui.button.assert_called()  # Emit button

            # Should set up timer for real-time updates
            mock_ui.timer.assert_called()

            # Should create refreshable components
            mock_ui.refreshable.assert_called()


@pytest.mark.asyncio
async def test_event_explorer_handler_statistics():
    """Test that EventExplorer tracks handler execution statistics"""
    app = Pantainos(database_url="sqlite:///:memory:")

    # Register a test handler
    @app.on("test.event")
    async def test_handler(event):
        pass

    with patch("pantainos.web.event_explorer.NICEGUI_AVAILABLE", True):
        from pantainos.web.event_explorer import EventExplorer

        explorer = EventExplorer(app)

        # Start the event bus to process events
        await app.event_bus.start()

        # Emit events
        event1 = GenericEvent(type="test.event", data={}, source="test")
        event2 = GenericEvent(type="test.event", data={}, source="test")
        await app.event_bus.emit(event1)
        await app.event_bus.emit(event2)

        # Give events time to be processed
        await asyncio.sleep(0.1)

        # Check handler stats
        assert "test_handler" in explorer.handler_stats
        assert explorer.handler_stats["test_handler"] == 2

        # Stop the event bus
        await app.event_bus.stop()


@pytest.mark.asyncio
async def test_event_explorer_recent_events_limit():
    """Test that EventExplorer limits the number of recent events"""
    app = Pantainos(database_url="sqlite:///:memory:")

    with patch("pantainos.web.event_explorer.NICEGUI_AVAILABLE", True):
        from pantainos.web.event_explorer import EventExplorer

        explorer = EventExplorer(app)

        # Start the event bus to process events
        await app.event_bus.start()

        # Emit more events than the limit
        for i in range(60):
            event = GenericEvent(type=f"test.event.{i}", data={}, source="test")
            await app.event_bus.emit(event)

        # Give events time to be processed
        await asyncio.sleep(0.2)

        # Should only keep last 50 events
        assert len(explorer.recent_events) == 50

        # Most recent event should be the last one emitted
        assert explorer.recent_events[-1]["type"] == "test.event.59"

        # Stop the event bus
        await app.event_bus.stop()
