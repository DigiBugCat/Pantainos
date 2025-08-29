"""
Shared test fixtures for the test suite
"""

import asyncio
import tempfile
from pathlib import Path

import pytest

from pantainos.core.di.container import ServiceContainer
from pantainos.core.event_bus import EventBus
from pantainos.db.database import Database


@pytest.fixture
async def test_database():
    """Create a temporary database for testing"""
    with tempfile.TemporaryDirectory() as temp_dir:
        db_path = Path(temp_dir) / "test.db"
        db = Database(db_path)
        await db.initialize()
        yield db
        await db.close()


@pytest.fixture
async def event_bus():
    """Create an EventBus with proper lifecycle management for tests"""
    container = ServiceContainer()
    bus = EventBus(container)

    await bus.start()

    yield bus

    # Use asyncio.wait_for to prevent hanging on stop
    try:
        await asyncio.wait_for(bus.stop(), timeout=5.0)
    except TimeoutError:
        pytest.fail("EventBus.stop() timed out")
