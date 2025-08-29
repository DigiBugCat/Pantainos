"""
Tests for web server functionality
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest


@pytest.fixture
def mock_pantainos_app():
    """Create a mock Pantainos application"""
    app = MagicMock()
    app.event_bus = MagicMock()
    app.event_bus.running = True
    app.event_bus.handlers = {"test.event": []}
    app.schedule_manager = MagicMock()
    app.schedule_manager.running = True
    app.plugins = {}
    app.emit = AsyncMock()
    return app


@pytest.mark.asyncio
async def test_web_server_import():
    """Test that WebServer can be imported when dependencies are available"""
    try:
        from pantainos.web.server import WebServer

        assert WebServer is not None
    except ImportError as e:
        # Skip test if web dependencies not available
        pytest.skip(f"Web dependencies not available: {e}")


@pytest.mark.asyncio
async def test_web_server_creation_without_dependencies():
    """Test that WebServer raises error when dependencies missing"""
    with patch("pantainos.web.server.WEB_AVAILABLE", False):
        from pantainos.web.server import WebServer

        mock_app = MagicMock()

        with pytest.raises(RuntimeError, match="Web dependencies not available"):
            WebServer(mock_app)


@pytest.mark.asyncio
async def test_web_server_creation_with_dependencies(mock_pantainos_app):
    """Test WebServer creation when dependencies are available"""
    with (
        patch("pantainos.web.server.WEB_AVAILABLE", True),
        patch("pantainos.web.server.FastAPI"),
    ):
        from pantainos.web.server import WebServer

        web_server = WebServer(mock_pantainos_app)

        assert web_server.app is mock_pantainos_app
        assert hasattr(web_server, "fastapi")
        assert hasattr(web_server, "plugin_pages")


@pytest.mark.asyncio
async def test_web_server_health_endpoint(mock_pantainos_app):
    """Test that health endpoint returns correct status"""
    with (
        patch("pantainos.web.server.WEB_AVAILABLE", True),
        patch("pantainos.web.server.FastAPI") as mock_fastapi,
    ):
        from pantainos.web.server import WebServer

        # Mock FastAPI instance
        mock_app = MagicMock()
        mock_fastapi.return_value = mock_app

        WebServer(mock_pantainos_app)

        # Verify FastAPI instance was created with correct parameters
        mock_fastapi.assert_called_once()
        call_kwargs = mock_fastapi.call_args[1]
        assert call_kwargs["title"] == "Pantainos API"
        assert "event-driven application" in call_kwargs["description"]


@pytest.mark.asyncio
async def test_plugin_page_mounting():
    """Test that plugin pages can be mounted"""
    with (
        patch("pantainos.web.server.WEB_AVAILABLE", True),
        patch("pantainos.web.server.FastAPI"),
    ):
        from pantainos.web.server import WebServer

        mock_app = MagicMock()
        mock_app.event_bus.running = True
        mock_app.schedule_manager.running = True
        mock_app.plugins = {}
        mock_app.event_bus.handlers = {}

        web_server = WebServer(mock_app)

        # Create mock plugin with pages
        mock_plugin = MagicMock()
        mock_plugin.name = "test_plugin"
        mock_plugin.pages = {"": {"handler": AsyncMock()}, "config": {"handler": AsyncMock()}}

        # Test mounting
        web_server.mount_plugin_pages(mock_plugin)

        assert "test_plugin" in web_server.plugin_pages
        assert web_server.plugin_pages["test_plugin"] == mock_plugin.pages


@pytest.mark.asyncio
async def test_plugin_without_pages():
    """Test handling plugins that don't have web pages"""
    with (
        patch("pantainos.web.server.WEB_AVAILABLE", True),
        patch("pantainos.web.server.FastAPI"),
    ):
        from pantainos.web.server import WebServer

        mock_app = MagicMock()
        mock_app.event_bus.running = True
        mock_app.schedule_manager.running = True
        mock_app.plugins = {}
        mock_app.event_bus.handlers = {}

        web_server = WebServer(mock_app)

        # Create mock plugin without pages
        mock_plugin = MagicMock()
        mock_plugin.name = "simple_plugin"
        # No pages attribute

        # Should not raise error
        web_server.mount_plugin_pages(mock_plugin)

        assert "simple_plugin" not in web_server.plugin_pages


