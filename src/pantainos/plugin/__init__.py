"""
Plugin system for Pantainos
"""

from .base import Plugin
from .manager import PluginRegistry

__all__ = ["Plugin", "PluginRegistry"]
