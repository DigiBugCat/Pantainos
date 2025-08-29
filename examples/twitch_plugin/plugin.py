"""
Twitch Plugin Implementation - Example External Plugin

This module demonstrates how to create a plugin that connects to external
services (Twitch in this case) and emits typed events with conditions.
"""

from __future__ import annotations

import asyncio
import contextlib
import logging
import time

from pantainos import Condition, Plugin

from .events import ChatMessage

logger = logging.getLogger(__name__)


class TwitchPlugin(Plugin):
    """
    Example Twitch plugin that demonstrates the new plugin architecture.

    This plugin would normally use a real Twitch client library like twitchio,
    but for this example we'll simulate events to demonstrate the patterns.

    Example usage:
        app = Pantainos()
        twitch = TwitchPlugin(channel="my_channel", token="oauth:token")
        app.mount(twitch)

        @app.on(ChatMessage, when=ChatMessage.command("hello"))
        async def hello_cmd(event: ChatMessage, twitch: TwitchPlugin):
            await twitch.send_message(f"Hello {event.user}!")
    """

    name = "twitch"

    def __init__(
        self, channel: str, token: str | None = None, client_id: str | None = None, simulate_events: bool = False
    ) -> None:
        """
        Initialize Twitch plugin.

        Args:
            channel: Twitch channel to connect to
            token: OAuth token for authentication
            client_id: Twitch application client ID
            simulate_events: If True, simulate events for testing
        """
        super().__init__()
        self.channel = channel
        self.token = token
        self.client_id = client_id
        self.simulate_events = simulate_events

        # Connection state
        self.connected = False
        self.simulation_task: asyncio.Task | None = None

        # Cooldown tracking for plugin-specific conditions
        self._user_cooldowns: dict[str, dict[str, float]] = {}

        # Mock client for demonstration
        self.client = None  # Would be twitchio.Client in real implementation

    async def start(self) -> None:
        """Start the Twitch plugin connection"""
        logger.info(f"Starting Twitch plugin for channel: {self.channel}")

        if self.simulate_events:
            # Start event simulation for testing
            self.simulation_task = asyncio.create_task(self._simulate_events())
            logger.info("Event simulation started")
        else:
            # In a real implementation, connect to Twitch
            # self.client = twitchio.Client(token=self.token)
            # await self.client.connect()
            logger.info("Real Twitch connection would be established here")

        self.connected = True
        logger.info("Twitch plugin started successfully")

    async def stop(self) -> None:
        """Stop the Twitch plugin connection"""
        logger.info("Stopping Twitch plugin")

        self.connected = False

        if self.simulation_task:
            self.simulation_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self.simulation_task

        if self.client:
            # In real implementation: await self.client.close()
            pass

        logger.info("Twitch plugin stopped")

    # Plugin-specific conditions that use plugin state
    def cooldown(self, seconds: int, per_user: bool = True) -> Condition[ChatMessage]:
        """
        Create a cooldown condition that tracks state in the plugin.

        Args:
            seconds: Cooldown duration in seconds
            per_user: If True, cooldown is per-user. If False, global cooldown.

        Returns:
            Condition that checks cooldown state
        """

        def check(event: ChatMessage) -> bool:
            now = time.time()

            if per_user:
                # Per-user cooldown
                user_cooldowns = self._user_cooldowns.setdefault(event.user, {})
                key = f"cooldown_{seconds}"

                last_used = user_cooldowns.get(key, 0)
                if now - last_used < seconds:
                    return False

                user_cooldowns[key] = now
                return True
            # Global cooldown
            global_key = f"global_cooldown_{seconds}"
            global_cooldowns = self._user_cooldowns.setdefault("__global__", {})

            last_used = global_cooldowns.get(global_key, 0)
            if now - last_used < seconds:
                return False

            global_cooldowns[global_key] = now
            return True

        cooldown_type = "per_user" if per_user else "global"
        return Condition[ChatMessage](check, f"cooldown({seconds}s, {cooldown_type})")

    def require_permission(self, level: str) -> Condition[ChatMessage]:
        """
        Create a condition that checks user permissions.

        Args:
            level: Permission level ("mod", "subscriber", "vip", etc.)
        """

        def check(event: ChatMessage) -> bool:
            if level == "mod":
                return event.is_mod or "moderator" in event.badges
            if level == "subscriber":
                return event.is_subscriber or "subscriber" in event.badges
            if level == "vip":
                return "vip" in event.badges
            if level == "broadcaster":
                return event.user.lower() == self.channel.lower()
            return False

        return Condition[ChatMessage](check, f"require_permission({level})")

    # Service methods that can be injected into handlers
    async def send_message(self, message: str, channel: str | None = None) -> None:
        """
        Send a message to Twitch chat.

        Args:
            message: Message to send
            channel: Channel to send to (defaults to plugin's channel)
        """
        target_channel = channel or self.channel

        if self.simulate_events:
            logger.info(f"[SIMULATED] Sending to {target_channel}: {message}")
        else:
            # In real implementation: await self.client.get_channel(target_channel).send(message)
            logger.info(f"Would send to {target_channel}: {message}")

    async def timeout_user(self, username: str, duration: int, reason: str = "") -> None:
        """
        Timeout a user in chat.

        Args:
            username: User to timeout
            duration: Timeout duration in seconds
            reason: Optional reason for timeout
        """
        if self.simulate_events:
            logger.info(f"[SIMULATED] Timing out {username} for {duration}s: {reason}")
        else:
            # In real implementation: use Twitch API to timeout user
            logger.info(f"Would timeout {username} for {duration}s: {reason}")

    async def get_user_info(self, username: str) -> dict[str, any]:
        """
        Get information about a user.

        Args:
            username: Username to look up

        Returns:
            Dictionary with user information
        """
        # In real implementation: call Twitch API
        return {
            "id": "123456",
            "username": username,
            "display_name": username.title(),
            "is_partner": False,
            "follower_count": 42,
        }

    # Event simulation for testing
    async def _simulate_events(self) -> None:
        """Simulate Twitch events for testing purposes"""
        sample_messages = [
            {"user": "alice", "message": "!hello world", "badges": ["subscriber"]},
            {"user": "bob", "message": "!stats", "badges": ["moderator"]},
            {"user": "charlie", "message": "just chatting here", "badges": []},
            {"user": "dana", "message": "!help me please", "badges": ["vip"]},
        ]

        sample_follows = [
            {"user": "new_follower_1"},
            {"user": "new_follower_2"},
        ]

        sample_raids = [
            {"from_channel": "friendly_streamer", "viewers": 25},
            {"from_channel": "big_streamer", "viewers": 150},
        ]

        event_count = 0

        while self.connected:
            try:
                # Simulate chat messages
                if event_count % 3 == 0:
                    msg_data = sample_messages[event_count % len(sample_messages)]
                    await self.emit(
                        "chat.message",
                        {
                            **msg_data,
                            "channel": self.channel,
                            "is_mod": "moderator" in msg_data["badges"],
                            "is_subscriber": "subscriber" in msg_data["badges"],
                        },
                    )

                # Simulate follows occasionally
                elif event_count % 10 == 5:
                    follow_data = sample_follows[event_count % len(sample_follows)]
                    await self.emit("follow", {**follow_data, "channel": self.channel})

                # Simulate raids rarely
                elif event_count % 20 == 15:
                    raid_data = sample_raids[event_count % len(sample_raids)]
                    await self.emit("raid", {**raid_data, "to_channel": self.channel})

                event_count += 1
                await asyncio.sleep(2)  # Emit events every 2 seconds

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in event simulation: {e}")
                await asyncio.sleep(1)
