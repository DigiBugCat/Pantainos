"""
Tests for documentation generator functionality
"""

from unittest.mock import AsyncMock, MagicMock

import pytest


@pytest.fixture
def mock_pantainos_app():
    """Create a mock Pantainos application for documentation testing"""
    app = MagicMock()
    app.event_bus = MagicMock()
    app.event_bus.handlers = {
        "test.event": [{"handler": AsyncMock(__name__="test_handler"), "condition": None, "source": "core"}],
        "chat.message": [
            {
                "handler": AsyncMock(__name__="chat_handler"),
                "condition": MagicMock(name="command_filter"),
                "source": "chat_plugin",
            }
        ],
    }
    app.plugins = {"chat_plugin": MagicMock(name="ChatPlugin"), "test_plugin": MagicMock(name="TestPlugin")}
    return app


@pytest.mark.asyncio
async def test_documentation_generator_import():
    """Test that DocumentationGenerator can be imported"""
    from pantainos.web.docs import DocumentationGenerator

    assert DocumentationGenerator is not None


@pytest.mark.asyncio
async def test_documentation_generator_creation(mock_pantainos_app):
    """Test DocumentationGenerator can be created with Pantainos app"""
    from pantainos.web.docs import DocumentationGenerator

    generator = DocumentationGenerator(mock_pantainos_app)

    assert generator is not None
    assert generator.app is mock_pantainos_app


@pytest.mark.asyncio
async def test_extract_handlers_docs_basic(mock_pantainos_app):
    """Test basic handler documentation extraction"""
    from pantainos.web.docs import DocumentationGenerator

    generator = DocumentationGenerator(mock_pantainos_app)
    docs = generator.extract_handlers_docs()

    assert isinstance(docs, dict)
    assert "handlers" in docs
    assert len(docs["handlers"]) == 2  # Two handlers in mock data


@pytest.mark.asyncio
async def test_extract_handlers_docs_structure(mock_pantainos_app):
    """Test that extracted docs have correct structure"""
    from pantainos.web.docs import DocumentationGenerator

    generator = DocumentationGenerator(mock_pantainos_app)
    docs = generator.extract_handlers_docs()

    # Check first handler
    handler_doc = docs["handlers"][0]

    assert "event_type" in handler_doc
    assert "handler_name" in handler_doc
    assert "docstring" in handler_doc
    assert "signature" in handler_doc
    assert "dependencies" in handler_doc
    assert "conditions" in handler_doc
    assert "source" in handler_doc


@pytest.mark.asyncio
async def test_extract_handlers_with_conditions(mock_pantainos_app):
    """Test extraction of handlers with conditions"""
    from pantainos.web.docs import DocumentationGenerator

    generator = DocumentationGenerator(mock_pantainos_app)
    docs = generator.extract_handlers_docs()

    # Find handler with condition
    handler_with_condition = next(h for h in docs["handlers"] if h["event_type"] == "chat.message")

    assert handler_with_condition["conditions"] is not None
    assert "name" in handler_with_condition["conditions"]


@pytest.mark.asyncio
async def test_extract_handlers_without_conditions(mock_pantainos_app):
    """Test extraction of handlers without conditions"""
    from pantainos.web.docs import DocumentationGenerator

    generator = DocumentationGenerator(mock_pantainos_app)
    docs = generator.extract_handlers_docs()

    # Find handler without condition
    handler_no_condition = next(h for h in docs["handlers"] if h["event_type"] == "test.event")

    assert handler_no_condition["conditions"] is None


@pytest.mark.asyncio
async def test_extract_handlers_empty_bus():
    """Test extraction when event bus has no handlers"""
    app = MagicMock()
    app.event_bus.handlers = {}
    app.plugins = {}

    from pantainos.web.docs import DocumentationGenerator

    generator = DocumentationGenerator(app)
    docs = generator.extract_handlers_docs()

    assert docs["handlers"] == []


@pytest.mark.asyncio
async def test_extract_dependencies_from_handler():
    """Test extraction of handler dependencies through signature inspection"""
    from pantainos.web.docs import DocumentationGenerator

    # Mock handler with dependencies in signature
    def sample_handler(event, db_repo, chat_plugin):
        """Sample handler with dependencies"""
        pass

    app = MagicMock()
    app.event_bus.handlers = {"sample.event": [{"handler": sample_handler, "condition": None, "source": "test"}]}
    app.plugins = {}

    generator = DocumentationGenerator(app)
    docs = generator.extract_handlers_docs()

    handler_doc = docs["handlers"][0]
    assert len(handler_doc["dependencies"]) > 0
    # Should extract parameter names beyond 'event'
    deps = handler_doc["dependencies"]
    assert "db_repo" in deps or "chat_plugin" in deps
