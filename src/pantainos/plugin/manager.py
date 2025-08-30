"""
Plugin management utilities for mounting and lifecycle management
"""

import logging
from typing import Any

from pantainos.core.di.container import ServiceContainer

logger = logging.getLogger(__name__)


class PluginRegistry:
    """
    Registry for managing plugin lifecycle and mounting in an application.
    """

    def __init__(self, container: ServiceContainer) -> None:
        """
        Initialize the plugin registry.

        Args:
            container: Service container for dependency injection
        """
        self.plugins: dict[str, Any] = {}
        self.container = container

    def mount(
        self,
        plugin: Any,
        name: str | None = None,
        web_server: Any = None,
    ) -> None:
        """
        Mount a plugin into the application.

        Args:
            plugin: Plugin instance to mount
            name: Optional custom name for the plugin
            web_server: Optional web server for mounting web components

        Raises:
            ValueError: If plugin with the same name is already mounted
        """
        plugin_name = name or getattr(plugin, "name", plugin.__class__.__name__.lower())

        if plugin_name in self.plugins:
            raise ValueError(f"Plugin '{plugin_name}' is already mounted")

        self.plugins[plugin_name] = plugin
        self.container.register_singleton(type(plugin), plugin)

        # Initialize plugin with app context using the Plugin base class API
        # All plugins should inherit from Plugin which provides _mount
        plugin._mount(None)  # Will need to pass app context  # noqa: SLF001

        # Integrate web components if available
        if web_server:
            if hasattr(plugin, "pages"):
                web_server.mount_plugin_pages(plugin)
            if hasattr(plugin, "apis"):
                web_server.mount_plugin_apis(plugin)

        logger.info(f"Mounted plugin: {plugin_name}")

    def get(self, name: str) -> Any | None:
        """Get a plugin by name."""
        return self.plugins.get(name)

    def get_all(self) -> dict[str, Any]:
        """Get all mounted plugins."""
        return self.plugins.copy()

    async def start_all(self) -> None:
        """Start all mounted plugins."""
        for plugin_name, plugin in self.plugins.items():
            if hasattr(plugin, "start"):
                try:
                    await plugin.start()
                    logger.debug(f"Started plugin: {plugin_name}")
                except Exception as e:
                    logger.error(f"Error starting plugin {plugin_name}: {e}")

    async def stop_all(self) -> None:
        """Stop all mounted plugins."""
        for plugin_name, plugin in self.plugins.items():
            if hasattr(plugin, "stop"):
                try:
                    await plugin.stop()
                    logger.debug(f"Stopped plugin: {plugin_name}")
                except Exception as e:
                    logger.error(f"Error stopping plugin {plugin_name}: {e}")

    def is_mounted(self, name: str) -> bool:
        """Check if a plugin is mounted."""
        return name in self.plugins
