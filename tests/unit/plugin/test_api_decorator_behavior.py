"""
Test that shows the specific behavior the api decorator should have
"""

from pantainos.plugin.base import Plugin


class TestApiPlugin(Plugin):
    @property
    def name(self) -> str:
        return "test"


def test_api_decorator_registers_handler():
    """Test that api decorator should register handlers in apis dict"""
    plugin = TestApiPlugin()

    # This will fail until api decorator is implemented
    @plugin.api("/status")
    def status_handler():
        return {"status": "active"}

    # Should register the handler
    assert "/status" in plugin.apis
    assert plugin.apis["/status"]["handler"] == status_handler
    assert plugin.apis["/status"]["type"] == "api"


def test_api_decorator_multiple_endpoints():
    """Test that api decorator works with multiple endpoints"""
    plugin = TestApiPlugin()

    # This will fail until api decorator is implemented
    @plugin.api("/health")
    def health_handler():
        return {"health": "ok"}

    @plugin.api("/version")
    def version_handler():
        return {"version": "1.0.0"}

    # Should register both handlers
    assert "/health" in plugin.apis
    assert "/version" in plugin.apis
    assert plugin.apis["/health"]["handler"] == health_handler
    assert plugin.apis["/version"]["handler"] == version_handler
