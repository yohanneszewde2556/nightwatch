"""Pytest fixtures for demo-shop test suite."""
import os
import sys
from typing import Generator

import pytest
from fastapi.testclient import TestClient

# Ensure sample-app root is in python path
current_dir = os.path.dirname(os.path.abspath(__file__))
sample_app_dir = os.path.dirname(current_dir)
if sample_app_dir not in sys.path:
    sys.path.insert(0, sample_app_dir)

from app.config import settings
from app.logs import log_buffer
from app.main import app
from app.state import state


@pytest.fixture(autouse=True)
def reset_app_state() -> Generator[None, None, None]:
    """Reset app state, disable background traffic, and clear log buffer before each test."""
    settings.TRAFFIC_ENABLED = False
    state.reset()
    log_buffer.clear()
    yield
    state.reset()
    log_buffer.clear()


@pytest.fixture
def client() -> Generator[TestClient, None, None]:
    """Test client instance."""
    with TestClient(app, raise_server_exceptions=False) as c:
        yield c


@pytest.fixture
def admin_headers() -> dict[str, str]:
    """Valid admin authentication headers."""
    return {"X-Admin-Token": settings.ADMIN_TOKEN}
