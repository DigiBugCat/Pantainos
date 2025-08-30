#!/usr/bin/env python
"""
Minimal hello world example using Pantainos
"""

import asyncio

from pantainos import Pantainos
from pantainos.events import GenericEvent


def create_hello_world_app() -> Pantainos:
    """Create and configure the hello world application"""

    # Create the main app
    app: Pantainos = Pantainos(database_url="sqlite:///:memory:", debug=True)  # In-memory database for minimal example

    @app.on("hello")
    async def say_hello(event: GenericEvent) -> None:
        """Handle hello events"""
        name = event.data.get("name", "World")
        print(f"Hello, {name}!")

    @app.on("timer.tick")
    async def periodic_greeting(_event: GenericEvent) -> None:
        """Handle periodic timer events"""
        print("👋 Periodic greeting from Pantainos!")

    return app


if __name__ == "__main__":

    async def main() -> None:
        print("🌟 Minimal Pantainos Hello World Example")

        app = create_hello_world_app()
        await app.start()

        # Emit a hello event
        await app.emit("hello", {"name": "Pantainos"})

        # Emit a timer tick event
        await app.emit("timer.tick", {})

        await asyncio.sleep(0.1)
        await app.stop()
        print("✅ Hello World example completed")

    asyncio.run(main())
