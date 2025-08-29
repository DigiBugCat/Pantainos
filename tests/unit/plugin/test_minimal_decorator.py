"""
Minimal test for Plugin decorator functionality - step by step implementation
"""

from pantainos.plugin.base import Plugin


class MinimalPlugin(Plugin):
    @property
    def name(self) -> str:
        return "minimal"


def test_plugin_needs_page_method():
    """Test that demonstrates Plugin needs a page method"""
    plugin = MinimalPlugin()

    # This should fail because page method doesn't exist yet
    try:
        plugin.page("")
        assert False, "Should have failed - page method doesn't exist"
    except AttributeError as e:
        assert "page" in str(e)
        # Good - this is the expected failure


def test_plugin_needs_api_method():
    """Test that demonstrates Plugin needs an api method"""
    plugin = MinimalPlugin()

    # This should fail because api method doesn't exist yet
    try:
        plugin.api("/test")
        assert False, "Should have failed - api method doesn't exist"
    except AttributeError as e:
        assert "api" in str(e)
        # Good - this is the expected failure
