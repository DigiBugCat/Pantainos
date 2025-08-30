# Pantainos

**Python 3.11+** | **GNU GPLv3**

Opinionated glue for event-driven systems. FastAPI-inspired patterns for connecting things that emit events.

## Philosophy

**Make the common case trivial, the complex case possible.**

- No config files, just code
- Everything is an event
- Plugins are just things that emit and receive events
- Type hints everywhere, IDE autocomplete works
- Async-first, no sync fallbacks

## Quick Start

```python
from pantainos import Pantainos

app = Pantainos()

@app.on("user.action")
async def handle_action(event):
    print(f"User did: {event.data}")

@app.on(Interval.every_minutes(5))
async def periodic_task():
    await app.emit("timer.tick", {"time": "now"})

app.run()
```

## What Actually Works

### Core Application
FastAPI-like decorators for event handling:
```python
app = Pantainos(database_url="sqlite:///app.db")

# String events
@app.on("message.received")
async def handler(event): ...

# Typed events with conditions
@app.on(ChatMessage, when=ChatMessage.command("!hello"))
async def hello_command(event: ChatMessage): ...

# Scheduled events
@app.on(Cron("0 9 * * *"))  # Daily at 9am
async def morning_task(): ...
```

### Event Models
Pydantic-based events with type-safe conditions:
```python
from pantainos.events import EventModel

class UserEvent(EventModel):
    event_type = "user.action"
    username: str
    action: str

    @classmethod
    def is_admin(cls):
        return cls.condition(lambda e: e.username == "admin")
```

### Plugins
Self-contained modules that extend functionality:
```python
from pantainos import Plugin

class MyPlugin(Plugin):
    @property
    def name(self) -> str:
        return "my-plugin"

    async def health_check(self):
        return HealthCheck.healthy("All good")

app.mount(MyPlugin())
```

### Dependency Injection
Automatic injection into handlers:
```python
from pantainos.db.repositories import VariableRepository

@app.on("user.login")
async def track_login(event, vars: VariableRepository):
    count = await vars.get("login_count", default=0)
    await vars.set("login_count", count + 1)
```

### Scheduler
Three types of scheduled tasks:
```python
# Fixed intervals
@app.on(Interval.every_seconds(30))

# Cron expressions
@app.on(Cron("*/5 * * * *"))

# File watching
@app.on(Watch("/path/to/file"))
```

### Database
Simple SQLite with repositories (no ORM):
- `VariableRepository` - Key-value storage (persistent or session)
- `EventRepository` - Event logging and history
- `SecureStorageRepository` - Encrypted credential storage

### Conditions
Composable event filters:
```python
@app.on("message",
    when=has_role("mod") & (command("!ban") | command("!kick")))
```

## Installation

```bash
pip install pantainos
```

## Example: Simple Bot

```python
from pantainos import Pantainos
from pantainos.events import EventModel

class Message(EventModel):
    event_type = "message"
    user: str
    text: str

    @classmethod
    def command(cls, cmd: str):
        return cls.condition(
            lambda e: e.text.startswith(cmd)
        )

app = Pantainos()

@app.on(Message, when=Message.command("!hello"))
async def hello(event: Message):
    print(f"Hello {event.user}!")

# In practice, a plugin would emit these events
await app.emit(Message(user="alice", text="!hello world"))
```

## Goals

Built to be the glue between services like Discord, Twitch, webhooks, and more. Each integration would be a plugin that translates platform events into Pantainos events.

## Development

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Format code
black . && ruff check --fix .
```

## License

GNU GPLv3
