"""
Integration tests for uvicorn reload functionality
"""

import asyncio

import pytest

from tests.fixtures.servers import create_test_server


class TestUvicornReload:
    """Test uvicorn reload functionality with Pantainos"""

    @pytest.mark.asyncio
    async def test_server_starts_with_reload_enabled(self):
        """Test that server starts correctly with reload enabled"""
        server = create_test_server(port=8901, reload=True)

        async with server.run_async():
            # Verify server is running
            response = await server.get("/")
            # NiceGUI typically returns 200 or redirects
            assert response.status_code in (200, 307, 404)  # 404 ok if no routes defined

            # Verify reload is enabled in config
            assert server.reload is True

    @pytest.mark.asyncio
    async def test_server_starts_with_reload_disabled(self):
        """Test that server starts correctly with reload disabled"""
        server = create_test_server(port=8902, reload=False)

        async with server.run_async():
            # Verify server is running
            response = await server.get("/")
            assert response.status_code in (200, 307, 404)

            # Verify reload is disabled in config
            assert server.reload is False

    @pytest.mark.asyncio
    async def test_uvicorn_config_contains_reload_settings(self):
        """Test that uvicorn config contains correct reload settings"""
        server_with_reload = create_test_server(port=8903, reload=True)
        server_without_reload = create_test_server(port=8904, reload=False)

        # Test with reload enabled
        async with server_with_reload.run_async():
            # The server should have reload enabled
            assert server_with_reload.server is not None
            config = server_with_reload.server.config
            assert config.reload is True

        # Test with reload disabled
        async with server_without_reload.run_async():
            # The server should have reload disabled
            assert server_without_reload.server is not None
            config = server_without_reload.server.config
            assert config.reload is False

    @pytest.mark.asyncio
    async def test_reload_dirs_configuration(self):
        """Test that server starts successfully with reload_dirs parameter"""
        server = create_test_server(port=8905, reload=True, reload_dirs=["src", "tests"])

        async with server.run_async():
            assert server.server is not None
            config = server.server.config

            # Verify server starts successfully with reload_dirs parameter
            assert config.reload is True

            # Verify server responds to requests
            response = await server.get("/")
            assert response.status_code in (200, 307, 404)

    @pytest.mark.asyncio
    async def test_reload_includes_configuration(self):
        """Test that reload includes parameters are accepted by server"""
        server = create_test_server(port=8906, reload=True, reload_includes=["*.py", "*.html"])

        async with server.run_async():
            assert server.server is not None

            # Verify the reload_includes parameter was passed to kwargs
            assert "reload_includes" in server.kwargs
            assert "*.py" in server.kwargs["reload_includes"]
            assert "*.html" in server.kwargs["reload_includes"]

    @pytest.mark.asyncio
    async def test_reload_excludes_configuration(self):
        """Test that reload excludes parameters are accepted by server"""
        server = create_test_server(port=8907, reload=True, reload_excludes=["*.pyc", "__pycache__"])

        async with server.run_async():
            assert server.server is not None

            # Verify the reload_excludes parameter was passed to kwargs
            assert "reload_excludes" in server.kwargs
            assert "*.pyc" in server.kwargs["reload_excludes"]
            assert "__pycache__" in server.kwargs["reload_excludes"]

    @pytest.mark.asyncio
    async def test_server_responds_after_startup(self):
        """Test that server responds to HTTP requests after startup"""
        server = create_test_server(port=8908, reload=True)

        async with server.run_async():
            # Test root endpoint
            response = await server.get("/")
            assert response.status_code in (200, 307, 404)

            # Test that server is actually serving content
            assert response.headers.get("server") or "uvicorn" in str(response.headers).lower()

    @pytest.mark.asyncio
    async def test_multiple_requests_with_reload_enabled(self):
        """Test that server handles multiple requests with reload enabled"""
        server = create_test_server(port=8909, reload=True)

        async with server.run_async():
            # Make multiple requests
            responses = []
            for _ in range(5):
                response = await server.get("/")
                responses.append(response)
                await asyncio.sleep(0.1)

            # All requests should succeed
            for response in responses:
                assert response.status_code in (200, 307, 404)

    @pytest.mark.asyncio
    async def test_server_handles_concurrent_requests(self):
        """Test that server handles concurrent requests with reload enabled"""
        server = create_test_server(port=8910, reload=True)

        async with server.run_async():
            # Make concurrent requests
            tasks = [server.get("/") for _ in range(10)]
            responses = await asyncio.gather(*tasks)

            # All requests should succeed
            for response in responses:
                assert response.status_code in (200, 307, 404)
