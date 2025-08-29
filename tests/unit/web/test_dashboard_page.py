"""
Test for DashboardHub page creation
"""

from unittest.mock import MagicMock


def test_dashboard_hub_has_create_dashboard_method():
    """Test that DashboardHub has create_dashboard method"""
    from pantainos.web.dashboard import DashboardHub

    # Mock the Pantainos app
    app = MagicMock()
    app.event_bus = MagicMock()
    app.plugins = {}

    dashboard = DashboardHub(app)

    # Should have create_dashboard method
    assert hasattr(dashboard, "create_dashboard")
    assert callable(dashboard.create_dashboard)


def test_create_dashboard_can_be_called():
    """Test that create_dashboard method can be called"""
    from pantainos.web.dashboard import DashboardHub

    # Mock the Pantainos app
    app = MagicMock()
    app.event_bus = MagicMock()
    app.plugins = {}

    dashboard = DashboardHub(app)

    # Should be able to call create_dashboard
    dashboard.create_dashboard()