@pytest.mark.asyncio
async def test_get_fastapi_app():
    """Test getting the FastAPI application instance"""
    with (
        patch("pantainos.web.server.WEB_AVAILABLE", True),
        patch("pantainos.web.server.FastAPI") as mock_fastapi,
    ):
        from pantainos.web.server import WebServer

        mock_app = MagicMock()
        mock_app.event_bus.running = True
        mock_app.schedule_manager.running = True
        mock_app.plugins = {}
        mock_app.event_bus.handlers = {}

        mock_fastapi_instance = MagicMock()
        mock_fastapi.return_value = mock_fastapi_instance

        web_server = WebServer(mock_app)

        assert web_server.get_fastapi_app() is mock_fastapi_instance


@pytest.mark.asyncio
async def test_web_server_start():
    """Test starting the web server"""
    with (
        patch("pantainos.web.server.WEB_AVAILABLE", True),
        patch("pantainos.web.server.FastAPI") as mock_fastapi,
        patch("uvicorn.Config") as mock_config,
        patch("uvicorn.Server") as mock_server_class,
    ):
        from pantainos.web.server import WebServer

        mock_app = MagicMock()
        mock_app.event_bus.running = True
        mock_app.schedule_manager.running = True
        mock_app.plugins = {}
        mock_app.event_bus.handlers = {}

        mock_fastapi_instance = MagicMock()
        mock_fastapi.return_value = mock_fastapi_instance

        # Mock uvicorn server instance
        mock_server_instance = AsyncMock()
        mock_server_class.return_value = mock_server_instance

        # Mock config instance
        mock_config_instance = MagicMock()
        mock_config.return_value = mock_config_instance

        web_server = WebServer(mock_app)

        # Test start with default port
        await web_server.start()

        # Should have created config with correct parameters
        mock_config.assert_called_once_with(app=mock_fastapi_instance, port=8080, host="127.0.0.1", log_level="info")

        # Should have created server with config
        mock_server_class.assert_called_once_with(mock_config_instance)

        # Should have called server.serve()
        mock_server_instance.serve.assert_called_once()


@pytest.mark.asyncio
async def test_web_server_start_custom_port():
    """Test starting the web server with custom port"""
    with (
        patch("pantainos.web.server.WEB_AVAILABLE", True),
        patch("pantainos.web.server.FastAPI") as mock_fastapi,
        patch("uvicorn.Config") as mock_config,
        patch("uvicorn.Server") as mock_server_class,
    ):
        from pantainos.web.server import WebServer

        mock_app = MagicMock()
        mock_app.event_bus.running = True
        mock_app.schedule_manager.running = True
        mock_app.plugins = {}
        mock_app.event_bus.handlers = {}

        mock_fastapi_instance = MagicMock()
        mock_fastapi.return_value = mock_fastapi_instance

        # Mock uvicorn server instance
        mock_server_instance = AsyncMock()
        mock_server_class.return_value = mock_server_instance

        # Mock config instance
        mock_config_instance = MagicMock()
        mock_config.return_value = mock_config_instance

        web_server = WebServer(mock_app)

        # Test start with custom port
        await web_server.start(port=9000, host="127.0.0.1")

        # Should have created config with custom parameters
        mock_config.assert_called_once_with(app=mock_fastapi_instance, port=9000, host="127.0.0.1", log_level="info")

        # Should have created server with config
        mock_server_class.assert_called_once_with(mock_config_instance)

        # Should have called server.serve()
        mock_server_instance.serve.assert_called_once()


