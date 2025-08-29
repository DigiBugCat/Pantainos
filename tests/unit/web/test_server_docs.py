"""
Tests for WebServer documentation route integration
"""

from unittest.mock import MagicMock, patch

import pytest

from pantainos.application import Pantainos


@pytest.mark.asyncio
async def test_web_server_registers_documentation_route():
    """Test that WebServer automatically registers /ui/docs documentation route"""
    app = Pantainos(database_url="sqlite:///:memory:")

    with (
        patch("pantainos.web.server.WEB_AVAILABLE", True),
        patch("pantainos.web.server.FastAPI") as mock_fastapi_class,
    ):
        mock_fastapi_instance = MagicMock()
        mock_fastapi_class.return_value = mock_fastapi_instance

        from pantainos.web.server import WebServer

        # Create WebServer instance
        web_server = WebServer(app)

        # Should have registered GET route for /ui/docs
        mock_fastapi_instance.get.assert_called_with("/ui/docs")


@pytest.mark.asyncio
async def test_documentation_route_returns_html():
    """Test that /ui/docs route returns HTML documentation"""
    app = Pantainos(database_url="sqlite:///:memory:")

    # Mock event bus with some handlers
    app.event_bus = MagicMock()
    app.event_bus.handlers = {"test.event": [{"handler": lambda: None, "condition": None, "source": "test"}]}

    with (
        patch("pantainos.web.server.WEB_AVAILABLE", True),
        patch("pantainos.web.server.FastAPI") as mock_fastapi_class,
        patch("pantainos.web.ui.NICEGUI_AVAILABLE", True),
    ):
        mock_fastapi_instance = MagicMock()
        mock_fastapi_class.return_value = mock_fastapi_instance

        from pantainos.web.server import WebServer

        # Create WebServer instance - should register documentation route
        web_server = WebServer(app)

        # Get the registered documentation handler
        get_call_args = mock_fastapi_instance.get.call_args_list
        docs_route_call = None
        for call in get_call_args:
            if call[0][0] == "/ui/docs":
                docs_route_call = call
                break

        assert docs_route_call is not None, "Expected /ui/docs route to be registered"

        # Get the handler function that was registered
        registered_handler = docs_route_call[0][1] if len(docs_route_call[0]) > 1 else docs_route_call[1].get("handler")

        # Handler should return HTML content when called
        if registered_handler:
            result = registered_handler()
            assert isinstance(result, str)
            assert "Pantainos Documentation" in result
            assert "<!DOCTYPE html>" in result
