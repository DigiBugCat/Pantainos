"""
Unit tests for HandlerInspector dependency injection functionality
"""

from typing import Any
from unittest.mock import MagicMock

from pantainos.core.di.inspector import HandlerInspector, HandlerStyle


# Mock types for testing
class MockTwitchClient:
    """Mock Twitch client for testing"""

    pass


class MockLogger:
    """Mock logger for testing"""

    pass


class MockEvent:
    """Mock event for testing"""

    pass


class TestHandlerInspector:
    """Test cases for HandlerInspector"""

    def test_get_style_legacy_handler_with_ctx(self):
        """Test that handlers with (event, ctx) are identified as LEGACY"""

        def legacy_handler(event, ctx):
            pass

        style = HandlerInspector.get_style(legacy_handler)
        assert style == HandlerStyle.LEGACY

    def test_get_style_legacy_handler_with_context(self):
        """Test that handlers with (event, context) are identified as LEGACY"""

        def legacy_handler(event, context):
            pass

        style = HandlerInspector.get_style(legacy_handler)
        assert style == HandlerStyle.LEGACY

    def test_get_style_legacy_handler_case_insensitive(self):
        """Test that handler style detection is case insensitive"""

        # Use lowercase names but uppercase the actual parameter name internally
        # This tests the case insensitive logic without violating naming conventions
        def legacy_handler_upper(event, **kwargs):
            # Simulate a handler that would have 'CTX' as parameter name
            pass

        def legacy_handler_mixed(event, **kwargs):
            # Simulate a handler that would have 'Context' as parameter name
            pass

        # Create test functions with the actual uppercase names dynamically
        import types

        # Create function with CTX parameter
        code_upper = compile("def test_func(event, CTX): pass", "<test>", "exec")
        func_upper = types.FunctionType(code_upper.co_consts[0], {})

        # Create function with Context parameter
        code_mixed = compile("def test_func(event, Context): pass", "<test>", "exec")
        func_mixed = types.FunctionType(code_mixed.co_consts[0], {})

        assert HandlerInspector.get_style(func_upper) == HandlerStyle.LEGACY
        assert HandlerInspector.get_style(func_mixed) == HandlerStyle.LEGACY

    def test_get_style_explicit_handler_with_annotations(self):
        """Test that handlers with type annotations are identified as EXPLICIT"""

        def explicit_handler(event: MockEvent, twitch: MockTwitchClient):
            pass

        style = HandlerInspector.get_style(explicit_handler)
        assert style == HandlerStyle.EXPLICIT

    def test_get_style_explicit_handler_without_annotations(self):
        """Test that handlers with multiple params (not ctx/context) are EXPLICIT"""

        def explicit_handler(event, twitch, logger):
            pass

        style = HandlerInspector.get_style(explicit_handler)
        assert style == HandlerStyle.EXPLICIT

    def test_get_style_single_parameter(self):
        """Test that handlers with only one parameter are EXPLICIT"""

        def single_param_handler(event):
            pass

        style = HandlerInspector.get_style(single_param_handler)
        assert style == HandlerStyle.EXPLICIT

    def test_get_style_no_parameters(self):
        """Test that handlers with no parameters are EXPLICIT"""

        def no_param_handler():
            pass

        style = HandlerInspector.get_style(no_param_handler)
        assert style == HandlerStyle.EXPLICIT

    def test_get_style_three_parameters_with_ctx(self):
        """Test that handlers with 3+ params (including ctx) are EXPLICIT"""

        def three_param_handler(event, ctx, extra):
            pass

        style = HandlerInspector.get_style(three_param_handler)
        assert style == HandlerStyle.EXPLICIT

    def test_get_style_inspection_error(self):
        """Test that inspection errors default to EXPLICIT style"""

        # Mock object that will cause inspection to fail
        mock_handler = MagicMock()
        mock_handler.__name__ = "mock_handler"

        # Make inspect.signature raise an exception
        import inspect

        original_signature = inspect.signature

        def failing_signature(obj):
            if obj is mock_handler:
                raise ValueError("Signature inspection failed")
            return original_signature(obj)

        inspect.signature = failing_signature

        try:
            style = HandlerInspector.get_style(mock_handler)
            assert style == HandlerStyle.EXPLICIT
        finally:
            inspect.signature = original_signature

    def test_get_dependencies_annotated_types(self):
        """Test extraction of dependency types from annotated parameters"""

        def annotated_handler(event: MockEvent, twitch: MockTwitchClient, logger: MockLogger):
            pass

        dependencies = HandlerInspector.get_dependencies(annotated_handler)
        assert dependencies == [MockTwitchClient, MockLogger]

    def test_get_dependencies_unannotated_params(self):
        """Test that unannotated parameters are skipped"""

        def mixed_handler(event: MockEvent, twitch: MockTwitchClient, unannotated):
            pass

        dependencies = HandlerInspector.get_dependencies(mixed_handler)
        assert dependencies == [MockTwitchClient]

    def test_get_dependencies_any_type(self):
        """Test that parameters annotated as Any are skipped"""

        def any_handler(event: MockEvent, any_param: Any, twitch: MockTwitchClient):
            pass

        dependencies = HandlerInspector.get_dependencies(any_handler)
        assert dependencies == [MockTwitchClient]

    def test_get_dependencies_optional_types(self):
        """Test handling of Optional[type] annotations"""

        def optional_handler(event: MockEvent, twitch: MockTwitchClient | None):
            pass

        dependencies = HandlerInspector.get_dependencies(optional_handler)
        assert dependencies == [MockTwitchClient]

    def test_get_dependencies_string_annotations(self):
        """Test that string annotations are skipped (forward references)"""

        def string_annotated_handler(event: MockEvent, forward: "SomeForwardReference"):  # noqa: F821
            pass

        dependencies = HandlerInspector.get_dependencies(string_annotated_handler)
        assert dependencies == []  # String annotations are skipped

    def test_get_dependencies_no_annotations(self):
        """Test that handlers without annotations return empty list"""

        def no_annotations_handler(event, param1, param2):
            pass

        dependencies = HandlerInspector.get_dependencies(no_annotations_handler)
        assert dependencies == []

    def test_get_dependencies_first_param_skipped(self):
        """Test that the first parameter (event) is always skipped"""

        def handler_with_event_annotation(event: MockEvent):
            pass

        dependencies = HandlerInspector.get_dependencies(handler_with_event_annotation)
        assert dependencies == []  # Event parameter should be skipped

    def test_get_dependencies_inspection_error(self):
        """Test that inspection errors return empty list"""

        # Mock object that will cause inspection to fail
        mock_handler = MagicMock()

        dependencies = HandlerInspector.get_dependencies(mock_handler)
        assert dependencies == []

    def test_get_parameter_names(self):
        """Test extraction of parameter names from handler signature"""

        def test_handler(event, twitch, logger):
            pass

        param_names = HandlerInspector.get_parameter_names(test_handler)
        assert param_names == ["event", "twitch", "logger"]

    def test_get_parameter_names_no_params(self):
        """Test parameter names extraction for parameterless function"""

        def no_params():
            pass

        param_names = HandlerInspector.get_parameter_names(no_params)
        assert param_names == []

    def test_get_parameter_names_inspection_error(self):
        """Test that inspection errors return empty list"""

        mock_handler = MagicMock()
        param_names = HandlerInspector.get_parameter_names(mock_handler)
        assert param_names == []

    def test_is_async_handler_async_function(self):
        """Test detection of async functions"""

        async def async_handler(event, ctx):
            pass

        assert HandlerInspector.is_async_handler(async_handler) is True

    def test_is_async_handler_sync_function(self):
        """Test detection of sync functions"""

        def sync_handler(event, ctx):
            pass

        assert HandlerInspector.is_async_handler(sync_handler) is False

    def test_validate_handler_valid_async(self):
        """Test validation of valid async handler"""

        async def valid_async_handler(event, ctx):
            pass

        is_valid, message = HandlerInspector.validate_handler(valid_async_handler)
        assert is_valid is True
        assert message == ""

    def test_validate_handler_valid_sync(self):
        """Test validation of valid sync handler (with warning)"""

        def valid_sync_handler(event, ctx):
            pass

        is_valid, message = HandlerInspector.validate_handler(valid_sync_handler)
        assert is_valid is True
        assert "Warning" in message
        assert "not async" in message

    def test_validate_handler_not_callable(self):
        """Test validation fails for non-callable objects"""

        not_callable = "not a function"

        is_valid, message = HandlerInspector.validate_handler(not_callable)
        assert is_valid is False
        assert "must be callable" in message

    def test_validate_handler_no_parameters(self):
        """Test validation fails for handlers with no parameters"""

        def no_params_handler():
            pass

        is_valid, message = HandlerInspector.validate_handler(no_params_handler)
        assert is_valid is False
        assert "at least one parameter" in message

    def test_validate_handler_inspection_error(self):
        """Test validation handles inspection errors"""

        # Create a mock that will cause inspect.signature to fail
        mock_handler = MagicMock()
        mock_handler.__call__ = MagicMock()  # Make it callable

        # Make signature inspection fail
        import inspect

        original_signature = inspect.signature

        def failing_signature(obj):
            if obj is mock_handler:
                raise ValueError("Signature inspection failed")
            return original_signature(obj)

        inspect.signature = failing_signature

        try:
            is_valid, message = HandlerInspector.validate_handler(mock_handler)
            assert is_valid is False
            assert "Failed to inspect" in message
        finally:
            inspect.signature = original_signature

    def test_inspect_handler_complete_legacy(self):
        """Test complete inspection of legacy handler"""

        async def legacy_handler(event, ctx):
            pass

        info = HandlerInspector.inspect_handler(legacy_handler)

        assert info["style"] == HandlerStyle.LEGACY
        assert info["dependencies"] == []  # Legacy style has no explicit dependencies
        assert info["parameter_names"] == ["event", "ctx"]
        assert info["is_async"] is True
        assert info["is_valid"] is True
        assert info["validation_message"] == ""
        assert info["handler_name"] == "legacy_handler"

    def test_inspect_handler_complete_explicit(self):
        """Test complete inspection of explicit dependency handler"""

        async def explicit_handler(event: MockEvent, twitch: MockTwitchClient, logger: MockLogger):
            pass

        info = HandlerInspector.inspect_handler(explicit_handler)

        assert info["style"] == HandlerStyle.EXPLICIT
        assert info["dependencies"] == [MockTwitchClient, MockLogger]
        assert info["parameter_names"] == ["event", "twitch", "logger"]
        assert info["is_async"] is True
        assert info["is_valid"] is True
        assert info["validation_message"] == ""
        assert info["handler_name"] == "explicit_handler"

    def test_inspect_handler_sync_with_warning(self):
        """Test complete inspection includes sync handler warning"""

        def sync_explicit_handler(event: MockEvent, twitch: MockTwitchClient):
            pass

        info = HandlerInspector.inspect_handler(sync_explicit_handler)

        assert info["style"] == HandlerStyle.EXPLICIT
        assert info["dependencies"] == [MockTwitchClient]
        assert info["is_async"] is False
        assert info["is_valid"] is True
        assert "Warning" in info["validation_message"]

    def test_inspect_handler_invalid(self):
        """Test complete inspection of invalid handler"""

        not_a_handler = "not callable"

        info = HandlerInspector.inspect_handler(not_a_handler)

        assert info["style"] == HandlerStyle.EXPLICIT  # Default for invalid handlers
        assert info["dependencies"] == []
        assert info["parameter_names"] == []
        assert info["is_async"] is False
        assert info["is_valid"] is False
        assert "must be callable" in info["validation_message"]
        assert info["handler_name"] == "unknown"
