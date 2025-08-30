"""
Tests for events.py - Event model definitions
"""

from pantainos.events import EventModel, GenericEvent, SampleEvent, SystemEvent


def test_generic_event_creation():
    """Test that GenericEvent can be created with basic fields"""
    event = GenericEvent(type="test.event", data={"key": "value"}, source="test")

    assert event.type == "test.event"
    assert event.data == {"key": "value"}
    assert event.source == "test"


def test_generic_event_dynamic_type_setting():
    """Test that GenericEvent sets event_type dynamically from type field"""
    event = GenericEvent(type="dynamic.event", data={}, source="test")

    # The event_type class variable should be updated
    assert GenericEvent.event_type == "dynamic.event"


def test_system_event_creation():
    """Test that SystemEvent has correct event_type and required fields"""
    event = SystemEvent(action="startup", source="system")

    assert event.event_type == "system"
    assert event.action == "startup"
    assert event.source == "system"
    assert event.extra_metadata == {}


def test_sample_event_creation():
    """Test that SampleEvent has correct event_type"""
    event = SampleEvent(source="test")

    assert event.event_type == "test.event"
    assert event.message == "Test message"  # default value
    assert event.data == {}
    assert event.source == "test"


def test_event_model_base_class():
    """Test that EventModel base class works correctly"""
    # Can't instantiate abstract EventModel directly, but can test inheritance
    assert issubclass(GenericEvent, EventModel)
    assert issubclass(SystemEvent, EventModel)
    assert issubclass(SampleEvent, EventModel)


def test_event_model_serialization():
    """Test that events can be serialized with model_dump"""
    event = GenericEvent(type="serialization.test", data={"nested": {"key": "value"}}, source="test")

    data = event.model_dump()

    assert data["type"] == "serialization.test"
    assert data["data"]["nested"]["key"] == "value"
    assert data["source"] == "test"


def test_event_condition_methods():
    """Test that EventModel condition methods work"""
    event = GenericEvent(type="test", data={}, source="test_source")

    # Test source_is condition
    source_condition = GenericEvent.source_is("test_source")
    assert source_condition(event) is True

    wrong_source_condition = GenericEvent.source_is("other_source")
    assert wrong_source_condition(event) is False
