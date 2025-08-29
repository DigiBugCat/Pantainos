"""
Tests for Pantainos application web interface integration
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from pantainos.application import Pantainos


@pytest.mark.asyncio
async def test_application_with_web_dashboard_enabled():
    """Test that application can be configured to enable web dashboard"""
    app = Pantainos(database_url="sqlite:///:memory:", web_dashboard=True, web_port=8080)

    # Should have web configuration
    assert app.kwargs.get("web_dashboard") is True
    assert app.kwargs.get("web_port") == 8080


@pytest.mark.asyncio
async def test_application_starts_web_server_when_enabled():
    """Test that web server is started when web_dashboard is enabled"""
    with (
        patch("pantainos.web.server.WEB_AVAILABLE", True),
        patch("pantainos.web.server.FastAPI"),
        patch("pantainos.application.WebServer") as mock_web_server_class,
    ):
        mock_web_server = MagicMock()
        mock_web_server.start = AsyncMock()
        mock_web_server_class.return_value = mock_web_server

        app = Pantainos(database_url="sqlite:///:memory:", web_dashboard=True, web_port=8080)

        # Should create web server during initialization
        assert hasattr(app, "web_server")

        # Should start web server when application starts
        await app.start()
        mock_web_server.start.assert_called_once()


@pytest.mark.asyncio
async def test_application_mounts_plugin_pages_to_web_server():
    """Test that plugin pages are mounted to web server when plugins are added"""
    with (
        patch("pantainos.web.server.WEB_AVAILABLE", True),
        patch("pantainos.web.server.FastAPI"),
        patch("pantainos.application.WebServer") as mock_web_server_class,
    ):
        mock_web_server = MagicMock()
        mock_web_server.mount_plugin_pages = MagicMock()
        mock_web_server_class.return_value = mock_web_server

        app = Pantainos(database_url="sqlite:///:memory:", web_dashboard=True)

        # Create mock plugin with pages
        mock_plugin = MagicMock()
        mock_plugin.name = "test_plugin"
        mock_plugin.pages = {"": {"handler": AsyncMock()}}

        # Mount plugin
        app.mount(mock_plugin)

        # Should mount plugin pages to web server
        mock_web_server.mount_plugin_pages.assert_called_once_with(mock_plugin)


@pytest.mark.asyncio
async def test_application_mounts_plugin_apis_to_web_server():
    """Test that plugin APIs are mounted to web server when plugins are added"""
    with (
        patch("pantainos.web.server.WEB_AVAILABLE", True),
        patch("pantainos.web.server.FastAPI"),
        patch("pantainos.application.WebServer") as mock_web_server_class,
    ):
        mock_web_server = MagicMock()
        mock_web_server.mount_plugin_pages = MagicMock()
        mock_web_server.mount_plugin_apis = MagicMock()
        mock_web_server_class.return_value = mock_web_server

        app = Pantainos(database_url="sqlite:///:memory:", web_dashboard=True)

        # Create mock plugin with APIs
        mock_plugin = MagicMock()
        mock_plugin.name = "test_plugin"
        mock_plugin.apis = {"/events": {"handler": AsyncMock()}}

        # Mount plugin
        app.mount(mock_plugin)

        # Should mount both plugin pages and APIs to web server
        mock_web_server.mount_plugin_pages.assert_called_once_with(mock_plugin)
        mock_web_server.mount_plugin_apis.assert_called_once_with(mock_plugin)


@pytest.mark.asyncio
async def test_application_no_web_server_when_disabled():
    """Test that no web server is created when web_dashboard is False"""
    app = Pantainos(database_url="sqlite:///:memory:", web_dashboard=False)

    # Should not have web_server attribute
    assert not hasattr(app, "web_server")


@pytest.mark.asyncio
async def test_application_web_server_default_disabled():
    """Test that web server is disabled by default"""
    app = Pantainos(database_url="sqlite:///:memory:")

    # Web dashboard should be disabled by default
    assert not hasattr(app, "web_server")
    assert app.kwargs.get("web_dashboard") is None
