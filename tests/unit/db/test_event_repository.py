"""
Tests for EventRepository
"""

import json
import tempfile
from datetime import datetime, timedelta
from pathlib import Path

import pytest

from pantainos.db.database import Database
from pantainos.db.repositories.event_repository import EventRepository


class TestEventRepository:
    """Test EventRepository functionality"""

    @pytest.fixture
    async def setup_repo(self):
        """Create a database and repository for testing"""
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "test_events.db"
            db = Database(db_path)
            await db.initialize()
            repo = EventRepository(db)
            yield repo
            await db.close()

    async def create_test_user(self, repo: EventRepository, user_id: int, twitch_id: str, username: str) -> None:
        """Helper method to create a test user and platform identity"""
        # Create user with new schema (no twitch_id column)
        await repo.db.execute(
            "INSERT INTO users (id, username, display_name) VALUES (?, ?, ?)",
            (user_id, username, username.title()),
        )
        # Create platform identity linking
        await repo.db.execute(
            "INSERT INTO user_identities (user_id, platform, platform_user_id, platform_username, is_primary) VALUES (?, ?, ?, ?, ?)",
            (user_id, "twitch", twitch_id, username, True),
        )
        await repo.db.commit()

    async def test_log_event_success(self, setup_repo):
        """Test that events are correctly inserted into the database"""
        repo = setup_repo

        # Create test user first
        await self.create_test_user(repo, 123, "twitch123", "testuser")

        # Log a simple event
        event_data = {"user": "testuser", "message": "hello world"}
        event_id = await repo.log_event("chat.message", event_data, user_id=123)

        assert isinstance(event_id, int)
        assert event_id > 0

        # Verify event was stored correctly
        event = await repo.get_event_by_id(event_id)
        assert event is not None
        assert event["type"] == "chat.message"
        assert event["user_id"] == 123
        assert event["data"] == event_data

    async def test_log_event_with_user_id(self, setup_repo):
        """Test event logging with user ID association"""
        repo = setup_repo

        # Create test user first
        await self.create_test_user(repo, 456, "twitch456", "follower")

        event_data = {"action": "follow"}
        event_id = await repo.log_event("twitch.follow", event_data, user_id=456)

        event = await repo.get_event_by_id(event_id)
        assert event["user_id"] == 456
        assert event["type"] == "twitch.follow"
        assert event["data"] == event_data

    async def test_log_event_with_empty_data(self, setup_repo):
        """Test logging events with empty or None data"""
        repo = setup_repo

        # Log event with empty dict
        event_id1 = await repo.log_event("empty.event", {})
        event1 = await repo.get_event_by_id(event_id1)
        assert event1["data"] == {}

        # Log event with None data
        event_id2 = await repo.log_event("none.event", None)  # type: ignore
        event2 = await repo.get_event_by_id(event_id2)
        assert event2["data"] == {}

    async def test_get_events_filtering(self, setup_repo):
        """Test event retrieval with various filter combinations"""
        repo = setup_repo

        # Create test users first
        await self.create_test_user(repo, 1, "twitch1", "alice")
        await self.create_test_user(repo, 2, "twitch2", "bob")
        await self.create_test_user(repo, 3, "twitch3", "charlie")

        # Create test events
        await repo.log_event("chat.message", {"user": "alice", "message": "hello"}, user_id=1)
        await repo.log_event("chat.message", {"user": "bob", "message": "hi"}, user_id=2)
        await repo.log_event("twitch.follow", {"user": "alice"}, user_id=1)
        await repo.log_event("twitch.sub", {"user": "charlie"}, user_id=3)

        # Test no filtering
        all_events = await repo.get_events()
        assert len(all_events) == 4

        # Test filtering by event type
        chat_events = await repo.get_events(event_type="chat.message")
        assert len(chat_events) == 2
        assert all(e["type"] == "chat.message" for e in chat_events)

        # Test filtering by user ID
        alice_events = await repo.get_events(user_id=1)
        assert len(alice_events) == 2
        assert all(e["user_id"] == 1 for e in alice_events)

        # Test filtering by both type and user ID
        alice_chat = await repo.get_events(event_type="chat.message", user_id=1)
        assert len(alice_chat) == 1
        assert alice_chat[0]["type"] == "chat.message"
        assert alice_chat[0]["user_id"] == 1

    async def test_get_events_pagination(self, setup_repo):
        """Test limit and offset parameters"""
        repo = setup_repo

        # Create multiple events
        for i in range(10):
            await repo.log_event("test.event", {"index": i})

        # Test limit
        limited_events = await repo.get_events(limit=5)
        assert len(limited_events) == 5

        # Test offset
        offset_events = await repo.get_events(limit=5, offset=5)
        assert len(offset_events) == 5

        # Events should be different (ordered by created_at DESC)
        limited_ids = {e["id"] for e in limited_events}
        offset_ids = {e["id"] for e in offset_events}
        assert limited_ids.isdisjoint(offset_ids)

    async def test_get_event_by_id_found(self, setup_repo):
        """Test retrieval of existing events by ID"""
        repo = setup_repo

        # Create test user first
        await self.create_test_user(repo, 789, "twitch789", "testuser789")

        event_data = {"test": "data", "number": 42}
        event_id = await repo.log_event("test.event", event_data, user_id=789)

        retrieved_event = await repo.get_event_by_id(event_id)
        assert retrieved_event is not None
        assert retrieved_event["id"] == event_id
        assert retrieved_event["type"] == "test.event"
        assert retrieved_event["user_id"] == 789
        assert retrieved_event["data"] == event_data
        assert "created_at" in retrieved_event

    async def test_get_event_by_id_not_found(self, setup_repo):
        """Test that None is returned for non-existent event IDs"""
        repo = setup_repo

        result = await repo.get_event_by_id(99999)
        assert result is None

    async def test_get_event_types(self, setup_repo):
        """Test that unique event types are correctly retrieved"""
        repo = setup_repo

        # Initially empty
        types = await repo.get_event_types()
        assert types == []

        # Add events of different types
        await repo.log_event("chat.message", {"text": "hello"})
        await repo.log_event("twitch.follow", {"user": "alice"})
        await repo.log_event("chat.message", {"text": "world"})  # Duplicate type
        await repo.log_event("obs.scene.change", {"scene": "game"})

        types = await repo.get_event_types()
        assert len(types) == 3
        assert "chat.message" in types
        assert "twitch.follow" in types
        assert "obs.scene.change" in types

    async def test_count_events(self, setup_repo):
        """Test event counting with and without filters"""
        repo = setup_repo

        # Initially empty
        count = await repo.count_events()
        assert count == 0

        # Create test users first
        await self.create_test_user(repo, 1, "twitch1", "alice")
        await self.create_test_user(repo, 2, "twitch2", "bob")

        # Add test events
        await repo.log_event("chat.message", {"user": "alice"}, user_id=1)
        await repo.log_event("chat.message", {"user": "bob"}, user_id=2)
        await repo.log_event("twitch.follow", {"user": "alice"}, user_id=1)

        # Count all events
        total_count = await repo.count_events()
        assert total_count == 3

        # Count by event type
        chat_count = await repo.count_events(event_type="chat.message")
        assert chat_count == 2

        # Count by user ID
        alice_count = await repo.count_events(user_id=1)
        assert alice_count == 2

        # Count by both filters
        alice_chat_count = await repo.count_events(event_type="chat.message", user_id=1)
        assert alice_chat_count == 1

        # Count non-existent
        none_count = await repo.count_events(event_type="nonexistent")
        assert none_count == 0

    async def test_delete_old_events(self, setup_repo):
        """Test that old events are properly deleted"""
        repo = setup_repo

        # Add some recent events
        recent_id1 = await repo.log_event("recent.event", {"data": "recent1"})
        recent_id2 = await repo.log_event("recent.event", {"data": "recent2"})

        # Manually insert old events by modifying the database directly
        old_date = (datetime.now() - timedelta(days=35)).isoformat()
        await repo.db.execute(
            "INSERT INTO events (type, data, created_at) VALUES (?, ?, ?)",
            ("old.event", json.dumps({"data": "old"}), old_date),
        )
        await repo.db.commit()

        # Verify we have 3 events total
        total_before = await repo.count_events()
        assert total_before == 3

        # Delete events older than 30 days
        deleted_count = await repo.delete_old_events(days_old=30)
        assert deleted_count == 1

        # Verify recent events still exist
        total_after = await repo.count_events()
        assert total_after == 2

        # Verify specific events still exist
        assert await repo.get_event_by_id(recent_id1) is not None
        assert await repo.get_event_by_id(recent_id2) is not None

    async def test_get_event_stats(self, setup_repo):
        """Test that statistics are correctly calculated"""
        repo = setup_repo

        # Initially empty
        stats = await repo.get_event_stats()
        assert stats["total_events"] == 0
        assert stats["event_type_breakdown"] == {}
        assert stats["daily_events_last_7_days"] == {}

        # Add test events
        await repo.log_event("chat.message", {"text": "hello"})
        await repo.log_event("chat.message", {"text": "world"})
        await repo.log_event("twitch.follow", {"user": "alice"})
        await repo.log_event("obs.scene.change", {"scene": "game"})

        stats = await repo.get_event_stats()

        # Check total
        assert stats["total_events"] == 4

        # Check type breakdown
        breakdown = stats["event_type_breakdown"]
        assert breakdown["chat.message"] == 2
        assert breakdown["twitch.follow"] == 1
        assert breakdown["obs.scene.change"] == 1

        # Check daily stats (should have events from recent days)
        daily_stats = stats["daily_events_last_7_days"]
        assert len(daily_stats) >= 1  # At least one day should have events
        total_daily_events = sum(daily_stats.values())
        assert total_daily_events >= 4  # All events should be accounted for

    async def test_json_decode_error_handling(self, setup_repo):
        """Test graceful handling of JSON decode errors"""
        repo = setup_repo

        # Manually insert event with invalid JSON
        await repo.db.execute("INSERT INTO events (type, data) VALUES (?, ?)", ("invalid.json", "{ invalid json }"))
        await repo.db.commit()

        # Should handle gracefully and return empty dict for data
        events = await repo.get_events()
        assert len(events) == 1
        assert events[0]["data"] == {}  # Should default to empty dict

        # Test get_event_by_id with invalid JSON
        event_id = events[0]["id"]
        event = await repo.get_event_by_id(event_id)
        assert event is not None
        assert event["data"] == {}

    async def test_empty_database_scenarios(self, setup_repo):
        """Test all methods when database is empty"""
        repo = setup_repo

        # All methods should handle empty database gracefully
        assert await repo.get_events() == []
        assert await repo.get_event_by_id(1) is None
        assert await repo.get_event_types() == []
        assert await repo.count_events() == 0
        assert await repo.delete_old_events() == 0

        stats = await repo.get_event_stats()
        assert stats["total_events"] == 0
        assert stats["event_type_breakdown"] == {}
        assert stats["daily_events_last_7_days"] == {}

    async def test_large_event_data(self, setup_repo):
        """Test handling of large event data"""
        repo = setup_repo

        # Create large event data
        large_data = {
            "users": [f"user_{i}" for i in range(1000)],
            "messages": [f"message_{i}" * 100 for i in range(100)],
            "metadata": {"large_field": "x" * 10000},
        }

        event_id = await repo.log_event("large.event", large_data)

        # Verify large data is stored and retrieved correctly
        retrieved_event = await repo.get_event_by_id(event_id)
        assert retrieved_event is not None
        assert retrieved_event["data"] == large_data
