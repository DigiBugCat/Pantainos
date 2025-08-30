"""
Dependency Injection Service Container

This module provides a lightweight service container for registering and resolving
dependencies in Pantainos handlers.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, TypeVar, cast

if TYPE_CHECKING:
    from collections.abc import Callable

T = TypeVar("T")


class ServiceContainer:
    """
    A lightweight dependency injection container that supports both singleton
    instances and factory functions for creating services.
    """

    def __init__(self) -> None:
        self._singletons: dict[type, Any] = {}
        self._factories: dict[type, Callable[[], Any]] = {}

    def register_singleton(self, service_type: type[T], instance: T) -> None:
        """
        Register a singleton service instance.

        Args:
            service_type: The type/interface that this service implements
            instance: The actual service instance

        Example:
            container.register_singleton(TwitchClient, twitch_client_instance)
        """
        self._singletons[service_type] = instance

    def register_factory(self, service_type: type[T], factory: Callable[[], T]) -> None:
        """
        Register a factory function for creating service instances.

        Args:
            service_type: The type/interface that this service implements
            factory: A callable that returns a new service instance

        Example:
            container.register_factory(Logger, lambda: logging.getLogger("pantainos"))
        """
        self._factories[service_type] = factory

    def resolve(self, service_type: type[T]) -> T:
        """
        Resolve a service by its type.

        Args:
            service_type: The type of service to resolve

        Returns:
            The service instance

        Raises:
            KeyError: If the service type is not registered

        Example:
            twitch_client = container.resolve(TwitchClient)
        """
        # Check singletons first
        if service_type in self._singletons:
            return cast("T", self._singletons[service_type])

        # Check factories
        if service_type in self._factories:
            factory = self._factories[service_type]
            return cast("T", factory())

        # Service not found
        raise KeyError(f"Service type {service_type.__name__} is not registered")

    def is_registered(self, service_type: type) -> bool:
        """
        Check if a service type is registered.

        Args:
            service_type: The type to check

        Returns:
            True if the service is registered, False otherwise
        """
        return service_type in self._singletons or service_type in self._factories

    def get_registered_types(self) -> set[type]:
        """
        Get all registered service types.

        Returns:
            Set of all registered service types
        """
        return set(self._singletons.keys()) | set(self._factories.keys())

    def clear(self) -> None:
        """Clear all registered services."""
        self._singletons.clear()
        self._factories.clear()

    def __repr__(self) -> str:
        singleton_count = len(self._singletons)
        factory_count = len(self._factories)
        return f"ServiceContainer(singletons={singleton_count}, factories={factory_count})"
