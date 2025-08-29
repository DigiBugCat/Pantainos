"""
Tests for NiceGUI documentation UI components
"""

from unittest.mock import MagicMock, patch

import pytest

from pantainos.application import Pantainos


@pytest.mark.asyncio
async def test_documentation_ui_creation_requires_nicegui():
    """Test that DocumentationUI raises error when NiceGUI not available"""
    app = Pantainos(database_url="sqlite:///:memory:")

    with patch("pantainos.web.ui.NICEGUI_AVAILABLE", False):
        from pantainos.web.ui import DocumentationUI

        with pytest.raises(RuntimeError, match="NiceGUI not available"):
            DocumentationUI(app)


@pytest.mark.asyncio
async def test_documentation_ui_creation_with_nicegui():
    """Test that DocumentationUI can be created when NiceGUI is available"""
    app = Pantainos(database_url="sqlite:///:memory:")

    with patch("pantainos.web.ui.NICEGUI_AVAILABLE", True):
        from pantainos.web.ui import DocumentationUI

        # Should create without error
        ui = DocumentationUI(app)
        assert ui.app is app


@pytest.mark.asyncio
async def test_documentation_ui_creates_styled_html():
    """Test that DocumentationUI creates properly styled HTML for web display"""
    app = Pantainos(database_url="sqlite:///:memory:")

    # Mock handlers data
    app.event_bus = MagicMock()
    app.event_bus.handlers = {"test.event": [{"handler": lambda event: None, "condition": None, "source": "test"}]}

    # Mock plugins
    app.plugins = {"test_plugin": MagicMock(name="test_plugin", apis={"route": "handler"}, pages={"page": "handler"})}

    with patch("pantainos.web.ui.NICEGUI_AVAILABLE", True):
        from pantainos.web.ui import DocumentationUI

        ui_instance = DocumentationUI(app)
        result = ui_instance.create_documentation_page()

        # Should return styled HTML string for web display
        assert isinstance(result, str)
        assert "<!DOCTYPE html>" in result
        assert "<style>" in result  # Should include CSS styling
        assert "Pantainos Documentation" in result
        assert "Event Handlers" in result
        assert "Plugins" in result
        assert "Application Overview" in result

        # Should have proper CSS classes and styling
        assert "container" in result or "documentation" in result  # CSS classes
        assert "background-color" in result or "color:" in result  # Some CSS styling


@pytest.mark.asyncio
async def test_documentation_ui_displays_handler_information():
    """Test that DocumentationUI displays event handler information correctly"""
    app = Pantainos(database_url="sqlite:///:memory:")

    # Create mock handler
    def test_handler(event):
        """Test handler docstring"""
        pass

    app.event_bus = MagicMock()
    app.event_bus.handlers = {"user.login": [{"handler": test_handler, "condition": None, "source": "test"}]}

    with patch("pantainos.web.ui.NICEGUI_AVAILABLE", True):
        from pantainos.web.ui import DocumentationUI

        ui = DocumentationUI(app)
        html_content = ui.create_documentation_page()

        # Should contain handler information
        assert "test_handler" in html_content
        assert "user.login" in html_content
        assert "Test handler docstring" in html_content


@pytest.mark.asyncio
async def test_documentation_ui_displays_plugin_information():
    """Test that DocumentationUI displays plugin information correctly"""
    app = Pantainos(database_url="sqlite:///:memory:")
    app.event_bus = MagicMock()
    app.event_bus.handlers = {}

    # Create mock plugin
    mock_plugin = MagicMock()
    mock_plugin.name = "test_plugin"
    mock_plugin.apis = {"/events": {"handler": MagicMock()}}
    mock_plugin.pages = {"": {"handler": MagicMock()}}

    app.plugins = {"test_plugin": mock_plugin}

    with patch("pantainos.web.ui.NICEGUI_AVAILABLE", True):
        from pantainos.web.ui import DocumentationUI

        ui = DocumentationUI(app)
        html_content = ui.create_documentation_page()

        # Should contain plugin information
        assert "test_plugin" in html_content
        assert "/events" in html_content
        assert "/ui/plugins/test_plugin" in html_content


@pytest.mark.asyncio
async def test_documentation_ui_shows_application_metrics():
    """Test that DocumentationUI displays application overview metrics"""
    app = Pantainos(database_url="sqlite:///:memory:")

    # Setup mock data
    app.event_bus = MagicMock()
    app.event_bus.handlers = {"event1": [], "event2": []}
    app.plugins = {"plugin1": MagicMock(), "plugin2": MagicMock()}
    app.web_server = MagicMock()
    app.database = MagicMock()

    with patch("pantainos.web.ui.NICEGUI_AVAILABLE", True):
        from pantainos.web.ui import DocumentationUI

        ui = DocumentationUI(app)
        html_content = ui.create_documentation_page()

        # Should show metrics
        assert "Application Overview" in html_content
        assert "Event Types" in html_content
        assert "Plugins" in html_content
        assert "Web Interface" in html_content
        assert "Database" in html_content
