"""
Tests for conditions.py - Event filtering conditions
"""

from pantainos.events import Condition, equals


def test_equals_condition_creates_callable():
    """Test that equals() creates a callable condition"""
    condition = equals("status", "active")

    assert callable(condition)
    assert isinstance(condition, Condition)


def test_equals_condition_matches_correct_value():
    """Test that equals condition matches the correct value"""
    from pantainos.events import GenericEvent

    condition = equals("status", "active")

    # Should match
    event = GenericEvent(type="test", data={"status": "active"}, source="test")
    assert condition(event) is True

    # Should not match
    event = GenericEvent(type="test", data={"status": "inactive"}, source="test")
    assert condition(event) is False


def test_equals_condition_handles_missing_field():
    """Test that equals condition handles missing fields gracefully"""
    from pantainos.events import GenericEvent

    condition = equals("status", "active")

    # Missing field should not match
    event = GenericEvent(type="test", data={"other_field": "value"}, source="test")
    assert condition(event) is False
