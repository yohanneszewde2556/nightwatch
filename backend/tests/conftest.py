"""Pytest configuration and test fixtures."""

import os
import tempfile
import uuid
import pytest
from fastapi.testclient import TestClient

from app.api.deps import get_storage
from app.core.config import settings
from app.main import app
from app.storage.sqlite import SQLiteRepository
from app.storage.seed_data import seed_database


@pytest.fixture(scope="session")
def session_db_path():
    """Create a temporary SQLite database file for the test session."""
    filename = f"test_nightwatch_{uuid.uuid4().hex}.db"
    db_path = os.path.join(tempfile.gettempdir(), filename)
    yield db_path
    try:
        if os.path.exists(db_path):
            os.remove(db_path)
    except Exception:
        pass


@pytest.fixture(scope="function")
def test_storage(session_db_path):
    """Provide a freshly reset and seeded SQLite test storage instance."""
    storage = SQLiteRepository(db_path=session_db_path)
    # Clear all data across tables
    with storage._get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM incident_events;")
        cursor.execute("DELETE FROM incidents;")
        cursor.execute("DELETE FROM checks;")
        cursor.execute("DELETE FROM services;")
        cursor.execute("DELETE FROM runbooks;")
        cursor.execute("DELETE FROM audit_logs;")
        cursor.execute("UPDATE settings SET kill_switch = 0, notification_targets = '{}', daily_gemini_budget = 100;")
        conn.commit()

    seed_database(storage)
    return storage


@pytest.fixture(scope="function")
def client(test_storage):
    """FastAPI TestClient with test storage dependency override."""
    app.dependency_overrides[get_storage] = lambda: test_storage
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def auth_headers():
    """Valid dashboard authentication headers."""
    return {"Authorization": f"Bearer {settings.DASHBOARD_PASSWORD}"}
