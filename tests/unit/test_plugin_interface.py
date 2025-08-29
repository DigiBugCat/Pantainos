"""
Test Plugin interface according to original design plan
"""

from pantainos import Plugin


class SimplePlugin(Plugin):
    """Simple test plugin following original plan - no version property"""

    @property
    def name(self) -> str:
        return "simple"


def test_plugin_can_be_instantiated_without_version():
    """Plugin should not require version property"""
    # According to original plan, Plugin only requires name property
    plugin = SimplePlugin()
    assert plugin.name == "simple"


def test_plugin_has_emit_method():
    """Plugin should have emit method for sending events"""
    plugin = SimplePlugin()

    # Plugin should have emit method
    assert hasattr(plugin, "emit")
    assert callable(plugin.emit)


def test_plugin_has_mount_hook():
    """Plugin should have _mount method for app integration"""
    plugin = SimplePlugin()

    # Plugin should have _mount method
    assert hasattr(plugin, "_mount")
    assert callable(plugin._mount)


def test_plugin_has_lifecycle_methods():
    """Plugin should have start/stop methods"""
    plugin = SimplePlugin()

    # Plugin should have start and stop methods
    assert hasattr(plugin, "start")
    assert callable(plugin.start)

    assert hasattr(plugin, "stop")
    assert callable(plugin.stop)
