"""
Test that shows the specific behavior the page decorator should have
"""

from pantainos.plugin.base import Plugin


class TestPagePlugin(Plugin):
    @property
    def name(self) -> str:
        return "test"


def test_page_decorator_registers_handler():
    """Test that page decorator should register handlers in pages dict"""
    plugin = TestPagePlugin()

    # This will fail until page decorator is implemented
    @plugin.page("dashboard")
    def dashboard_handler():
        return "dashboard content"

    # Should register the handler
    assert "dashboard" in plugin.pages
    assert plugin.pages["dashboard"]["handler"] == dashboard_handler
    assert plugin.pages["dashboard"]["type"] == "page"


def test_page_decorator_empty_route():
    """Test that page decorator works with empty route for main page"""
    plugin = TestPagePlugin()

    # This will fail until page decorator is implemented
    @plugin.page("")
    def main_handler():
        return "main page"

    # Should register with empty string key
    assert "" in plugin.pages
    assert plugin.pages[""]["handler"] == main_handler
