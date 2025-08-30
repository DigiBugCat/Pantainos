"""
Tests for PluginRegistry - Plugin management and lifecycle
"""

from unittest.mock import MagicMock

import pytest

from pantainos.core.di.container import ServiceContainer
from pantainos.plugin.base import HealthCheck, Plugin
from pantainos.plugin.manager import PluginRegistry


class MockPlugin(Plugin):
    """Mock plugin for testing"""

    def __init__(self, name: str = "mock", **config):
        super().__init__(**config)
        self._name = name
        self.started = False
        self.stopped = False
        self.pages = {"index": {"handler": lambda: "home", "type": "page"}}
        self.apis = {"status": {"handler": lambda: {"status": "ok"}, "type": "api"}}

    @property
    def name(self) -> str:
        return self._name

    async def health_check(self) -> HealthCheck:
        return HealthCheck.healthy("Mock plugin is healthy")

    async def start(self) -> None:
        self.started = True

    async def stop(self) -> None:
        self.stopped = True


class MockPluginWithoutLifecycle(Plugin):
    """Mock plugin without start/stop methods"""

    @property
    def name(self) -> str:
        return "simple"

    async def health_check(self) -> HealthCheck:
        return HealthCheck.healthy("Simple plugin is healthy")


class MockPluginThrowsError(Plugin):
    """Mock plugin that throws errors during lifecycle"""

    @property
    def name(self) -> str:
        return "error"

    async def health_check(self) -> HealthCheck:
        return HealthCheck.unhealthy("Error plugin always fails")

    async def start(self) -> None:
        raise Exception("Start error")

    async def stop(self) -> None:
        raise Exception("Stop error")


@pytest.fixture
def mock_container():
    """Create mock ServiceContainer"""
    return MagicMock(spec=ServiceContainer)


@pytest.fixture
def plugin_registry(mock_container):
    """Create PluginRegistry with mocked dependencies"""
    return PluginRegistry(mock_container)


@pytest.fixture
def mock_plugin():
    """Create mock plugin"""
    return MockPlugin()


@pytest.fixture
def mock_web_server():
    """Create mock web server"""
    web_server = MagicMock()
    web_server.mount_plugin_pages = MagicMock()
    web_server.mount_plugin_apis = MagicMock()
    return web_server


def test_plugin_registry_initialization(mock_container):
    """Test PluginRegistry initialization"""
    registry = PluginRegistry(mock_container)

    assert registry.plugins == {}
    assert registry.container == mock_container


def test_mount_plugin_success(plugin_registry, mock_plugin, mock_container):
    """Test mounting a plugin successfully"""
    plugin_registry.mount(mock_plugin)

    assert "mock" in plugin_registry.plugins
    assert plugin_registry.plugins["mock"] == mock_plugin
    mock_container.register_singleton.assert_called_once_with(MockPlugin, mock_plugin)


def test_mount_plugin_with_custom_name(plugin_registry, mock_plugin, mock_container):
    """Test mounting a plugin with custom name"""
    plugin_registry.mount(mock_plugin, name="custom_name")

    assert "custom_name" in plugin_registry.plugins
    assert plugin_registry.plugins["custom_name"] == mock_plugin
    mock_container.register_singleton.assert_called_once_with(MockPlugin, mock_plugin)


def test_mount_plugin_with_web_server(plugin_registry, mock_plugin, mock_web_server):
    """Test mounting a plugin with web server integration"""
    plugin_registry.mount(mock_plugin, web_server=mock_web_server)

    assert "mock" in plugin_registry.plugins
    mock_web_server.mount_plugin_pages.assert_called_once_with(mock_plugin)
    mock_web_server.mount_plugin_apis.assert_called_once_with(mock_plugin)


def test_mount_plugin_without_web_components(plugin_registry, mock_web_server):
    """Test mounting a plugin with empty web components"""
    plugin = MockPluginWithoutLifecycle()
    plugin.pages = {}
    plugin.apis = {}

    plugin_registry.mount(plugin, web_server=mock_web_server)

    assert "simple" in plugin_registry.plugins
    # Plugin has pages/apis attributes, so mount methods are called even if empty
    mock_web_server.mount_plugin_pages.assert_called_once_with(plugin)
    mock_web_server.mount_plugin_apis.assert_called_once_with(plugin)


def test_mount_plugin_duplicate_name_error(plugin_registry, mock_plugin):
    """Test mounting plugins with duplicate names raises error"""
    plugin_registry.mount(mock_plugin)

    another_plugin = MockPlugin(name="mock")
    with pytest.raises(ValueError, match="Plugin 'mock' is already mounted"):
        plugin_registry.mount(another_plugin)


def test_mount_plugin_uses_class_name_fallback(plugin_registry):
    """Test mounting plugin uses class name when no name attribute"""

    class TestPlugin(Plugin):
        @property
        def name(self) -> str:
            return "testplugin"

        async def health_check(self) -> HealthCheck:
            return HealthCheck.healthy("Test")

    plugin = TestPlugin()
    plugin_registry.mount(plugin)

    assert "testplugin" in plugin_registry.plugins


def test_get_plugin_success(plugin_registry, mock_plugin):
    """Test getting a mounted plugin"""
    plugin_registry.mount(mock_plugin)

    result = plugin_registry.get("mock")
    assert result == mock_plugin


def test_get_plugin_not_found(plugin_registry):
    """Test getting non-existent plugin returns None"""
    result = plugin_registry.get("nonexistent")
    assert result is None


