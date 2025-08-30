"""
Tests for event models and the events system
"""

from pantainos.events import (
    ErrorEvent,
    GenericEvent,
    MetricEvent,
    PluginHealthEvent,
    SampleEvent,
    SystemEvent,
    SystemHealthEvent,
    WebhookEvent,
)


class TestGenericEvent:
    """Test GenericEvent class and its event_type property"""

    def test_generic_event_event_type_property(self):
        """Test that GenericEvent uses instance-specific event_type"""
        # Create two different GenericEvent instances
        event1 = GenericEvent(type="hello", data={"name": "World"})
        event2 = GenericEvent(type="timer.tick", data={})

        # Both events should have their own correct event types
        assert event1.event_type == "hello"
        assert event2.event_type == "timer.tick"

        # Creating more events shouldn't affect existing ones
        event3 = GenericEvent(type="user.login", data={"user_id": "123"})
        assert event1.event_type == "hello"
        assert event2.event_type == "timer.tick"
        assert event3.event_type == "user.login"

    def test_generic_event_data_field(self):
        """Test GenericEvent data field defaults and values"""
        # Test with data
        event_with_data = GenericEvent(type="test", data={"key": "value"})
        assert event_with_data.data == {"key": "value"}

        # Test without data (should default to empty dict)
        event_without_data = GenericEvent(type="test")
        assert event_without_data.data == {}

    def test_generic_event_source_field(self):
        """Test GenericEvent source field"""
        # Test default source
        event = GenericEvent(type="test")
        assert event.source == "system"

        # Test custom source
        event_custom = GenericEvent(type="test", source="web")
        assert event_custom.source == "web"


class TestEventModel:
    """Test EventModel base class functionality"""

    def test_event_model_conditions(self):
        """Test EventModel condition methods"""
        # Create a test event
        event = SystemEvent(action="startup", version="1.0.0", source="system")

        # Test source_is condition
        source_condition = SystemEvent.source_is("system")
        assert source_condition(event) is True

        wrong_source_condition = SystemEvent.source_is("web")
        assert wrong_source_condition(event) is False

        # Test has_field condition
        has_action_condition = SystemEvent.has_field("action")
        assert has_action_condition(event) is True

        has_nonexistent_condition = SystemEvent.has_field("nonexistent")
        assert has_nonexistent_condition(event) is False

        # Test field_equals condition
        action_startup_condition = SystemEvent.field_equals("action", "startup")
        assert action_startup_condition(event) is True

        action_wrong_condition = SystemEvent.field_equals("action", "shutdown")
        assert action_wrong_condition(event) is False


class TestSystemEvent:
    """Test SystemEvent class"""

    def test_system_event_creation(self):
        """Test SystemEvent creation and fields"""
        event = SystemEvent(
            action="startup",
            version="1.0.0",
            hostname="localhost",
            pid=12345,
            uptime=123.45,
            extra_metadata={"key": "value"},
        )

        assert event.event_type == "system"
        assert event.action == "startup"
        assert event.version == "1.0.0"
        assert event.hostname == "localhost"
        assert event.pid == 12345
        assert event.uptime == 123.45
        assert event.extra_metadata == {"key": "value"}

    def test_system_event_minimal(self):
        """Test SystemEvent with minimal required fields"""
        event = SystemEvent(action="shutdown")

        assert event.event_type == "system"
        assert event.action == "shutdown"
        assert event.version is None
        assert event.hostname is None
        assert event.pid is None
        assert event.uptime is None
        assert event.extra_metadata == {}


class TestSampleEvent:
    """Test SampleEvent class"""

    def test_sample_event_creation(self):
        """Test SampleEvent creation"""
        event = SampleEvent(message="Test message", data={"test": "data"})

        assert event.event_type == "test.event"
        assert event.message == "Test message"
        assert event.data == {"test": "data"}

    def test_sample_event_defaults(self):
        """Test SampleEvent with default values"""
        event = SampleEvent()

        assert event.event_type == "test.event"
        assert event.message == "Test message"
        assert event.data == {}


