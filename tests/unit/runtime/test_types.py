"""Tests for runtime types - Event"""

import time

from pantainos.runtime.types import Event


class TestEvent:
    """Tests for Event dataclass"""

    def test_event_creation_and_defaults(self):
        """Verify that Event instances are created with correct default values"""
        before_time = time.time()
        event = Event(type="test.event", data={"key": "value"})
        after_time = time.time()

        assert event.type == "test.event"
        assert event.data == {"key": "value"}
        assert event.source == "unknown"
        assert before_time <= event.timestamp <= after_time

    def test_event_creation_with_custom_values(self):
        """Verify Event creation with custom source and timestamp"""
        custom_timestamp = 1234567890.0
        event = Event(
            type="custom.event",
            data={"test": True},
            source="custom_source",
            timestamp=custom_timestamp,
        )

        assert event.type == "custom.event"
        assert event.data == {"test": True}
        assert event.source == "custom_source"
        assert event.timestamp == custom_timestamp
