"""
Test that demonstrates version property is not required in Plugin
"""

from pantainos import Plugin


def test_plugin_does_not_require_version_property():
    """
    Test that Plugin does not require version property.

    According to design, Plugin only needs name property.
    """

    class MinimalPlugin(Plugin):
        """Plugin following design - only name property"""

        @property
        def name(self) -> str:
            return "minimal"

        # Note: No version property - this is allowed

    # This should work fine
    plugin = MinimalPlugin()
    assert plugin.name == "minimal"


def test_plugin_without_version_works_in_examples():
    """
    Test showing that plugins work without version property.

    Our plugin examples don't need version property.
    """

    # Simulate what our TwitchPlugin looks like
    class ExampleTwitchPlugin(Plugin):
        @property
        def name(self) -> str:
            return "twitch"

        def __init__(self, channel: str):
            super().__init__()
            self.channel = channel

    # This works fine without version
    plugin = ExampleTwitchPlugin("test_channel")
    assert plugin.name == "twitch"
    assert plugin.channel == "test_channel"
