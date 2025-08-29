"""
Tests for Event Explorer integration with WebServer
"""

from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from pantainos.application import Pantainos
from pantainos.web.server import WebServer


@pytest.mark.asyncio
async def test_event_explorer_route_exists():
    """Test that Event Explorer route is registered in WebServer"""
    app = Pantainos(database_url="sqlite:///:memory:")
    web_server = WebServer(app)

    # Get FastAPI app
    fastapi_app = web_server.get_fastapi_app()

    # Create test client
    client = TestClient(fastapi_app)

    # Test that the route exists
    response = client.get("/ui/events")
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_event_explorer_route_without_nicegui():
    """Test Event Explorer route when NiceGUI is not available"""
    app = Pantainos(database_url="sqlite:///:memory:")

    with patch("pantainos.web.event_explorer.NICEGUI_AVAILABLE", False):
        web_server = WebServer(app)
        fastapi_app = web_server.get_fastapi_app()
        client = TestClient(fastapi_app)

        response = client.get("/ui/events")
        assert response.status_code == 200
        assert "Event Explorer unavailable" in response.text
        assert "NiceGUI not installed" in response.text


@pytest.mark.asyncio
async def test_event_explorer_route_with_nicegui():
    """Test Event Explorer route when NiceGUI is available"""
    app = Pantainos(database_url="sqlite:///:memory:")

    with patch("pantainos.web.event_explorer.NICEGUI_AVAILABLE", True):
        web_server = WebServer(app)
        fastapi_app = web_server.get_fastapi_app()
        client = TestClient(fastapi_app)

        response = client.get("/ui/events")
        assert response.status_code == 200
        assert "Event Explorer" in response.text
