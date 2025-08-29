"""
Test suite for the unified theme and design system.
"""

from unittest.mock import MagicMock, patch

# Mock NiceGUI before import
with patch.dict("sys.modules", {"nicegui": MagicMock(), "nicegui.events": MagicMock()}):
    from pantainos.web.components.theme import ThemeConfig, ThemeManager


def test_theme_config_has_default_colors():
    """Test that ThemeConfig has default color palette."""
    config = ThemeConfig()

    # Primary colors
    assert config.primary is not None
    assert config.secondary is not None
    assert config.accent is not None

    # Neutral colors
    assert config.background is not None
    assert config.surface is not None
    assert config.text_primary is not None
    assert config.text_secondary is not None

    # Status colors
    assert config.success is not None
    assert config.warning is not None
    assert config.error is not None
    assert config.info is not None


def test_theme_config_has_typography():
    """Test that ThemeConfig includes typography settings."""
    config = ThemeConfig()

    assert config.font_family is not None
    assert config.font_size_base is not None
    assert config.heading_sizes is not None
    assert len(config.heading_sizes) >= 6  # h1-h6


def test_theme_config_has_spacing():
    """Test that ThemeConfig includes spacing system."""
    config = ThemeConfig()

    assert config.spacing is not None
    assert "xs" in config.spacing
    assert "sm" in config.spacing
    assert "md" in config.spacing
    assert "lg" in config.spacing
    assert "xl" in config.spacing


def test_theme_manager_initialization():
    """Test ThemeManager initialization."""
    manager = ThemeManager()

    assert manager.current_theme == "dark"
    assert manager.themes is not None
    assert "dark" in manager.themes
    assert "light" in manager.themes


def test_theme_manager_switch_theme():
    """Test switching between themes."""
    manager = ThemeManager()

    # Start with dark theme
    assert manager.current_theme == "dark"

    # Switch to light theme
    manager.switch_theme("light")
    assert manager.current_theme == "light"

    # Switch back to dark
    manager.switch_theme("dark")
    assert manager.current_theme == "dark"


def test_theme_manager_get_current_config():
    """Test getting current theme configuration."""
    manager = ThemeManager()

    config = manager.get_current_config()
    assert isinstance(config, ThemeConfig)
    assert config.primary is not None


def test_theme_manager_apply_theme():
    """Test applying theme to UI."""
    manager = ThemeManager()

    # Should not raise an error even with mocked UI
    manager.apply_theme()


def test_theme_config_custom_values():
    """Test creating ThemeConfig with custom values."""
    config = ThemeConfig(primary="#FF0000", secondary="#00FF00", font_family="Arial, sans-serif")

    assert config.primary == "#FF0000"
    assert config.secondary == "#00FF00"
    assert config.font_family == "Arial, sans-serif"


def test_theme_manager_register_custom_theme():
    """Test registering a custom theme."""
    manager = ThemeManager()

    custom_config = ThemeConfig(primary="#FF00FF")
    manager.register_theme("custom", custom_config)

    assert "custom" in manager.themes
    manager.switch_theme("custom")
    assert manager.current_theme == "custom"

    config = manager.get_current_config()
    assert config.primary == "#FF00FF"


def test_theme_config_generate_css():
    """Test generating CSS from theme config."""
    config = ThemeConfig()

    css = config.generate_css()
    assert isinstance(css, str)
    assert ":root" in css or ".dark" in css
    assert "--primary" in css or "primary" in css


def test_theme_manager_toggle_theme():
    """Test toggling between dark and light themes."""
    manager = ThemeManager()

    # Start with dark
    assert manager.current_theme == "dark"

    # Toggle to light
    manager.toggle_theme()
    assert manager.current_theme == "light"

    # Toggle back to dark
    manager.toggle_theme()
    assert manager.current_theme == "dark"


def test_theme_config_component_styles():
    """Test that ThemeConfig includes component-specific styles."""
    config = ThemeConfig()

    assert hasattr(config, "button_styles")
    assert hasattr(config, "card_styles")
    assert hasattr(config, "input_styles")
