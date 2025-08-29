"""Tests for Plugin decorator registration"""

from pantainos.plugin.base import Plugin


class MinimalPlugin(Plugin):
    @property
    def name(self) -> str:
        return "minimal"


def test_plugin_page_registration():
    plugin = MinimalPlugin()

    @plugin.page("/")
    def home() -> None:
        pass

    assert "/" in plugin.pages
    assert plugin.pages["/"]["handler"] is home


def test_plugin_api_registration():
    plugin = MinimalPlugin()

    @plugin.api("/test")
    def handler() -> None:
        pass

    assert "/test" in plugin.apis
    assert plugin.apis["/test"]["handler"] is handler
