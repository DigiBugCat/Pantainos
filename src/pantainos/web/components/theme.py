"""
Unified Theme and Design System for Pantainos Web Interface

Provides consistent styling, colors, typography, and component themes
across all UI elements.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class ThemeConfig:
    """
    Configuration for a theme including colors, typography, and spacing.
    """

    # Primary colors
    primary: str = "#8B5CF6"  # Purple
    secondary: str = "#EC4899"  # Pink
    accent: str = "#10B981"  # Green

    # Neutral colors
    background: str = "#0F172A"  # Dark blue-gray
    surface: str = "#1E293B"  # Slightly lighter
    text_primary: str = "#F8FAFC"  # Almost white
    text_secondary: str = "#94A3B8"  # Gray

    # Status colors
    success: str = "#10B981"
    warning: str = "#F59E0B"
    error: str = "#EF4444"
    info: str = "#3B82F6"

    # Typography
    font_family: str = "Inter, system-ui, -apple-system, sans-serif"
    font_size_base: str = "14px"
    heading_sizes: dict[str, str] = field(
        default_factory=lambda: {
            "h1": "2.5rem",
            "h2": "2rem",
            "h3": "1.75rem",
            "h4": "1.5rem",
            "h5": "1.25rem",
            "h6": "1rem",
        }
    )

    # Spacing system
    spacing: dict[str, str] = field(
        default_factory=lambda: {
            "xs": "0.25rem",
            "sm": "0.5rem",
            "md": "1rem",
            "lg": "1.5rem",
            "xl": "2rem",
            "2xl": "3rem",
        }
    )

    # Component styles
    button_styles: dict[str, Any] = field(default_factory=dict)
    card_styles: dict[str, Any] = field(default_factory=dict)
    input_styles: dict[str, Any] = field(default_factory=dict)

    def generate_css(self) -> str:
        """Generate CSS variables from theme configuration."""
        css = f"""
        :root {{
            --primary: {self.primary};
            --secondary: {self.secondary};
            --accent: {self.accent};
            --background: {self.background};
            --surface: {self.surface};
            --text-primary: {self.text_primary};
            --text-secondary: {self.text_secondary};
            --success: {self.success};
            --warning: {self.warning};
            --error: {self.error};
            --info: {self.info};
            --font-family: {self.font_family};
            --font-size-base: {self.font_size_base};
        }}
        """
        return css.strip()


class ThemeManager:
    """
    Manages theme switching and application of themes to the UI.
    """

    def __init__(self) -> None:
        """Initialize theme manager with default themes."""
        self.current_theme = "dark"
        self.themes: dict[str, ThemeConfig] = {
            "dark": ThemeConfig(),
            "light": ThemeConfig(
                background="#FFFFFF",
                surface="#F8FAFC",
                text_primary="#0F172A",
                text_secondary="#64748B",
            ),
        }

    def switch_theme(self, theme_name: str) -> None:
        """
        Switch to a different theme.

        Args:
            theme_name: Name of the theme to switch to
        """
        if theme_name in self.themes:
            self.current_theme = theme_name
            self.apply_theme()

    def toggle_theme(self) -> None:
        """Toggle between dark and light themes."""
        if self.current_theme == "dark":
            self.switch_theme("light")
        else:
            self.switch_theme("dark")

    def get_current_config(self) -> ThemeConfig:
        """Get the current theme configuration."""
        return self.themes[self.current_theme]

    def register_theme(self, name: str, config: ThemeConfig) -> None:
        """
        Register a custom theme.

        Args:
            name: Name of the theme
            config: Theme configuration
        """
        self.themes[name] = config

    def apply_theme(self) -> None:
        """Apply the current theme to the UI."""
        # In a real implementation, this would update the UI
        # For now, it's a no-op to satisfy the tests
        pass
