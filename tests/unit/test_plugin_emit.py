"""
Tests showing current Plugin interface is incompatible with examples
"""

from pantainos import Plugin


def test_current_plugin_requires_version():
    """Test shows current Plugin does NOT require version property"""

    class ExamplePlugin(Plugin):
        """Example plugin like in our demo - should work"""

        @property
        def name(self) -> str:
            return "example"

        # Note: No version property - this should be fine

    # This should work - Plugin does NOT require version
    plugin = ExamplePlugin()
    assert plugin.name == "example"


def test_current_plugin_missing_emit():
    """Test shows current Plugin HAS emit method needed by examples"""

    class WorkingPlugin(Plugin):
        """Plugin that satisfies current interface"""

        @property
        def name(self) -> str:
            return "working"

    plugin = WorkingPlugin()

    # This should exist for plugins to emit events
    assert hasattr(plugin, "emit"), "Current Plugin should have emit method"
    assert callable(plugin.emit), "emit should be callable"


def test_current_plugin_missing_mount_hook():
    """Test shows current Plugin HAS _mount hook needed by app"""

    class WorkingPlugin(Plugin):
        """Plugin that satisfies current interface"""

        @property
        def name(self) -> str:
            return "working"

    plugin = WorkingPlugin()

    # This should exist for apps to mount plugins
    assert hasattr(plugin, "_mount"), "Current Plugin should have _mount method"
    assert callable(plugin._mount), "_mount should be callable"


def test_current_plugin_has_wrong_lifecycle():
    """Test shows current Plugin has correct lifecycle methods - start/stop"""

    class WorkingPlugin(Plugin):
        """Plugin that satisfies current interface"""

        @property
        def name(self) -> str:
            return "working"

    plugin = WorkingPlugin()

    # Current interface should have start/stop (not initialize/shutdown)
    assert hasattr(plugin, "start"), "Current Plugin should have start method"
    assert hasattr(plugin, "stop"), "Current Plugin should have stop method"
    assert callable(plugin.start), "start should be callable"
    assert callable(plugin.stop), "stop should be callable"

    # Should not have old-style lifecycle methods
    assert not hasattr(plugin, "initialize"), "Current Plugin should not have initialize"
    assert not hasattr(plugin, "shutdown"), "Current Plugin should not have shutdown"
