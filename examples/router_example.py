#!/usr/bin/env python
"""
Router Example - Demonstrating FastAPI-like Router Pattern

This example shows how to organize handlers using routers, similar to
FastAPI's router pattern for organizing endpoints.

Run with: uv run python examples/router_example.py
"""

from __future__ import annotations

import asyncio
import logging

from twitch_plugin import ChatMessage, FollowEvent, RaidEvent, TwitchPlugin

from pantainos import Pantainos, Router

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")

# === CHAT COMMAND ROUTER ===

# Create a router for chat commands
chat_router = Router(prefix="chat")


@chat_router.on(ChatMessage, when=ChatMessage.command("hello"))
async def hello_command(event: ChatMessage, twitch: TwitchPlugin) -> None:
    """Simple hello command"""
    await twitch.send_message(f"Hello {event.user}! 👋")


@chat_router.on(ChatMessage, when=ChatMessage.command("stats"))
async def stats_command(event: ChatMessage, twitch: TwitchPlugin) -> None:
    """Show user stats"""
    user_info = await twitch.get_user_info(event.user)
    await twitch.send_message(f"{event.user}: {user_info['follower_count']} followers")


@chat_router.on(ChatMessage, when=ChatMessage.command("help"))
async def help_command(_event: ChatMessage, twitch: TwitchPlugin) -> None:
    """Show available commands"""
    commands = ["!hello", "!stats", "!help", "!song"]
    await twitch.send_message(f"Available commands: {', '.join(commands)}")


# === MODERATION ROUTER ===

# Create a router for moderation commands
mod_router = Router(prefix="moderation")


@mod_router.on(
    ChatMessage,
    when=(
        ChatMessage.command("timeout")
        & ChatMessage.from_mod()
        # Plugin-specific cooldown would be added via TwitchPlugin dependency
    ),
)
async def timeout_command(event: ChatMessage, twitch: TwitchPlugin) -> None:
    """Timeout command (mods only)"""
    if not event.command_args:
        await twitch.send_message("Usage: !timeout <username> [duration]")
        return

    username = event.command_args[0]
    duration = int(event.command_args[1]) if len(event.command_args) > 1 else 60

    await twitch.timeout_user(username, duration, "Timeout command")
    await twitch.send_message(f"Timed out {username} for {duration} seconds")


@mod_router.on(ChatMessage, when=(ChatMessage.contains_text("spam") & ~ChatMessage.from_mod()))
async def anti_spam(event: ChatMessage, twitch: TwitchPlugin) -> None:
    """Automatic spam detection"""
    await twitch.timeout_user(event.user, 1, "Spam detected")
    await twitch.send_message(f"⚠️ Message filtered from {event.user}")


# === SUBSCRIBER PERKS ROUTER ===

# Create a router for subscriber features
subscriber_router = Router(prefix="vip")


@subscriber_router.on(
    ChatMessage, when=(ChatMessage.command("song") & (ChatMessage.from_subscriber() | ChatMessage.from_mod()))
)
async def song_request(event: ChatMessage, twitch: TwitchPlugin) -> None:
    """Song request (subscribers and mods only)"""
    if not event.command_args:
        await twitch.send_message("Usage: !song <song name>")
        return

    song = " ".join(event.command_args)
    await twitch.send_message(f"🎵 Added '{song}' to queue (requested by {event.user})")


# === EVENT RESPONSE ROUTER ===

# Create a router for handling Twitch events
events_router = Router(prefix="events")


@events_router.on(FollowEvent)
async def new_follower(event: FollowEvent, twitch: TwitchPlugin) -> None:
    """Welcome new followers"""
    await twitch.send_message(f"Welcome {event.user}! Thanks for the follow! 💜")


@events_router.on(RaidEvent, when=RaidEvent.min_viewers(10))
async def raid_response(event: RaidEvent, twitch: TwitchPlugin) -> None:
    """Respond to raids with 10+ viewers"""
    await twitch.send_message(f"🚀 Thank you {event.from_channel} for the raid with {event.viewers} viewers!")


# === NESTED ROUTER EXAMPLE ===

# Create a main moderator router that includes sub-routers
main_mod_router = Router(prefix="moderation")

# Create specialized moderation routers
timeout_router = Router()


@timeout_router.on(ChatMessage, when=(ChatMessage.command("ban") & ChatMessage.from_mod()))
async def ban_command(event: ChatMessage, twitch: TwitchPlugin) -> None:
    """Ban command"""
    if not event.command_args:
        await twitch.send_message("Usage: !ban <username>")
        return
    username = event.command_args[0]
    await twitch.send_message(f"Banned {username}")


# Include the timeout router in the main moderation router
main_mod_router.include_router(timeout_router, prefix="advanced")


def create_router_demo() -> Pantainos:
    """Create and configure the router demo application"""

    # Create the main app
    app = Pantainos(database_url="sqlite:///router_demo.db", debug=True)

    # Mount Twitch plugin
    twitch = TwitchPlugin(channel="demo_streamer", simulate_events=True)
    app.mount(twitch)

    # Include all routers in the main app
    app.include_router(chat_router)  # Handlers get "chat." prefix
    app.include_router(mod_router)  # Handlers get "moderation." prefix
    app.include_router(subscriber_router)  # Handlers get "vip." prefix
    app.include_router(events_router)  # Handlers get "events." prefix
    app.include_router(main_mod_router)  # Demonstrates nested routers

    # You can also add handlers directly to the app
    @app.on("system.startup")
    async def startup_handler(_event: any) -> None:
        """Handle system startup"""
        print("🚀 Router demo system started!")

    return app


async def main() -> None:
    """Main function to run the router demo"""
    print("🤖 Starting Pantainos Router Demo")
    print("This demo shows how to organize handlers using FastAPI-like routers")
    print("==" * 40)

    app = create_router_demo()

    try:
        # Emit a startup event to test app-level handlers
        await app.emit("system.startup", {})

        # Start the application
        await app.start()

        print("✅ Router demo is running!")
        print("Watch the console for simulated Twitch events organized by routers...")
        print("Press Ctrl+C to stop")

        # Run for 30 seconds to see the organized events
        await asyncio.sleep(30)

    except KeyboardInterrupt:
        print("\n🛑 Stopping router demo...")
    finally:
        await app.stop()
        print("✅ Router demo stopped cleanly")

        # Show summary of registered handlers
        print("\n📊 Demo Summary:")
        print(f"   - Registered {len(app.routers)} routers")
        print(f"   - Total event types: {len(app.event_bus.handlers)}")
        for event_type, handlers in app.event_bus.handlers.items():
            print(f"     • {event_type}: {len(handlers)} handler(s)")


if __name__ == "__main__":
    # Run the router demo
    asyncio.run(main())
