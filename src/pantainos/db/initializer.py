"""
Database initialization and repository setup for Pantainos.

This module handles database connection setup and registers all
repository services with the dependency injection container.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from pantainos.core.di.container import ServiceContainer

logger = logging.getLogger(__name__)


class DatabaseInitializer:
    """
    Manages database initialization and repository registration.

    Handles database connection setup, repository creation,
    and dependency injection registration.
    """

    def __init__(self, container: ServiceContainer) -> None:
        """Initialize database initializer with DI container."""
        self.container = container
        self.database: Any | None = None

    async def initialize(self, database_url: str, master_key: str | None = None) -> Any:
        """
        Set up database connection and register repository services for dependency injection.

        Args:
            database_url: Database connection URL
            master_key: Master encryption key for secure storage (optional)

        Returns:
            Database instance

        Raises:
            RuntimeError: If database initialization fails
        """
        try:
            from .database import Database
            from .repositories.auth_repository import AuthRepository
            from .repositories.event_repository import EventRepository
            from .repositories.secure_storage_repository import SecureStorageRepository
            from .repositories.user_repository import UserRepository
            from .repositories.variable_repository import VariableRepository

            self.database = Database(database_url)
            await self.database.initialize()

            # Create secure storage repository first (needed by auth repository)
            secure_storage_repo = SecureStorageRepository(self.database, master_key=master_key)

            # Make repositories available for injection
            self.container.register_singleton(SecureStorageRepository, secure_storage_repo)
            self.container.register_factory(AuthRepository, lambda: AuthRepository(secure_storage_repo))
            # Type assertion safe here since we just created database
            db = self.database
            assert db is not None
            self.container.register_factory(EventRepository, lambda: EventRepository(db))
            self.container.register_factory(UserRepository, lambda: UserRepository(db))
            self.container.register_factory(VariableRepository, lambda: VariableRepository(db))

            logger.info(f"Database initialized: {database_url}")
            return self.database

        except ImportError as e:
            logger.warning(f"Database components not available: {e}")
            # Allow app to run without a database
            raise
        except Exception as e:
            logger.error(f"Database initialization failed: {e}", exc_info=True)
            raise

    async def close(self) -> None:
        """Close database connection if open."""
        if self.database and hasattr(self.database, "close"):
            await self.database.close()
            logger.info("Database connection closed")
