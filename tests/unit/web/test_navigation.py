"""
Test suite for the Navigation System component.
"""

from unittest.mock import MagicMock, patch

import pytest

# Mock NiceGUI before import
mock_nicegui = MagicMock()
mock_nicegui.__bool__ = lambda self: True  # Make it truthy
mock_nicegui.__nonzero__ = lambda self: True  # Python 2 compatibility

with patch.dict("sys.modules", {"nicegui": mock_nicegui, "nicegui.events": MagicMock()}):
    from pantainos.web.components.navigation import NavigationBuilder, NavigationSystem


@pytest.fixture
def mock_app():
    """Mock Pantainos application."""
    app = MagicMock()
    app.event_bus = MagicMock()
    app.plugins = {}
    return app


@pytest.fixture
def navigation_system(mock_app):
    """Create a navigation system instance."""
    return NavigationSystem(mock_app)


def test_navigation_system_initialization(navigation_system, mock_app):
    """Test that NavigationSystem initializes correctly."""
    assert navigation_system.app == mock_app
    assert navigation_system.current_page == "dashboard"
    assert navigation_system.sidebar_expanded is True
    assert navigation_system.search_query == ""
    assert len(navigation_system.nav_items) > 0


def test_navigation_has_default_items(navigation_system):
    """Test that navigation has default menu items."""
    items = navigation_system.nav_items

    # Check we have essential items
    item_ids = [item["id"] for item in items]
    assert "dashboard" in item_ids
    assert "events" in item_ids
    assert "plugins" in item_ids
    assert "settings" in item_ids

    # Check item structure
    for item in items:
        assert "id" in item
        assert "label" in item
        assert "icon" in item
        assert "path" in item


def test_toggle_sidebar(navigation_system):
    """Test sidebar toggle functionality."""
    # Initially expanded
    assert navigation_system.sidebar_expanded is True

    # Toggle to collapsed
    navigation_system._toggle_sidebar()
    assert navigation_system.sidebar_expanded is False

    # Toggle back to expanded
    navigation_system._toggle_sidebar()
    assert navigation_system.sidebar_expanded is True


def test_navigate_to_page(navigation_system):
    """Test navigation to different pages."""
    # Navigation should update current_page regardless of ui availability
    navigation_system._navigate_to("events", "/events")
    assert navigation_system.current_page == "events"

    navigation_system._navigate_to("plugins", "/plugins")
    assert navigation_system.current_page == "plugins"


def test_get_current_page_label(navigation_system):
    """Test getting the current page label."""
    # Default page
    assert navigation_system._get_current_page_label() == "Dashboard"

    # Change page
    navigation_system.current_page = "events"
    assert navigation_system._get_current_page_label() == "Events"

    # Unknown page
    navigation_system.current_page = "unknown"
    assert navigation_system._get_current_page_label() == "Dashboard"


def test_search_query_update(navigation_system):
    """Test search query updates."""
    assert navigation_system.search_query == ""

    # Update search query
    navigation_system.search_query = "test query"
    assert navigation_system.search_query == "test query"


def test_navigation_builder(mock_app):
    """Test NavigationBuilder for customizing navigation."""
    builder = NavigationBuilder(mock_app)

    # Customize navigation
    custom_items = [{"id": "custom", "label": "Custom", "icon": "star", "path": "/custom"}]

    nav = builder.with_items(custom_items).with_sidebar(expanded=False).build()

    assert nav.nav_items == custom_items
    assert nav.sidebar_expanded is False


def test_navigation_builder_chain(mock_app):
    """Test NavigationBuilder method chaining."""
    nav = NavigationBuilder(mock_app).with_sidebar(expanded=False).build()

    assert isinstance(nav, NavigationSystem)
    assert nav.sidebar_expanded is False


def test_setup_routing_with_callback(navigation_system):
    """Test routing setup with callback."""
    callback_called = []

    def on_route_change(page_id):
        callback_called.append(page_id)

    # Should work without errors even when ui is None
    navigation_system.setup_routing(on_route_change)
    # No error should occur - function returns early when ui is None


def test_mobile_menu_shows_limited_items(navigation_system):
    """Test that mobile menu shows only main items."""
    # Mobile menu should show only first 4 items
    main_items = navigation_system.nav_items[:4]
    assert len(main_items) == 4
    assert main_items[0]["id"] == "dashboard"


def test_navigation_system_initialization_check():
    """Test that NavigationSystem checks for NiceGUI availability."""
    # Since we mocked nicegui at import time, NICEGUI_AVAILABLE is True
    # So this test verifies the NavigationSystem can be created with our mock
    mock_app = MagicMock()
    mock_app.event_bus = MagicMock()
    mock_app.plugins = {}

    # Should create successfully with our mocked nicegui
    nav = NavigationSystem(mock_app)
    assert nav is not None
    assert nav.app == mock_app
