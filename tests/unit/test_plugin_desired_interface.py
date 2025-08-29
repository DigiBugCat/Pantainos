"""
Tests for desired Plugin interface based on original plan
"""

import pytest

from pantainos import Pantainos


def test_plugin_should_work_like_twitch_example():
    """Test that Plugin interface should match our TwitchPlugin example"""

    # This is what TwitchPlugin looks like in our examples
    # It should work but currently fails due to wrong Plugin interface
    from examples.twitch_plugin import TwitchPlugin

    # This should work - no version property required
    plugin = TwitchPlugin(channel="test", simulate_events=False)

    # Plugin should have name property
    assert plugin.name == "twitch"

    # Plugin should have emit method for sending events
    assert hasattr(plugin, "emit"), "Plugin should have emit method"

    # Plugin should have _mount method for app integration
    assert hasattr(plugin, "_mount"), "Plugin should have _mount method"

    # Plugin should have start/stop lifecycle methods
    assert hasattr(plugin, "start"), "Plugin should have start method"
    assert hasattr(plugin, "stop"), "Plugin should have stop method"


@pytest.mark.asyncio
async def test_plugin_emit_integration():
    """Test that plugins can emit events through the app"""

    from examples.twitch_plugin import TwitchPlugin

    app = Pantainos()
    plugin = TwitchPlugin(channel="test", simulate_events=False)

    # Mount plugin
    app.mount(plugin)

    # Plugin should be able to emit events
    await plugin.emit("test.event", {"message": "hello"})


@pytest.mark.asyncio
async def test_plugin_lifecycle_integration():
    """Test plugin lifecycle with app start/stop"""

    from examples.twitch_plugin import TwitchPlugin

    app = Pantainos(database_url=":memory:")
    plugin = TwitchPlugin(channel="test", simulate_events=False)

    # Mount plugin
    app.mount(plugin)

    # Mock database initialization to avoid file system
    from unittest.mock import AsyncMock

    app._initialize_database = AsyncMock()

    # Should start successfully and call plugin.start()
    await app.start()

    # Should stop successfully and call plugin.stop()
    await app.stop()
