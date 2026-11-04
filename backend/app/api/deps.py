"""FastAPI dependency injection utilities."""

from fastapi import Depends
from app.storage.base import BaseRepository
from app.storage import get_repository


def get_storage() -> BaseRepository:
    """Dependency that supplies the configured BaseRepository."""
    return get_repository()
