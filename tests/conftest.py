# tests/conftest.py
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import delete

from backend.db import SessionLocal
from backend.main import app
from backend.models import ResearchJob


@pytest.fixture
def client():
    # Not used with "with", so the app's startup hook does not run.
    # That keeps the test from touching the worker or cleaning real jobs.
    return TestClient(app)


@pytest.fixture
def created_ids():
    """Collect the ids of jobs a test creates, then delete them afterwards."""
    ids = []
    yield ids

    db = SessionLocal()
    try:
        if ids:
            db.execute(delete(ResearchJob).where(ResearchJob.id.in_(ids)))
            db.commit()
    finally:
        db.close()