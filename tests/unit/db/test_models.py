"""
Tests for database models
"""

import json

from pantainos.db.models import PersistentVariable, SessionVariable


class TestPersistentVariable:
    """Test PersistentVariable functionality"""

    def test_get_typed_value_string(self):
        """Test string value retrieval"""
        var = PersistentVariable(name="test", value="hello", data_type="string")
        assert var.get_typed_value() == "hello"

    def test_get_typed_value_number_int(self):
        """Test integer value retrieval"""
        var = PersistentVariable(name="test", value="42", data_type="number")
        assert var.get_typed_value() == 42

    def test_get_typed_value_number_float(self):
        """Test float value retrieval"""
        var = PersistentVariable(name="test", value="3.14", data_type="number")
        assert var.get_typed_value() == 3.14

    def test_get_typed_value_number_invalid(self):
        """Test invalid number returns 0"""
        var = PersistentVariable(name="test", value="not_a_number", data_type="number")
        assert var.get_typed_value() == 0

    def test_get_typed_value_boolean_true(self):
        """Test boolean true values"""
        test_values = ["true", "1", "yes", "on", "TRUE", "Yes", "ON"]
        for value in test_values:
            var = PersistentVariable(name="test", value=value, data_type="boolean")
            assert var.get_typed_value() is True

    def test_get_typed_value_boolean_false(self):
        """Test boolean false values"""
        test_values = ["false", "0", "no", "off", "FALSE", "No", "OFF", ""]
        for value in test_values:
            var = PersistentVariable(name="test", value=value, data_type="boolean")
            assert var.get_typed_value() is False

    def test_get_typed_value_json_valid(self):
        """Test valid JSON value retrieval"""
        data = {"key": "value", "number": 42}
        var = PersistentVariable(name="test", value=json.dumps(data), data_type="json")
        assert var.get_typed_value() == data

    def test_get_typed_value_json_invalid(self):
        """Test invalid JSON returns empty dict"""
        var = PersistentVariable(name="test", value="invalid_json", data_type="json")
        assert var.get_typed_value() == {}

    def test_from_value_boolean(self):
        """Test creating from boolean value"""
        var = PersistentVariable.from_value("test", True, "description")
        assert var.name == "test"
        assert var.value == "true"
        assert var.data_type == "boolean"
        assert var.description == "description"

    def test_from_value_int(self):
        """Test creating from integer value"""
        var = PersistentVariable.from_value("test", 42, "description")
        assert var.name == "test"
        assert var.value == "42"
        assert var.data_type == "number"

    def test_from_value_float(self):
        """Test creating from float value"""
        var = PersistentVariable.from_value("test", 3.14, "description")
        assert var.name == "test"
        assert var.value == "3.14"
        assert var.data_type == "number"

    def test_from_value_dict(self):
        """Test creating from dict value"""
        data = {"key": "value"}
        var = PersistentVariable.from_value("test", data, "description")
        assert var.name == "test"
        assert var.value == json.dumps(data)
        assert var.data_type == "json"

    def test_from_value_list(self):
        """Test creating from list value"""
        data = [1, 2, 3]
        var = PersistentVariable.from_value("test", data, "description")
        assert var.name == "test"
        assert var.value == json.dumps(data)
        assert var.data_type == "json"

    def test_from_value_string(self):
        """Test creating from string value"""
        var = PersistentVariable.from_value("test", "hello", "description")
        assert var.name == "test"
        assert var.value == "hello"
        assert var.data_type == "string"


class TestSessionVariable:
    """Test SessionVariable functionality"""

    def test_get_typed_value_string(self):
        """Test string value retrieval"""
        var = SessionVariable(name="test", value="hello", data_type="string")
        assert var.get_typed_value() == "hello"

    def test_get_typed_value_number_int(self):
        """Test integer value retrieval"""
        var = SessionVariable(name="test", value="42", data_type="number")
        assert var.get_typed_value() == 42

    def test_get_typed_value_number_float(self):
        """Test float value retrieval"""
        var = SessionVariable(name="test", value="3.14", data_type="number")
        assert var.get_typed_value() == 3.14

    def test_get_typed_value_number_invalid(self):
        """Test invalid number returns 0"""
        var = SessionVariable(name="test", value="not_a_number", data_type="number")
        assert var.get_typed_value() == 0

    def test_get_typed_value_boolean_true(self):
        """Test boolean true values"""
        test_values = ["true", "1", "yes", "on", "TRUE", "Yes", "ON"]
        for value in test_values:
            var = SessionVariable(name="test", value=value, data_type="boolean")
            assert var.get_typed_value() is True

    def test_get_typed_value_boolean_false(self):
        """Test boolean false values"""
        test_values = ["false", "0", "no", "off", "FALSE", "No", "OFF", ""]
        for value in test_values:
            var = SessionVariable(name="test", value=value, data_type="boolean")
            assert var.get_typed_value() is False

    def test_get_typed_value_json_valid(self):
        """Test valid JSON value retrieval"""
        data = {"key": "value", "number": 42}
        var = SessionVariable(name="test", value=json.dumps(data), data_type="json")
        assert var.get_typed_value() == data

    def test_get_typed_value_json_invalid(self):
        """Test invalid JSON returns empty dict"""
        var = SessionVariable(name="test", value="invalid_json", data_type="json")
        assert var.get_typed_value() == {}

    def test_from_value_boolean(self):
        """Test creating from boolean value"""
        var = SessionVariable.from_value("test", True)
        assert var.name == "test"
        assert var.value == "true"
        assert var.data_type == "boolean"

    def test_from_value_int(self):
        """Test creating from integer value"""
        var = SessionVariable.from_value("test", 42)
        assert var.name == "test"
        assert var.value == "42"
        assert var.data_type == "number"

    def test_from_value_float(self):
        """Test creating from float value"""
        var = SessionVariable.from_value("test", 3.14)
        assert var.name == "test"
        assert var.value == "3.14"
        assert var.data_type == "number"

    def test_from_value_dict(self):
        """Test creating from dict value"""
        data = {"key": "value"}
        var = SessionVariable.from_value("test", data)
        assert var.name == "test"
        assert var.value == json.dumps(data)
        assert var.data_type == "json"

    def test_from_value_list(self):
        """Test creating from list value"""
        data = [1, 2, 3]
        var = SessionVariable.from_value("test", data)
        assert var.name == "test"
        assert var.value == json.dumps(data)
        assert var.data_type == "json"

    def test_from_value_string(self):
        """Test creating from string value"""
        var = SessionVariable.from_value("test", "hello")
        assert var.name == "test"
        assert var.value == "hello"
        assert var.data_type == "string"