class TestWebhookEvent:
    """Test WebhookEvent class"""

    def test_webhook_event_creation(self):
        """Test WebhookEvent creation"""
        event = WebhookEvent(
            endpoint="/webhook/test", method="POST", headers={"Content-Type": "application/json"}, body={"data": "test"}
        )

        assert event.event_type == "webhook.received"
        assert event.endpoint == "/webhook/test"
        assert event.method == "POST"
        assert event.headers == {"Content-Type": "application/json"}
        assert event.body == {"data": "test"}

    def test_webhook_event_defaults(self):
        """Test WebhookEvent with default values"""
        event = WebhookEvent(endpoint="/webhook/test")

        assert event.event_type == "webhook.received"
        assert event.endpoint == "/webhook/test"
        assert event.method == "POST"
        assert event.headers == {}
        assert event.body == {}


class TestErrorEvent:
    """Test ErrorEvent class"""

    def test_error_event_creation(self):
        """Test ErrorEvent creation"""
        event = ErrorEvent(
            error="Test error message",
            error_type="ValueError",
            traceback="Test traceback",
            module="test_module",
            function="test_function",
            line_number=42,
            extra_context={"key": "value"},
        )

        assert event.event_type == "error"
        assert event.error == "Test error message"
        assert event.error_type == "ValueError"
        assert event.traceback == "Test traceback"
        assert event.module == "test_module"
        assert event.function == "test_function"
        assert event.line_number == 42
        assert event.extra_context == {"key": "value"}


class TestMetricEvent:
    """Test MetricEvent class"""

    def test_metric_event_creation(self):
        """Test MetricEvent creation"""
        event = MetricEvent(
            metrics={"cpu_usage": 75.5, "memory_usage": 60.2},
            tags={"host": "server1", "region": "us-east-1"},
            timestamp=1234567890.0,
        )

        assert event.event_type == "metric.update"
        assert event.metrics == {"cpu_usage": 75.5, "memory_usage": 60.2}
        assert event.tags == {"host": "server1", "region": "us-east-1"}
        assert event.timestamp == 1234567890.0


class TestHealthEvents:
    """Test health event classes"""

    def test_plugin_health_event_creation(self):
        """Test PluginHealthEvent creation"""
        event = PluginHealthEvent(
            plugin_name="test_plugin", status="healthy", message="All systems operational", details={"version": "1.0.0"}
        )

        assert event.event_type == "plugin.health"
        assert event.plugin_name == "test_plugin"
        assert event.status == "healthy"
        assert event.message == "All systems operational"
        assert event.details == {"version": "1.0.0"}

    def test_system_health_event_creation(self):
        """Test SystemHealthEvent creation"""
        event = SystemHealthEvent(
            overall_status="healthy",
            healthy_plugins=3,
            degraded_plugins=1,
            unhealthy_plugins=0,
            plugin_statuses={"plugin1": "healthy", "plugin2": "healthy", "plugin3": "degraded"},
            check_summary={"total_checks": 4, "uptime": 3600},
        )

        assert event.event_type == "system.health"
        assert event.overall_status == "healthy"
        assert event.healthy_plugins == 3
        assert event.degraded_plugins == 1
        assert event.unhealthy_plugins == 0
        assert event.plugin_statuses == {"plugin1": "healthy", "plugin2": "healthy", "plugin3": "degraded"}
        assert event.check_summary == {"total_checks": 4, "uptime": 3600}


class TestEventRegressions:
    """Regression tests to prevent known issues"""

    def test_multiple_generic_events_maintain_separate_event_types(self):
        """
        Regression test: Ensure multiple GenericEvent instances maintain
        their own event_type values without interfering with each other.

        This test prevents the regression where GenericEvent.event_type was
        a class variable that got overwritten by each instance.
        """
        # Create events in sequence like the hello world example
        hello_event = GenericEvent(type="hello", data={"name": "Pantainos"})
        timer_event = GenericEvent(type="timer.tick", data={})

        # Both events should maintain their correct types
        assert hello_event.event_type == "hello"
        assert timer_event.event_type == "timer.tick"

        # Create more events to stress test
        events = [GenericEvent(type=f"test.event.{i}", data={"index": i}) for i in range(10)]

        # All events should have their correct types
        for i, event in enumerate(events):
            assert event.event_type == f"test.event.{i}"

        # Original events should still be correct
        assert hello_event.event_type == "hello"
        assert timer_event.event_type == "timer.tick"
