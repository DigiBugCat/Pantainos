"""
Tests for Plugin base class decorator functionality
"""

import pytest

from pantainos.plugin.base import Plugin


class TestPluginImpl(Plugin):
    """Test implementation of Plugin base class"""

    @property
    def name(self) -> str:
        return "test_plugin"


@pytest.mark.asyncio
async def test_plugin_base_has_page_decorator():
    """Test that Plugin base class has page decorator method"""
    plugin = TestPluginImpl()

    # Plugin should have page decorator method
    assert hasattr(plugin, "page")
    assert callable(plugin.page)

    # Should have pages storage
    assert hasattr(plugin, "pages")
    assert isinstance(plugin.pages, dict)


@pytest.mark.asyncio
async def test_plugin_base_has_api_decorator():
    """Test that Plugin base class has api decorator method"""
    plugin = TestPluginImpl()

    # Plugin should have api decorator method
    assert hasattr(plugin, "api")
    assert callable(plugin.api)

    # Should have apis storage
    assert hasattr(plugin, "apis")
    assert isinstance(plugin.apis, dict)


@pytest.mark.asyncio
async def test_plugin_base_page_decorator_usage():
    """Test using page decorator from Plugin base class"""
    plugin = TestPluginImpl()

    @plugin.page("dashboard")
    async def dashboard_handler():
        return "Dashboard content"

    # Page should be registered
    assert "dashboard" in plugin.pages
    assert plugin.pages["dashboard"]["handler"] == dashboard_handler
    assert plugin.pages["dashboard"]["type"] == "page"


@pytest.mark.asyncio
async def test_plugin_base_api_decorator_usage():
    """Test using api decorator from Plugin base class"""
    plugin = TestPluginImpl()

    @plugin.api("/health")
    async def health_handler():
        return {"status": "healthy"}

    # API should be registered
    assert "/health" in plugin.apis
    assert plugin.apis["/health"]["handler"] == health_handler
    assert plugin.apis["/health"]["type"] == "api"


@pytest.mark.asyncio
async def test_plugin_base_empty_pages_apis():
    """Test that new plugin instances start with empty pages and apis"""
    plugin = TestPluginImpl()

    assert plugin.pages == {}
    assert plugin.apis == {}