@pytest.mark.asyncio
async def test_plugin_api_mounting():
    """Test that plugin API endpoints can be mounted to FastAPI"""
    with (
        patch("pantainos.web.server.WEB_AVAILABLE", True),
        patch("pantainos.web.server.FastAPI") as mock_fastapi,
    ):
        from pantainos.web.server import WebServer

        mock_app = MagicMock()
        mock_app.event_bus.running = True
        mock_app.schedule_manager.running = True
        mock_app.plugins = {}
        mock_app.event_bus.handlers = {}

        # Mock FastAPI instance
        mock_fastapi_instance = MagicMock()
        mock_fastapi.return_value = mock_fastapi_instance

        web_server = WebServer(mock_app)

        # Create mock plugin with API endpoints
        mock_plugin = MagicMock()
        mock_plugin.name = "test_plugin"
        mock_plugin.apis = {
            "/events": {"handler": AsyncMock(), "type": "api"},
            "/metrics": {"handler": AsyncMock(), "type": "api"},
            "/metrics/reset": {"handler": AsyncMock(), "type": "api"},
        }

        # Test mounting APIs
        web_server.mount_plugin_apis(mock_plugin)

        # Verify that endpoints were registered with FastAPI
        assert mock_fastapi_instance.post.call_count == 2  # /events and /metrics/reset
        assert mock_fastapi_instance.get.call_count == 3  # /metrics, /ui/docs, and /ui/events

        # Check specific endpoint registrations with correct namespacing
        post_calls = [call[0][0] for call in mock_fastapi_instance.post.call_args_list]
        get_calls = [call[0][0] for call in mock_fastapi_instance.get.call_args_list]

        assert "/api/plugins/test_plugin/events" in post_calls
        assert "/api/plugins/test_plugin/metrics/reset" in post_calls
        assert "/api/plugins/test_plugin/metrics" in get_calls


@pytest.mark.asyncio
async def test_plugin_without_apis():
    """Test handling plugins that don't have API endpoints"""
    with (
        patch("pantainos.web.server.WEB_AVAILABLE", True),
        patch("pantainos.web.server.FastAPI") as mock_fastapi,
    ):
        from pantainos.web.server import WebServer

        mock_app = MagicMock()
        mock_app.event_bus.running = True
        mock_app.schedule_manager.running = True
        mock_app.plugins = {}
        mock_app.event_bus.handlers = {}

        mock_fastapi_instance = MagicMock()
        mock_fastapi.return_value = mock_fastapi_instance

        web_server = WebServer(mock_app)

        # Create mock plugin without APIs
        mock_plugin = MagicMock()
        mock_plugin.name = "simple_plugin"
        # No apis attribute

        # Should not raise error
        web_server.mount_plugin_apis(mock_plugin)

        # Should not have registered any endpoints (except docs routes)
        assert mock_fastapi_instance.post.call_count == 0
        assert mock_fastapi_instance.get.call_count == 2  # Documentation and Event Explorer routes


@pytest.mark.asyncio
async def test_plugin_page_ui_route_mounting():
    """Test that plugin pages are mounted as UI routes with proper namespacing"""
    with (
        patch("pantainos.web.server.WEB_AVAILABLE", True),
        patch("pantainos.web.server.FastAPI") as mock_fastapi,
    ):
        from pantainos.web.server import WebServer

        mock_app = MagicMock()
        mock_app.event_bus.running = True
        mock_app.schedule_manager.running = True
        mock_app.plugins = {}
        mock_app.event_bus.handlers = {}

        # Mock FastAPI instance
        mock_fastapi_instance = MagicMock()
        mock_fastapi.return_value = mock_fastapi_instance

        web_server = WebServer(mock_app)

        # Create mock plugin with pages
        mock_plugin = MagicMock()
        mock_plugin.name = "test_plugin"
        mock_plugin.pages = {
            "": {"handler": AsyncMock(), "type": "page"},  # Main page
            "config": {"handler": AsyncMock(), "type": "page"},  # Config subpage
            "dashboard": {"handler": AsyncMock(), "type": "page"},  # Dashboard subpage
        }

        # Test mounting pages as UI routes
        web_server.mount_plugin_pages(mock_plugin)

        # Verify that pages were registered as GET routes with proper namespacing
        assert mock_fastapi_instance.get.call_count == 5  # Main, config, dashboard, /ui/docs, and /ui/events

        # Check specific UI route registrations
        get_calls = [call[0][0] for call in mock_fastapi_instance.get.call_args_list]

        assert "/ui/plugins/test_plugin/" in get_calls  # Main page
        assert "/ui/plugins/test_plugin/config" in get_calls  # Config subpage
        assert "/ui/plugins/test_plugin/dashboard" in get_calls  # Dashboard subpage
