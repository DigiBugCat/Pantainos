# Pantainos 🏛️

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)

**Pantainos** is a minimal Python framework for building event-driven applications with plugin architecture. Originally designed for streaming automation, it provides a clean foundation for any application that needs event handling, dependency injection, and extensible plugins.

## 🎯 Philosophy

- **Library First**: Import and extend, don't configure
- **Event-Driven**: Everything communicates through events
- **Plugin Architecture**: Extend functionality through plugins
- **Developer Experience**: Type hints, async/await, hot reloading

## 🏗️ Architecture

```
Plugins → Event Bus → Handlers → Database/External Services
```

### Key Components

- **Application**: Base class for your applications
- **Event Bus**: Central event routing with async support
- **Service Container**: Dependency injection system
- **Plugin System**: Extend functionality with plugins
- **Database**: Generic SQLite with repository pattern
- **Triggers**: Composable event filtering

## 🚀 Quick Start

### Installation

```bash
pip install pantainos
```

### Basic Usage

```python
from pantainos import Application, on_event, CommandTrigger, trigger

# Define event handlers
@on_event("message.received")
@trigger(CommandTrigger("!hello"))
async def hello_command(event):
    print(f"Hello {event.data.get('user')}!")

# Create your application
class MyApp(Application):
    def __init__(self):
        super().__init__(database_url="sqlite:///myapp.db")

# Run it
app = MyApp()
app.run()
```

### With Plugins

```python
from pantainos import Application, BasePlugin

class MyPlugin(BasePlugin):
    @property
    def name(self) -> str:
        return "my-plugin"

    @property
    def version(self) -> str:
        return "1.0.0"

    async def initialize(self, app):
        # Setup plugin
        pass

class MyApp(Application):
    def __init__(self):
        super().__init__()
        self.register_plugin(MyPlugin())

app = MyApp()
app.run()
```

## 📚 Examples

### Observability Application

A minimal metrics collection application:

```python
from pantainos import Application, on_event

@on_event("metric.received")
async def process_metric(event):
    print(f"Metric: {event.data}")

app = Application(database_url="sqlite:///metrics.db")
app.run()
```

See `examples/observability/` for a complete implementation.

### Streaming Bot Application

A comprehensive streaming automation application using multiple plugins:

```python
from pantainos import Application
from plugins.twitch import TwitchPlugin
from plugins.obs import OBSPlugin

class StreamingBot(Application):
    def __init__(self):
        super().__init__(database_url="sqlite:///streamer.db")
        self.register_plugin(TwitchPlugin(channel="my_channel"))
        self.register_plugin(OBSPlugin(host="localhost"))

bot = StreamingBot()
bot.run()
```

See `examples/streaming_bot/` for a complete implementation.

## 🧩 Core Features

### Event System

```python
from pantainos import on_event

@on_event("user.joined")
async def welcome_user(event):
    user = event.data.get("user")
    print(f"Welcome {user}!")

# Emit events
await app.event_bus.emit("user.joined", {"user": "alice"})
```

### Triggers

```python
from pantainos import trigger, CommandTrigger, CooldownTrigger

@on_event("chat.message")
@trigger(CommandTrigger("!points"))
@trigger(CooldownTrigger(30))  # 30 second cooldown
async def check_points(event):
    # Handle !points command with cooldown
    pass
```

### Dependency Injection

```python
from pantainos.db.repositories import VariableRepository

@on_event("user.action")
async def handle_action(event, variables: VariableRepository):
    # VariableRepository automatically injected
    await variables.set("last_action", event.data)
```

### Database

```python
from pantainos.db.repositories import EventRepository, VariableRepository

# Event logging
await event_repo.log_event("user.login", {"user": "alice"})

# Key-value storage
await var_repo.set("counter", 42)
value = await var_repo.get("counter", default=0)
```

## 🔌 Plugin Development

Create plugins by extending `BasePlugin`:

```python
from pantainos import BasePlugin, on_event

class WeatherPlugin(BasePlugin):
    @property
    def name(self) -> str:
        return "weather"

    @property
    def version(self) -> str:
        return "1.0.0"

    async def initialize(self, app):
        # Register handlers, setup resources, etc.
        pass

    async def shutdown(self):
        # Cleanup resources
        pass

# Register with application
app.register_plugin(WeatherPlugin())
```

## 📋 Requirements

- Python 3.11+
- aiosqlite
- aiofiles
- click

## 🤝 Contributing

Pantainos is designed to be minimal and focused. Contributions should maintain the library's simplicity while extending functionality through the plugin system.

## 📄 License

MIT License - see LICENSE file for details.

---

**Pantainos** - *A solid foundation for event-driven applications* 🏛️
