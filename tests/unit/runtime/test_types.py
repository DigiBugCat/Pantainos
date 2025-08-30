"""Tests for runtime types - Event"""

import time
from dataclasses import asdict

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

    def test_event_to_dict_conversion(self):
        """Verify that to_dict method correctly converts Event to dictionary"""
        event = Event(
            type="test.event",
            data={"key": "value"},
            source="test_source",
            timestamp=1234567890.0,
        )
        result = event.to_dict()

        expected = {
            "type": "test.event",
            "data": {"key": "value"},
            "source": "test_source",
            "timestamp": 1234567890.0,
        }
        assert result == expected
        assert result == asdict(event)

    def test_event_model_dump_conversion(self):
        """Verify that model_dump method correctly converts Event to dictionary"""
        event = Event(
            type="test.event",
            data={"key": "value"},
            source="test_source",
            timestamp=1234567890.0,
        )
        result = event.model_dump()

        expected = {
            "type": "test.event",
            "data": {"key": "value"},
            "source": "test_source",
            "timestamp": 1234567890.0,
        }
        assert result == expected
        assert result == event.to_dict()
