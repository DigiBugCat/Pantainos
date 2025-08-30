#!/usr/bin/env python
"""
Minimal hello world example using Pantainos
"""

from pantainos import Pantainos
from pantainos.events import GenericEvent


def create_hello_world_app() -> Pantainos:
    """Create and configure the hello world application"""

    # Create the main app - webserver always enabled in new ASGI pattern
    app: Pantainos = Pantainos(database_url="sqlite:///:memory:", debug=True)

    @app.on("hello")
    async def say_hello(event: GenericEvent) -> None:
        """Handle hello events"""
        name = event.data.get("name", "World")
        print(f"Hello, {name}!")

    @app.on("timer.tick")
    async def periodic_greeting(_event: GenericEvent) -> None:
        """Handle periodic timer events"""
        print("👋 Periodic greeting from Pantainos!")

    # Startup event handler to emit initial events
    @app.on("system.startup")
    async def on_startup(_event: GenericEvent) -> None:
        """Emit initial events when app starts"""
        await app.emit("hello", {"name": "Pantainos"})
        await app.emit("timer.tick", {})

    return app


# Create app instance at module level for uvicorn reload
app = create_hello_world_app()

if __name__ == "__main__":
    print("🌟 Minimal Pantainos Hello World Example")
    print("🌐 Webserver will be available at http://127.0.0.1:8080")
    print("📡 Try /docs, /ui/docs, /ui/events endpoints")
    print("⏰ Press Ctrl+C to stop")

    # Clean Pantainos pattern - reload auto-detected!
    app.run(host="127.0.0.1", port=8080, reload=True, reload_dirs=["src", "examples"])
