#!/usr/bin/env python
"""
Complete Stream Bot Example - Demonstrating New Pantainos Architecture

This example showcases the FastAPI-like event-driven architecture with:
- App-bound decorators (@app.on)
- Type-safe event models with conditions
- Plugin mounting and dependency injection
- SQL-like "when" parameter for event filtering
- Cross-plugin interactions

Run with: uv run python examples/stream_bot.py
"""

from __future__ import annotations

import asyncio
import logging

from twitch_plugin import ChatMessage, FollowEvent, RaidEvent, TwitchPlugin

from pantainos import Pantainos

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")


def create_stream_bot() -> Pantainos:
    """Create and configure the stream bot application"""

    # Create the main app with database
    app = Pantainos(database_url="sqlite:///stream_bot.db", debug=True)

    # Mount Twitch plugin with event simulation
    twitch = TwitchPlugin(channel="demo_streamer", simulate_events=True)  # Simulate events for this demo
    app.mount(twitch)

    # === BASIC COMMANDS ===

    @app.on(ChatMessage, when=ChatMessage.command("hello"))
    async def hello_command(event: ChatMessage, twitch: TwitchPlugin) -> None:
        """Simple hello command"""
        await twitch.send_message(f"Hello {event.user}! 👋")

    @app.on(ChatMessage, when=ChatMessage.command("stats"))
    async def stats_command(event: ChatMessage, twitch: TwitchPlugin) -> None:
        """Show user stats"""
        user_info = await twitch.get_user_info(event.user)
        await twitch.send_message(f"{event.user}: {user_info['follower_count']} followers")

    # === MODERATION COMMANDS ===

    @app.on(
        ChatMessage,
        when=(
            ChatMessage.command("timeout")
            & ChatMessage.from_mod()
            & twitch.cooldown(10)  # Plugin-specific cooldown condition
        ),
    )
    async def timeout_command(event: ChatMessage, twitch: TwitchPlugin) -> None:
        """Timeout command (mods only with 10s cooldown)"""
        if not event.command_args:
            await twitch.send_message("Usage: !timeout <username> [duration]")
            return

        username = event.command_args[0]
        duration = int(event.command_args[1]) if len(event.command_args) > 1 else 60

        await twitch.timeout_user(username, duration, "Timeout command")
        await twitch.send_message(f"Timed out {username} for {duration} seconds")

    # === SUBSCRIBER PERKS ===

    @app.on(ChatMessage, when=(ChatMessage.command("song") & (ChatMessage.from_subscriber() | ChatMessage.from_mod())))
    async def song_request(event: ChatMessage, twitch: TwitchPlugin) -> None:
        """Song request (subscribers and mods only)"""
        if not event.command_args:
            await twitch.send_message("Usage: !song <song name>")
            return

        song = " ".join(event.command_args)
        await twitch.send_message(f"🎵 Added '{song}' to queue (requested by {event.user})")

    # === CONTENT FILTERING ===

    @app.on(ChatMessage, when=(ChatMessage.contains_text("spam") & ~ChatMessage.from_mod()))  # NOT a moderator
    async def anti_spam(event: ChatMessage, twitch: TwitchPlugin) -> None:
        """Automatic spam detection"""
        await twitch.timeout_user(event.user, 1, "Spam detected")
        await twitch.send_message(f"⚠️ Message filtered from {event.user}")

    # === EVENT RESPONSES ===

    @app.on(FollowEvent)
    async def new_follower(event: FollowEvent, twitch: TwitchPlugin) -> None:
        """Welcome new followers"""
        await twitch.send_message(f"Welcome {event.user}! Thanks for the follow! 💜")

    @app.on(RaidEvent, when=RaidEvent.min_viewers(10))
    async def raid_response(event: RaidEvent, twitch: TwitchPlugin) -> None:
        """Respond to raids with 10+ viewers"""
        await twitch.send_message(f"🚀 Thank you {event.from_channel} for the raid with {event.viewers} viewers!")

    # === UTILITY COMMANDS ===

    @app.on(ChatMessage, when=ChatMessage.command("uptime"))
    async def uptime_command(_event: ChatMessage, twitch: TwitchPlugin) -> None:
        """Show stream uptime"""
        # In a real bot, this would calculate actual uptime
        await twitch.send_message("Stream has been live for 2 hours 30 minutes")

    @app.on(ChatMessage, when=(ChatMessage.command("help") & twitch.cooldown(30, per_user=False)))  # Global cooldown
    async def help_command(_event: ChatMessage, twitch: TwitchPlugin) -> None:
        """Show available commands"""
        commands = ["!hello", "!stats", "!song", "!uptime", "!help"]
        await twitch.send_message(f"Available commands: {', '.join(commands)}")

    # === ADVANCED PATTERNS ===

    @app.on(
        ChatMessage,
        when=(ChatMessage.from_user("demo_streamer") & ChatMessage.contains_text("!secret")),  # Broadcaster only
    )
    async def broadcaster_command(_event: ChatMessage, twitch: TwitchPlugin) -> None:
        """Special broadcaster-only command"""
        await twitch.send_message("🔒 Broadcaster secret command executed!")

    # Multiple event types with same handler
    @app.on(FollowEvent)
    @app.on(RaidEvent, when=RaidEvent.min_viewers(1))
    async def engagement_tracker(event: FollowEvent | RaidEvent) -> None:
        """Track engagement events"""
        if isinstance(event, FollowEvent):
            print(f"📊 New follower: {event.user}")
        elif isinstance(event, RaidEvent):
            print(f"📊 Raid from: {event.from_channel} ({event.viewers} viewers)")

    # === STRING EVENT EXAMPLES (for comparison) ===

    @app.on("twitch.chat.message", when=lambda e: "bot" in e.data.get("message", "").lower())
    async def bot_mention(event: any) -> None:
        """Example using string event type and lambda condition"""
        print(f"Bot mentioned by: {event.data.get('user', 'unknown')}")

    return app


async def main() -> None:
    """Main function to run the stream bot"""
    print("🤖 Starting Pantainos Stream Bot Demo")
    print("This demo simulates Twitch events to showcase the new architecture")
    print("=" * 60)

    app = create_stream_bot()

    try:
        # Start the application
        await app.start()

        print("✅ Stream bot is running!")
        print("Watch the console for simulated Twitch events...")
        print("Press Ctrl+C to stop")

        # Keep running and processing events
        await asyncio.sleep(30)  # Run for 30 seconds

    except KeyboardInterrupt:
        print("\n🛑 Stopping stream bot...")
    finally:
        await app.stop()
        print("✅ Stream bot stopped cleanly")


if __name__ == "__main__":
    # Example of different ways to run the app

    # Option 1: Using asyncio.run (demonstrated)
    asyncio.run(main())

    # Alternative: app.run() would run forever until Ctrl+C