def test_get_all_plugins(plugin_registry):
    """Test getting all mounted plugins"""
    plugin1 = MockPlugin(name="plugin1")
    plugin2 = MockPlugin(name="plugin2")

    plugin_registry.mount(plugin1)
    plugin_registry.mount(plugin2)

    all_plugins = plugin_registry.get_all()
    assert len(all_plugins) == 2
    assert all_plugins["plugin1"] == plugin1
    assert all_plugins["plugin2"] == plugin2

    # Should return a copy, not the original dict
    all_plugins["plugin3"] = "test"
    assert "plugin3" not in plugin_registry.plugins


def test_get_all_plugins_empty(plugin_registry):
    """Test getting all plugins when none are mounted"""
    all_plugins = plugin_registry.get_all()
    assert all_plugins == {}


@pytest.mark.asyncio
async def test_start_all_plugins(plugin_registry):
    """Test starting all mounted plugins"""
    plugin1 = MockPlugin(name="plugin1")
    plugin2 = MockPlugin(name="plugin2")
    plugin3 = MockPluginWithoutLifecycle()  # No start method

    plugin_registry.mount(plugin1)
    plugin_registry.mount(plugin2)
    plugin_registry.mount(plugin3)

    await plugin_registry.start_all()

    assert plugin1.started is True
    assert plugin2.started is True
    # plugin3 should not error even without start method


@pytest.mark.asyncio
async def test_start_all_plugins_with_error(plugin_registry, caplog):
    """Test starting plugins when one throws error"""
    plugin1 = MockPlugin(name="plugin1")
    error_plugin = MockPluginThrowsError()
    plugin2 = MockPlugin(name="plugin2")

    plugin_registry.mount(plugin1)
    plugin_registry.mount(error_plugin)
    plugin_registry.mount(plugin2)

    await plugin_registry.start_all()

    # Good plugins should still start
    assert plugin1.started is True
    assert plugin2.started is True

    # Should log error for failing plugin
    assert "Error starting plugin error:" in caplog.text


@pytest.mark.asyncio
async def test_stop_all_plugins(plugin_registry):
    """Test stopping all mounted plugins"""
    plugin1 = MockPlugin(name="plugin1")
    plugin2 = MockPlugin(name="plugin2")
    plugin3 = MockPluginWithoutLifecycle()  # No stop method

    plugin_registry.mount(plugin1)
    plugin_registry.mount(plugin2)
    plugin_registry.mount(plugin3)

    await plugin_registry.stop_all()

    assert plugin1.stopped is True
    assert plugin2.stopped is True
    # plugin3 should not error even without stop method


@pytest.mark.asyncio
async def test_stop_all_plugins_with_error(plugin_registry, caplog):
    """Test stopping plugins when one throws error"""
    plugin1 = MockPlugin(name="plugin1")
    error_plugin = MockPluginThrowsError()
    plugin2 = MockPlugin(name="plugin2")

    plugin_registry.mount(plugin1)
    plugin_registry.mount(error_plugin)
    plugin_registry.mount(plugin2)

    await plugin_registry.stop_all()

    # Good plugins should still stop
    assert plugin1.stopped is True
    assert plugin2.stopped is True

    # Should log error for failing plugin
    assert "Error stopping plugin error:" in caplog.text


def test_is_mounted_true(plugin_registry, mock_plugin):
    """Test is_mounted returns True for mounted plugin"""
    plugin_registry.mount(mock_plugin)

    assert plugin_registry.is_mounted("mock") is True


def test_is_mounted_false(plugin_registry):
    """Test is_mounted returns False for non-mounted plugin"""
    assert plugin_registry.is_mounted("nonexistent") is False


def test_mount_calls_plugin_mount_hook(plugin_registry, mock_plugin):
    """Test mounting calls the plugin's _mount hook"""
    plugin_registry.mount(mock_plugin)

    # Plugin should have app context set (though it's None in this test)
    assert mock_plugin.app is None  # _mount(None) was called


def test_plugin_registry_lifecycle_integration(plugin_registry):
    """Test full plugin lifecycle integration"""
    plugin = MockPlugin(name="lifecycle_test")

    # Mount plugin
    plugin_registry.mount(plugin)
    assert plugin_registry.is_mounted("lifecycle_test")
    assert plugin_registry.get("lifecycle_test") == plugin

    # Plugin should be in all plugins
    all_plugins = plugin_registry.get_all()
    assert "lifecycle_test" in all_plugins


def test_mount_plugin_without_pages_attribute(plugin_registry, mock_web_server):
    """Test mounting plugin without pages attribute doesn't error"""
    plugin = MockPluginWithoutLifecycle()
    delattr(plugin, "pages")  # Remove pages attribute
    delattr(plugin, "apis")  # Remove apis attribute

    # Should not error
    plugin_registry.mount(plugin, web_server=mock_web_server)

    assert "simple" in plugin_registry.plugins
    mock_web_server.mount_plugin_pages.assert_not_called()
    mock_web_server.mount_plugin_apis.assert_not_called()


@pytest.mark.asyncio
async def test_start_stop_empty_registry(plugin_registry):
    """Test starting and stopping when no plugins are mounted"""
    # Should not error
    await plugin_registry.start_all()
    await plugin_registry.stop_all()


def test_plugin_registry_container_integration(plugin_registry, mock_plugin, mock_container):
    """Test plugin registry properly integrates with service container"""
    plugin_registry.mount(mock_plugin)

    # Should register plugin as singleton
    mock_container.register_singleton.assert_called_once_with(MockPlugin, mock_plugin)

    # Should be able to get plugin by name
    assert plugin_registry.get("mock") == mock_plugin
