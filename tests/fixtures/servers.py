"""
Server management utilities for Pantainos integration and E2E tests
"""

import asyncio
import contextlib
import logging
import threading
import time
from collections.abc import AsyncIterator
from typing import Any

import httpx
import uvicorn
from fastapi import FastAPI

from pantainos.core import EventBus
from pantainos.core.di.container import ServiceContainer
from pantainos.core.di.registry import HandlerRegistry

logger = logging.getLogger(__name__)


class TestUvicornServer(uvicorn.Server):
    """Uvicorn test server that can be run in a thread for testing"""

    def install_signal_handlers(self):
        """Override to prevent signal handler installation in tests"""
        pass

    @contextlib.contextmanager
    def run_in_thread(self):
        """Run the server in a background thread"""
        thread = threading.Thread(target=self.run)
        thread.start()
        try:
            # Wait for server to start
            while not self.started:
                time.sleep(0.001)
            yield
        finally:
            self.should_exit = True
            thread.join()


class PantainosTestServer:
    """Test server wrapper for Pantainos application"""

    def __init__(
        self,
        host: str = "127.0.0.1",
        port: int = 8899,
        reload: bool = False,
        **kwargs: Any,
    ) -> None:
        self.host = host
        self.port = port
        self.reload = reload
        self.kwargs = kwargs
        self.server: TestUvicornServer | None = None
        self.event_bus: EventBus | None = None
        self._started = False

    async def create_app(self) -> FastAPI:
        """Create the Pantainos FastAPI application"""
        # Create minimal event bus for testing
        container = ServiceContainer()
        registry = HandlerRegistry(container)
        self.event_bus = EventBus(registry)

        # Create FastAPI app for testing
        # Skip NiceGUI integration to avoid middleware conflicts in tests
        # The key part we're testing is the uvicorn reload configuration
        fastapi_app = FastAPI(title="Pantainos Test")

        # Add a simple test route for health checks
        @fastapi_app.get("/")
        async def root():
            return {"message": "Pantainos Test Server", "status": "running"}

        return fastapi_app

    @contextlib.asynccontextmanager
    async def run_async(self) -> AsyncIterator["PantainosTestServer"]:
        """Run the server asynchronously with proper cleanup"""
        try:
            app = await self.create_app()

            config = uvicorn.Config(
                app,
                host=self.host,
                port=self.port,
                reload=self.reload,
                log_level="warning",  # Reduce noise in tests
                **self.kwargs,
            )

            self.server = TestUvicornServer(config)

            with self.server.run_in_thread():
                # Wait for server to be responsive
                await self.wait_for_startup()
                self._started = True
                yield self
        finally:
            await self.shutdown()

    async def wait_for_startup(self) -> None:
        """Wait for the server to become responsive"""
        async with asyncio.timeout(10.0):
            async with httpx.AsyncClient() as client:
                while True:
                    try:
                        response = await client.get(f"http://{self.host}:{self.port}/")
                        if response.status_code in (200, 404):  # 404 is OK if no routes defined
                            return
                    except (httpx.ConnectError, httpx.TimeoutException):
                        pass
                    await asyncio.sleep(0.1)

    async def shutdown(self) -> None:
        """Shutdown the server and cleanup resources"""
        if self.server and self._started:
            self.server.should_exit = True

        if self.event_bus:
            try:
                await asyncio.wait_for(self.event_bus.stop(), timeout=2.0)
            except TimeoutError:
                logger.warning("EventBus stop timed out")

        self._started = False

    @property
    def base_url(self) -> str:
        """Get the base URL for the test server"""
        return f"http://{self.host}:{self.port}"

    async def get(self, path: str = "/") -> httpx.Response:
        """Make a GET request to the server"""
        async with httpx.AsyncClient() as client:
            return await client.get(f"{self.base_url}{path}")

    async def post(self, path: str, **kwargs: Any) -> httpx.Response:
        """Make a POST request to the server"""
        async with httpx.AsyncClient() as client:
            return await client.post(f"{self.base_url}{path}", **kwargs)


def create_test_server(
    host: str = "127.0.0.1",
    port: int = 8899,
    reload: bool = False,
    **kwargs: Any,
) -> PantainosTestServer:
    """Create a test server instance"""
    return PantainosTestServer(
        host=host,
        port=port,
        reload=reload,
        **kwargs,
    )
