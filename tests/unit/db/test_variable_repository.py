"""
Tests for VariableRepository
"""

import json
import tempfile
from pathlib import Path

import pytest

from pantainos.db.database import Database
from pantainos.db.repositories.variable_repository import VariableRepository


class TestVariableRepository:
    """Test VariableRepository functionality"""

    @pytest.fixture
    async def setup_repo(self):
        """Create a database and repository for testing"""
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "test_variables.db"
            db = Database(db_path)
            await db.initialize()
            repo = VariableRepository(db)
            yield repo
            await db.close()

    async def test_get_persistent_variable_returns_correct_value(self, setup_repo):
        """Test getting persistent variables with different data types"""
        repo = setup_repo

        # Test string variable
        await repo.set("test_string", "hello world", persistent=True)
        result = await repo.get("test_string", persistent=True)
        assert result == "hello world"

        # Test number variable
        await repo.set("test_number", 42, persistent=True)
        result = await repo.get("test_number", persistent=True)
        assert result == 42

        # Test boolean variable
        await repo.set("test_bool", True, persistent=True)
        result = await repo.get("test_bool", persistent=True)
        assert result is True

        # Test JSON variable
        test_data = {"key": "value", "list": [1, 2, 3]}
        await repo.set("test_json", test_data, persistent=True)
        result = await repo.get("test_json", persistent=True)
        assert result == test_data

    async def test_get_session_variable_returns_correct_value(self, setup_repo):
        """Test getting session variables with different data types"""
        repo = setup_repo

        # Test string variable
        await repo.set("session_string", "hello session", persistent=False)
        result = await repo.get("session_string", persistent=False)
        assert result == "hello session"

        # Test number variable
        await repo.set("session_number", 3.14, persistent=False)
        result = await repo.get("session_number", persistent=False)
        assert result == 3.14

    async def test_get_nonexistent_variable_returns_default(self, setup_repo):
        """Test that default values are returned for missing variables"""
        repo = setup_repo

        # Test with default
        result = await repo.get("nonexistent", default="default_value", persistent=True)
        assert result == "default_value"

        # Test with None default
        result = await repo.get("nonexistent", default=None, persistent=True)
        assert result is None

        # Test session variable
        result = await repo.get("nonexistent_session", default=123, persistent=False)
        assert result == 123

    async def test_set_persistent_variable_all_types(self, setup_repo):
        """Test setting persistent variables with all supported types"""
        repo = setup_repo

        # String
        await repo.set("string_var", "test string", persistent=True, description="A test string")
        result = await repo.get("string_var", persistent=True)
        assert result == "test string"

        # Integer
        await repo.set("int_var", 42, persistent=True)
        result = await repo.get("int_var", persistent=True)
        assert result == 42

        # Float
        await repo.set("float_var", 3.14159, persistent=True)
        result = await repo.get("float_var", persistent=True)
        assert result == 3.14159

        # Boolean
        await repo.set("bool_var", False, persistent=True)
        result = await repo.get("bool_var", persistent=True)
        assert result is False

        # List
        await repo.set("list_var", [1, "two", 3.0], persistent=True)
        result = await repo.get("list_var", persistent=True)
        assert result == [1, "two", 3.0]

        # Dict
        await repo.set("dict_var", {"nested": {"key": "value"}}, persistent=True)
        result = await repo.get("dict_var", persistent=True)
        assert result == {"nested": {"key": "value"}}

    async def test_set_session_variable_all_types(self, setup_repo):
        """Test setting session variables with all supported types"""
        repo = setup_repo

        # String
        await repo.set("session_string", "session test", persistent=False)
        result = await repo.get("session_string", persistent=False)
        assert result == "session test"

        # Number
        await repo.set("session_number", 99.9, persistent=False)
        result = await repo.get("session_number", persistent=False)
        assert result == 99.9

        # Boolean
        await repo.set("session_bool", True, persistent=False)
        result = await repo.get("session_bool", persistent=False)
        assert result is True

    async def test_delete_variable(self, setup_repo):
        """Test deletion of both persistent and session variables"""
        repo = setup_repo

        # Create variables
        await repo.set("persistent_var", "test", persistent=True)
        await repo.set("session_var", "test", persistent=False)

        # Verify they exist
        assert await repo.exists("persistent_var", persistent=True)
        assert await repo.exists("session_var", persistent=False)

        # Delete persistent variable
        deleted = await repo.delete("persistent_var", persistent=True)
        assert deleted is True
        assert not await repo.exists("persistent_var", persistent=True)

        # Delete session variable
        deleted = await repo.delete("session_var", persistent=False)
        assert deleted is True
        assert not await repo.exists("session_var", persistent=False)

        # Try to delete non-existent variable
        deleted = await repo.delete("nonexistent", persistent=True)
        assert deleted is False

    async def test_exists_variable(self, setup_repo):
        """Test existence checking for both variable types"""
        repo = setup_repo

        # Initially doesn't exist
        assert not await repo.exists("test_var", persistent=True)
        assert not await repo.exists("test_var", persistent=False)

        # Create variables
        await repo.set("persistent_var", "value", persistent=True)
        await repo.set("session_var", "value", persistent=False)

        # Now they exist
        assert await repo.exists("persistent_var", persistent=True)
        assert await repo.exists("session_var", persistent=False)

        # Check cross-type doesn't exist
        assert not await repo.exists("persistent_var", persistent=False)
        assert not await repo.exists("session_var", persistent=True)

    async def test_list_variables(self, setup_repo):
        """Test listing variables and type conversion"""
        repo = setup_repo

        # Create some test variables
        await repo.set("string_var", "hello", persistent=True, description="A string")
        await repo.set("number_var", 42, persistent=True)
        await repo.set("bool_var", True, persistent=True)
        await repo.set("json_var", {"key": "value"}, persistent=True)

        await repo.set("session_string", "session", persistent=False)
        await repo.set("session_number", 3.14, persistent=False)

        # List persistent variables
        persistent_vars = await repo.list_variables(persistent=True)
        assert len(persistent_vars) == 4

        # Check structure and values
        string_var = next(v for v in persistent_vars if v["name"] == "string_var")
        assert string_var["value"] == "hello"
        assert string_var["data_type"] == "string"
        assert string_var["description"] == "A string"

        number_var = next(v for v in persistent_vars if v["name"] == "number_var")
        assert number_var["value"] == 42
        assert number_var["data_type"] == "number"

        # List session variables
        session_vars = await repo.list_variables(persistent=False)
        assert len(session_vars) == 2

        session_string = next(v for v in session_vars if v["name"] == "session_string")
        assert session_string["value"] == "session"
        assert session_string["data_type"] == "string"

    async def test_clear_session_variables(self, setup_repo):
        """Test that all session variables are properly cleared"""
        repo = setup_repo

        # Create some variables
        await repo.set("persistent_var", "keep me", persistent=True)
        await repo.set("session_var1", "delete me", persistent=False)
        await repo.set("session_var2", "delete me too", persistent=False)

        # Verify they exist
        assert await repo.exists("persistent_var", persistent=True)
        assert await repo.exists("session_var1", persistent=False)
        assert await repo.exists("session_var2", persistent=False)

        # Clear session variables
        cleared_count = await repo.clear_session_variables()
        assert cleared_count == 2

        # Verify only session variables were cleared
        assert await repo.exists("persistent_var", persistent=True)
        assert not await repo.exists("session_var1", persistent=False)
        assert not await repo.exists("session_var2", persistent=False)

        # Clear again should return 0
        cleared_count = await repo.clear_session_variables()
        assert cleared_count == 0

    async def test_increment_numeric_variables(self, setup_repo):
        """Test incrementing integer and float variables"""
        repo = setup_repo

        # Test incrementing integer
        await repo.set("counter", 10, persistent=True)
        result = await repo.increment("counter", amount=5, persistent=True)
        assert result == 15
        stored_value = await repo.get("counter", persistent=True)
        assert stored_value == 15

        # Test incrementing float
        await repo.set("decimal", 3.14, persistent=True)
        result = await repo.increment("decimal", amount=0.86, persistent=True)
        assert result == 4.0
        stored_value = await repo.get("decimal", persistent=True)
        assert stored_value == 4.0

        # Test incrementing non-existent variable with default
        result = await repo.increment("new_counter", amount=1, default=100, persistent=True)
        assert result == 101
        stored_value = await repo.get("new_counter", persistent=True)
        assert stored_value == 101

    async def test_increment_non_numeric_raises_error(self, setup_repo):
        """Test that incrementing non-numeric variables raises ValueError"""
        repo = setup_repo

        # Create non-numeric variable
        await repo.set("string_var", "not a number", persistent=True)

        # Should raise ValueError
        with pytest.raises(ValueError, match="Cannot increment non-numeric variable"):
            await repo.increment("string_var", persistent=True)

    async def test_append_to_list_existing_variable(self, setup_repo):
        """Test appending items to existing list variables"""
        repo = setup_repo

        # Create list variable
        await repo.set("my_list", [1, 2, 3], persistent=True)

        # Append item
        result = await repo.append_to_list("my_list", 4, persistent=True)
        assert result == [1, 2, 3, 4]

        # Verify stored value
        stored_value = await repo.get("my_list", persistent=True)
        assert stored_value == [1, 2, 3, 4]

        # Append another item
        result = await repo.append_to_list("my_list", "five", persistent=True)
        assert result == [1, 2, 3, 4, "five"]

    async def test_append_to_list_nonexistent_variable_creates_new(self, setup_repo):
        """Test that appending to non-existent variable creates new list"""
        repo = setup_repo

        # Append to non-existent variable
        result = await repo.append_to_list("new_list", "first_item", persistent=True)
        assert result == ["first_item"]

        # Verify stored value
        stored_value = await repo.get("new_list", persistent=True)
        assert stored_value == ["first_item"]

    async def test_append_to_list_with_max_length(self, setup_repo):
        """Test list trimming when max_length is specified"""
        repo = setup_repo

        # Create list with 3 items
        await repo.set("limited_list", [1, 2, 3], persistent=True)

        # Append with max_length=3, should trim oldest
        result = await repo.append_to_list("limited_list", 4, max_length=3, persistent=True)
        assert result == [2, 3, 4]

        # Append another with max_length=2
        result = await repo.append_to_list("limited_list", 5, max_length=2, persistent=True)
        assert result == [4, 5]

    async def test_append_to_non_list_raises_error(self, setup_repo):
        """Test that appending to non-list variables raises ValueError"""
        repo = setup_repo

        # Create non-list variable
        await repo.set("not_a_list", "string value", persistent=True)

        # Should raise ValueError
        with pytest.raises(ValueError, match="Cannot append to non-list variable"):
            await repo.append_to_list("not_a_list", "item", persistent=True)

    async def test_convert_value_handles_all_data_types(self, setup_repo):
        """Test all type conversions"""
        repo = setup_repo

        # Test number conversions
        assert repo.convert_value("42", "number") == 42
        assert repo.convert_value("3.14", "number") == 3.14
        assert repo.convert_value("invalid", "number") == 0

        # Test boolean conversions
        assert repo.convert_value("true", "boolean") is True
        assert repo.convert_value("1", "boolean") is True
        assert repo.convert_value("yes", "boolean") is True
        assert repo.convert_value("on", "boolean") is True
        assert repo.convert_value("false", "boolean") is False
        assert repo.convert_value("0", "boolean") is False
        assert repo.convert_value("no", "boolean") is False

        # Test JSON conversions
        json_data = {"key": "value", "list": [1, 2, 3]}
        json_string = json.dumps(json_data)
        assert repo.convert_value(json_string, "json") == json_data
        assert repo.convert_value("invalid json", "json") == {}

        # Test string conversion
        assert repo.convert_value("hello world", "string") == "hello world"
        assert repo.convert_value("123", "string") == "123"

    async def test_get_stats_returns_correct_counts(self, setup_repo):
        """Test statistics collection for variable counts and types"""
        repo = setup_repo

        # Initially empty
        stats = await repo.get_stats()
        assert stats["persistent_variables"] == 0
        assert stats["session_variables"] == 0
        assert stats["total_variables"] == 0
        assert stats["persistent_type_breakdown"] == {}

        # Add some variables
        await repo.set("string_var", "hello", persistent=True)
        await repo.set("number_var1", 42, persistent=True)
        await repo.set("number_var2", 3.14, persistent=True)
        await repo.set("bool_var", True, persistent=True)
        await repo.set("json_var", {"key": "value"}, persistent=True)

        await repo.set("session_var1", "session", persistent=False)
        await repo.set("session_var2", 123, persistent=False)

        # Check stats
        stats = await repo.get_stats()
        assert stats["persistent_variables"] == 5
        assert stats["session_variables"] == 2
        assert stats["total_variables"] == 7

        # Check type breakdown
        breakdown = stats["persistent_type_breakdown"]
        assert breakdown["string"] == 1
        assert breakdown["number"] == 2
        assert breakdown["boolean"] == 1
        assert breakdown["json"] == 1
