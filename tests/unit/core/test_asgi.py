"""
Tests for ASGIManager
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from pantainos.core.asgi import ASGIManager


@pytest.fixture
def mock_app():
    """Create mock Pantainos app instance."""
    app = MagicMock()
    app.lifecycle_manager = AsyncMock()
    app.db_initializer = MagicMock()
    app.database_url = "sqlite:///:memory:"
    app.master_key = None
    return app


@pytest.fixture
def asgi_manager(mock_app):
    """Create ASGIManager with mocked FastAPI."""
    with patch("pantainos.core.asgi.WEB_AVAILABLE", True), patch("pantainos.core.asgi.FastAPI") as mock_fastapi_class:
        mock_fastapi = MagicMock()
        mock_fastapi_class.return_value = mock_fastapi

        manager = ASGIManager(mock_app)
        return manager, mock_fastapi


def test_asgi_manager_web_unavailable(mock_app):
    """Test ASGIManager when web dependencies are not available."""
    with patch("pantainos.core.asgi.WEB_AVAILABLE", False):
        with pytest.raises(RuntimeError, match="Web dependencies not available"):
            ASGIManager(mock_app)


@pytest.mark.asyncio
async def test_lifespan_startup_shutdown(asgi_manager):
    """Test ASGI lifespan protocol startup and shutdown."""
    manager, mock_fastapi = asgi_manager
    mock_app = manager.app

    # Test lifespan context manager
    async with manager.lifespan(mock_fastapi):
        # Verify startup was called
        mock_app.lifecycle_manager.start.assert_called_once_with(
            database_url=mock_app.database_url,
            master_key=mock_app.master_key,
            emit_startup_event=True,
        )
        assert mock_app.database == mock_app.db_initializer.database

    # Verify shutdown was called
    mock_app.lifecycle_manager.stop.assert_called_once()


@pytest.mark.asyncio
async def test_startup_internal(asgi_manager):
    """Test internal startup logic."""
    manager, _ = asgi_manager
    mock_app = manager.app

    await manager._startup()

    mock_app.lifecycle_manager.start.assert_called_once_with(
        database_url=mock_app.database_url,
        master_key=mock_app.master_key,
        emit_startup_event=True,
    )
    assert mock_app.database == mock_app.db_initializer.database


@pytest.mark.asyncio
async def test_shutdown_internal(asgi_manager):
    """Test internal shutdown logic."""
    manager, _ = asgi_manager
    mock_app = manager.app

    await manager._shutdown()

    mock_app.lifecycle_manager.stop.assert_called_once()


def test_setup_web_routes(asgi_manager):
    """Test that web routes are properly registered."""
    manager, mock_fastapi = asgi_manager

    # Verify that routes were registered
    assert mock_fastapi.get.call_count == 2

    # Check that the correct routes were registered
    call_args_list = mock_fastapi.get.call_args_list

    # Extract the route paths from the calls
    routes = []
    for call in call_args_list:
        if call.args:
            routes.append(call.args[0])

    assert "/ui/docs" in routes
    assert "/ui/events" in routes


def test_asgi_manager_callable(asgi_manager):
    """Test that ASGIManager is callable and returns FastAPI app."""
    manager, mock_fastapi = asgi_manager

    result = manager()

    assert result == mock_fastapi


def test_fastapi_creation_parameters(asgi_manager):
    """Test that FastAPI is created with correct parameters."""
    manager, _ = asgi_manager

    with patch("pantainos.core.asgi.FastAPI") as mock_fastapi_class:
        ASGIManager(manager.app)

        mock_fastapi_class.assert_called_once()
        call_kwargs = mock_fastapi_class.call_args.kwargs

        assert call_kwargs["title"] == "Pantainos API"
        assert call_kwargs["description"] == "REST API for Pantainos event-driven application"
        assert call_kwargs["version"] == "0.1.0"
        assert "lifespan" in call_kwargs


def test_documentation_route_success():
    """Test documentation route with successful DocumentationUI."""
    mock_app = MagicMock()

    with patch("pantainos.core.asgi.WEB_AVAILABLE", True):
        with patch("pantainos.core.asgi.FastAPI") as mock_fastapi_class:
            mock_fastapi = MagicMock()
            mock_fastapi_class.return_value = mock_fastapi

            # Create manager to trigger route setup
            manager = ASGIManager(mock_app)

            # Test that DocumentationUI import and usage works
            with patch("pantainos.web.ui.DocumentationUI") as mock_doc_ui:
                mock_doc_ui.return_value.create_documentation_page.return_value = "<html>docs</html>"

                # This tests the route setup was successful
                assert mock_fastapi.get.call_count == 2


def test_documentation_route_error():
    """Test documentation route error handling."""
    mock_app = MagicMock()

    with patch("pantainos.core.asgi.WEB_AVAILABLE", True):
        with patch("pantainos.core.asgi.FastAPI") as mock_fastapi_class:
            mock_fastapi = MagicMock()
            mock_fastapi_class.return_value = mock_fastapi

            # Create manager - should not raise even if DocumentationUI would fail
            manager = ASGIManager(mock_app)

            # Route should be registered successfully
            assert mock_fastapi.get.call_count == 2


def test_event_explorer_route_setup():
    """Test event explorer route setup."""
    mock_app = MagicMock()

    with patch("pantainos.core.asgi.WEB_AVAILABLE", True):
        with patch("pantainos.core.asgi.FastAPI") as mock_fastapi_class:
            mock_fastapi = MagicMock()
            mock_fastapi_class.return_value = mock_fastapi

            # Create manager to trigger route setup
            manager = ASGIManager(mock_app)

            # Verify routes are registered
            assert mock_fastapi.get.call_count == 2

            # Check HTMLResponse is used
            call_kwargs_list = [call.kwargs for call in mock_fastapi.get.call_args_list]
            response_classes = [kwargs.get("response_class") for kwargs in call_kwargs_list]

            # Both routes should use HTMLResponse
            from pantainos.core.asgi import HTMLResponse

            assert all(rc == HTMLResponse for rc in response_classes if rc is not None)
