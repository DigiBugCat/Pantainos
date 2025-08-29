"""
Simple test showing WebServer import is needed in application module
"""


def test_webserver_import_available():
    """Test that WebServer can be imported from pantainos.application"""
    # This will fail until WebServer is imported in application.py
    from pantainos.application import WebServer

    assert WebServer is not None
