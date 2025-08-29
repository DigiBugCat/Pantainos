"""
Example Twitch Plugin Package for Pantainos

This package demonstrates how to create a Twitch integration plugin
with type-safe events and conditions.
"""

from .events import ChatMessage, FollowEvent, RaidEvent
from .plugin import TwitchPlugin

__all__ = ["ChatMessage", "FollowEvent", "RaidEvent", "TwitchPlugin"]
