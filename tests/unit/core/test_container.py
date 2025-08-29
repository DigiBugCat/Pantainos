"""
Unit tests for ServiceContainer dependency injection functionality
"""

import pytest

from pantainos.core.di.container import ServiceContainer


class MockService:
    """Mock service for testing"""

    def __init__(self, value: str = "default"):
        self.value = value


class AnotherMockService:
    """Another mock service for testing"""

    def __init__(self, name: str = "test"):
        self.name = name


class TestServiceContainer:
    """Test cases for ServiceContainer"""

    def test_singleton_registration_and_resolution(self):
        """Test that singleton services can be registered and resolved"""
        container = ServiceContainer()
        service_instance = MockService("singleton")

        # Register singleton
        container.register_singleton(MockService, service_instance)

        # Resolve should return the same instance
        resolved = container.resolve(MockService)
        assert resolved is service_instance
        assert resolved.value == "singleton"

    def test_factory_registration_and_resolution(self):
        """Test that factory services can be registered and create new instances"""
        container = ServiceContainer()

        # Register factory
        container.register_factory(MockService, lambda: MockService("factory"))

        # Resolve should return new instances each time
        resolved1 = container.resolve(MockService)
        resolved2 = container.resolve(MockService)

        assert resolved1 is not resolved2  # Different instances
        assert resolved1.value == "factory"
        assert resolved2.value == "factory"

    def test_singleton_takes_precedence_over_factory(self):
        """Test that singleton registration takes precedence over factory"""
        container = ServiceContainer()
        singleton_instance = MockService("singleton")

        # Register both factory and singleton for same type
        container.register_factory(MockService, lambda: MockService("factory"))
        container.register_singleton(MockService, singleton_instance)

        # Should resolve to singleton
        resolved = container.resolve(MockService)
        assert resolved is singleton_instance
        assert resolved.value == "singleton"

    def test_keyerror_raised_for_unregistered_service(self):
        """Test that KeyError is raised when resolving unregistered service"""
        container = ServiceContainer()

        with pytest.raises(KeyError) as exc_info:
            container.resolve(MockService)

        assert "MockService" in str(exc_info.value)
        assert "is not registered" in str(exc_info.value)

    def test_is_registered_for_singleton_services(self):
        """Test is_registered method works for singleton services"""
        container = ServiceContainer()
        service_instance = MockService()

        # Should not be registered initially
        assert not container.is_registered(MockService)

        # Register and check
        container.register_singleton(MockService, service_instance)
        assert container.is_registered(MockService)

        # Other types should not be registered
        assert not container.is_registered(AnotherMockService)

    def test_is_registered_for_factory_services(self):
        """Test is_registered method works for factory services"""
        container = ServiceContainer()

        # Should not be registered initially
        assert not container.is_registered(MockService)

        # Register factory and check
        container.register_factory(MockService, lambda: MockService())
        assert container.is_registered(MockService)

        # Other types should not be registered
        assert not container.is_registered(AnotherMockService)

    def test_get_registered_types_empty_container(self):
        """Test get_registered_types returns empty set for empty container"""
        container = ServiceContainer()

        registered_types = container.get_registered_types()
        assert registered_types == set()

    def test_get_registered_types_with_services(self):
        """Test get_registered_types returns correct set of registered types"""
        container = ServiceContainer()

        # Register different types
        container.register_singleton(MockService, MockService())
        container.register_factory(AnotherMockService, lambda: AnotherMockService())

        registered_types = container.get_registered_types()
        expected_types = {MockService, AnotherMockService}

        assert registered_types == expected_types

    def test_clear_removes_all_services(self):
        """Test clear method removes all registered services"""
        container = ServiceContainer()

        # Register services
        container.register_singleton(MockService, MockService())
        container.register_factory(AnotherMockService, lambda: AnotherMockService())

        # Verify they are registered
        assert container.is_registered(MockService)
        assert container.is_registered(AnotherMockService)
        assert len(container.get_registered_types()) == 2

        # Clear and verify empty
        container.clear()
        assert not container.is_registered(MockService)
        assert not container.is_registered(AnotherMockService)
        assert len(container.get_registered_types()) == 0

    def test_repr_method_empty_container(self):
        """Test repr method for empty container"""
        container = ServiceContainer()

        repr_str = repr(container)
        assert repr_str == "ServiceContainer(singletons=0, factories=0)"

    def test_repr_method_with_services(self):
        """Test repr method with registered services"""
        container = ServiceContainer()

        # Register one singleton and one factory
        container.register_singleton(MockService, MockService())
        container.register_factory(AnotherMockService, lambda: AnotherMockService())

        repr_str = repr(container)
        assert repr_str == "ServiceContainer(singletons=1, factories=1)"

    def test_multiple_service_types(self):
        """Test registering and resolving multiple different service types"""
        container = ServiceContainer()

        # Register different services
        mock_service = MockService("test")
        container.register_singleton(MockService, mock_service)
        container.register_factory(AnotherMockService, lambda: AnotherMockService("created"))

        # Resolve both
        resolved_mock = container.resolve(MockService)
        resolved_another = container.resolve(AnotherMockService)

        assert resolved_mock is mock_service
        assert resolved_mock.value == "test"
        assert resolved_another.name == "created"

    def test_factory_can_be_called_multiple_times(self):
        """Test that factory functions can be called multiple times"""
        container = ServiceContainer()
        call_count = 0

        def counting_factory():
            nonlocal call_count
            call_count += 1
            return MockService(f"call_{call_count}")

        container.register_factory(MockService, counting_factory)

        # Resolve multiple times
        service1 = container.resolve(MockService)
        service2 = container.resolve(MockService)
        service3 = container.resolve(MockService)

        assert service1.value == "call_1"
        assert service2.value == "call_2"
        assert service3.value == "call_3"
        assert call_count == 3
