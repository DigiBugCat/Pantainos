"""
Database repositories for Pantainos

Generic repositories provide a clean interface for data access operations,
hiding the underlying database implementation details.
"""

from .auth_repository import AuthRepository
from .base import BaseRepository
from .event_repository import EventRepository
from .secure_storage_repository import SecureStorageRepository
from .user_repository import UserRepository
from .variable_repository import VariableRepository

__all__ = [
    "AuthRepository",
    "BaseRepository",
    "EventRepository",
    "SecureStorageRepository",
    "UserRepository",
    "VariableRepository",
]
