# tests/conftest.py
import uuid

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import delete

from backend import security
from backend.db import SessionLocal
from backend.main import app
from backend.models import ResearchJob, User


@pytest.fixture
def client():
    # Not used with "with", so the app's startup hook does not run.
    # That keeps the tests from touching the worker or cleaning real jobs.
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


@pytest.fixture
def test_user():
    """Create a unique user for one test, then delete it afterwards.

    Deleting the user also deletes their jobs, through the database cascade.
    """
    email = f"test-{uuid.uuid4().hex[:12]}@example.com"
    password = "test-password-123"

    db = SessionLocal()
    try:
        user = User(email=email, password_hash=security.hash_password(password))
        db.add(user)
        db.commit()
        db.refresh(user)
        user_info = {"id": user.id, "email": email, "password": password}
    finally:
        db.close()

    yield user_info

    db = SessionLocal()
    try:
        db.execute(delete(User).where(User.id == user_info["id"]))
        db.commit()
    finally:
        db.close()


@pytest.fixture
def auth_headers(test_user):
    """Authorization header for the test user, ready to pass to requests."""
    token = security.create_access_token(test_user["id"])
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def auth_client(client, auth_headers):
    """A test client that is logged in as the test user."""
    client.headers.update(auth_headers)
    return client