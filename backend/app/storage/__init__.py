"""Storage package initialisation and repository factory."""

from functools import lru_cache
from app.core.config import settings
from app.storage.base import BaseRepository
from app.storage.firestore_stub import FirestoreRepository
from app.storage.sqlite import SQLiteRepository
from app.storage.seed_data import seed_database


@lru_cache(maxsize=1)
def get_repository() -> BaseRepository:
    """Return configured storage repository instance.

    Business logic and FastAPI route handlers depend only on BaseRepository.
    """
    if settings.STORAGE_BACKEND == "firestore":
        return FirestoreRepository()
    return SQLiteRepository(db_path=settings.SQLITE_DB_PATH)


__all__ = [
    "BaseRepository",
    "SQLiteRepository",
    "FirestoreRepository",
    "get_repository",
    "seed_database",
]
