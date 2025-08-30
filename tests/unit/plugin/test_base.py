"""
Tests for Plugin base class (src/pantainos/plugin/base.py)
"""

from pantainos.plugin.base import HealthCheck, Plugin


class SimpleTestPlugin(Plugin):
    """Test plugin implementation for testing"""

    @property
    def name(self) -> str:
        return "test"

    async def health_check(self) -> HealthCheck:
        """Simple healthy status for testing"""
        return HealthCheck.healthy("Test plugin is healthy")


def test_plugin_can_be_instantiated_with_only_name():
    """Plugin should only require name property, not version"""
    # This should work now that version is removed
    plugin = SimpleTestPlugin()
    assert plugin.name == "test"


def test_plugin_needs_emit_method():
    """Plugin should have emit method for sending events"""
    plugin = SimpleTestPlugin()

    # Plugin should have emit method
    assert hasattr(plugin, "emit"), "Plugin missing emit method"
    assert callable(plugin.emit), "emit should be callable"


def test_plugin_needs_mount_hook():
    """Plugin should have _mount method for app integration"""
    plugin = SimpleTestPlugin()

    # Plugin should have _mount method
    assert hasattr(plugin, "_mount"), "Plugin missing _mount method"
    assert callable(plugin._mount), "_mount should be callable"


def test_plugin_needs_lifecycle_methods():
    """Plugin should have start/stop lifecycle methods"""
    plugin = SimpleTestPlugin()

    # Plugin should have start and stop methods
    assert hasattr(plugin, "start"), "Plugin missing start method"
    assert callable(plugin.start), "start should be callable"

    assert hasattr(plugin, "stop"), "Plugin missing stop method"
    assert callable(plugin.stop), "stop should be callable"
