"""
Tests for Pantainos library public API
"""


def test_basic_imports():
    """Test that basic pantainos imports work"""
    from pantainos import Event, EventBus, on_event

    assert Event is not None
    assert EventBus is not None
    assert on_event is not None


def test_version_available():
    """Test that version is available"""
    from pantainos import __version__

    assert __version__ == "0.1.0"


# Triggers removed - using Conditions instead


def test_di_imports_work():
    """Test that DI imports work for library users"""
    from pantainos import HandlerRegistry, ServiceContainer

    assert ServiceContainer is not None
    assert HandlerRegistry is not None


def test_core_repositories_imports_work():
    """Test that core repository imports work for library users"""
    from pantainos import BaseRepository, EventRepository, VariableRepository

    assert EventRepository is not None
    assert VariableRepository is not None
    assert BaseRepository is not None
