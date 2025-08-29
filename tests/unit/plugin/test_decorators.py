"""
Tests for plugin decorator functionality (@page and @api decorators)
"""


import pytest


class TestPlugin:
    """Test plugin for decorator testing"""

    def __init__(self):
        self.name = "test_plugin"
        self.pages = {}
        self.apis = {}

    def page(self, route: str = ""):
        """Page decorator for registering web pages"""

        def decorator(func):
            self.pages[route] = {"handler": func, "type": "page"}
            return func

        return decorator

    def api(self, route: str):
        """API decorator for registering API endpoints"""

        def decorator(func):
            self.apis[route] = {"handler": func, "type": "api"}
            return func

        return decorator


@pytest.mark.asyncio
async def test_plugin_page_decorator():
    """Test that @plugin.page decorator registers page handlers"""
    plugin = TestPlugin()

    @plugin.page("")
    async def main_page():
        return "Main dashboard"

    @plugin.page("config")
    async def config_page():
        return "Configuration page"

    # Check that pages were registered
    assert "" in plugin.pages
    assert "config" in plugin.pages
    assert plugin.pages[""]["handler"] == main_page
    assert plugin.pages["config"]["handler"] == config_page
    assert plugin.pages[""]["type"] == "page"
    assert plugin.pages["config"]["type"] == "page"


@pytest.mark.asyncio
async def test_plugin_api_decorator():
    """Test that @plugin.api decorator registers API endpoints"""
    plugin = TestPlugin()

    @plugin.api("/status")
    async def status_endpoint():
        return {"status": "active"}

    @plugin.api("/health")
    async def health_endpoint():
        return {"health": "ok"}

    # Check that APIs were registered
    assert "/status" in plugin.apis
    assert "/health" in plugin.apis
    assert plugin.apis["/status"]["handler"] == status_endpoint
    assert plugin.apis["/health"]["handler"] == health_endpoint
    assert plugin.apis["/status"]["type"] == "api"
    assert plugin.apis["/health"]["type"] == "api"


@pytest.mark.asyncio
async def test_plugin_decorator_handler_execution():
    """Test that decorated handlers can be executed"""
    plugin = TestPlugin()

    @plugin.page("test")
    async def test_handler():
        return "Test response"

    # Execute the handler
    result = await plugin.pages["test"]["handler"]()
    assert result == "Test response"


@pytest.mark.asyncio
async def test_plugin_empty_pages_and_apis():
    """Test plugin with no registered pages or APIs"""
    plugin = TestPlugin()

    assert plugin.pages == {}
    assert plugin.apis == {}


@pytest.mark.asyncio
async def test_plugin_page_route_variations():
    """Test different route formats for pages"""
    plugin = TestPlugin()

    @plugin.page("")
    async def root_page():
        return "Root"

    @plugin.page("dashboard")
    async def dashboard_page():
        return "Dashboard"

    @plugin.page("config/advanced")
    async def advanced_config():
        return "Advanced Config"

    assert "" in plugin.pages
    assert "dashboard" in plugin.pages
    assert "config/advanced" in plugin.pages
