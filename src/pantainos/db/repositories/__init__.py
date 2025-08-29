"""
Database repositories for Pantainos

Generic repositories provide a clean interface for data access operations,
hiding the underlying database implementation details.
"""

from .base import BaseRepository
from .event_repository import EventRepository
from .variable_repository import VariableRepository

__all__ = ["BaseRepository", "EventRepository", "VariableRepository"]
