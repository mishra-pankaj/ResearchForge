# tests/test_auth.py
import uuid

import pytest
from sqlalchemy import delete

from backend import security
from backend.db import SessionLocal
from backend.models import User

PASSWORD = "strong-password-123"


@pytest.fixture
def registered_emails():
    """Collect emails registered during a test, then delete those users afterwards."""
    emails = []
    yield emails

    db = SessionLocal()
    try:
        if emails:
            db.execute(delete(User).where(User.email.in_(emails)))
            db.commit()
    finally:
        db.close()


def unique_email(prefix="auth"):
    return f"{prefix}-{uuid.uuid4().hex[:12]}@example.com"


def make_user(client, registered_emails):
    """Register a user through the API and return the email."""
    email = unique_email()
    registered_emails.append(email)
    response = client.post("/auth/register", json={"email": email, "password": PASSWORD})
    assert response.status_code == 201
    return email


# ---------- POST /auth/register ----------

def test_register_creates_user_and_returns_201(client, registered_emails):
    email = unique_email()
    registered_emails.append(email)

    response = client.post("/auth/register", json={"email": email, "password": PASSWORD})

    assert response.status_code == 201
    body = response.json()
    assert body["email"] == email
    assert "id" in body
    assert "access_token" not in body
    assert "password" not in body
    assert "password_hash" not in body


def test_register_stores_only_a_hash(client, registered_emails):
    email = make_user(client, registered_emails)

    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == email).one()
        assert user.password_hash != PASSWORD
        assert user.password_hash.startswith("$2")
    finally:
        db.close()


def test_register_normalizes_email_to_lowercase(client, registered_emails):
    email = unique_email()
    registered_emails.append(email)

    response = client.post(
        "/auth/register", json={"email": email.upper(), "password": PASSWORD}
    )

    assert response.status_code == 201
    assert response.json()["email"] == email


def test_register_duplicate_email_returns_409(client, registered_emails):
    email = make_user(client, registered_emails)

    response = client.post("/auth/register", json={"email": email, "password": PASSWORD})

    assert response.status_code == 409


def test_register_duplicate_is_case_insensitive(client, registered_emails):
    email = make_user(client, registered_emails)

    response = client.post(
        "/auth/register", json={"email": email.upper(), "password": PASSWORD}
    )

    assert response.status_code == 409


def test_register_rejects_invalid_email(client):
    response = client.post(
        "/auth/register", json={"email": "not-an-email", "password": PASSWORD}
    )
    assert response.status_code == 422


def test_register_rejects_short_password(client):
    response = client.post(
        "/auth/register", json={"email": unique_email(), "password": "short"}
    )
    assert response.status_code == 422


def test_register_rejects_missing_password(client):
    response = client.post("/auth/register", json={"email": unique_email()})
    assert response.status_code == 422


# ---------- POST /auth/login ----------

def test_login_returns_token_for_correct_password(client, registered_emails):
    email = make_user(client, registered_emails)

    response = client.post("/auth/login", json={"email": email, "password": PASSWORD})

    assert response.status_code == 200
    body = response.json()
    assert body["token_type"] == "bearer"
    assert body["access_token"]


def test_login_accepts_uppercase_email(client, registered_emails):
    email = make_user(client, registered_emails)

    response = client.post(
        "/auth/login", json={"email": email.upper(), "password": PASSWORD}
    )

    assert response.status_code == 200


def test_login_wrong_password_returns_401(client, registered_emails):
    email = make_user(client, registered_emails)

    response = client.post(
        "/auth/login", json={"email": email, "password": "wrong-password"}
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid email or password"


def test_login_unknown_email_returns_same_401_message(client):
    response = client.post(
        "/auth/login", json={"email": unique_email("nobody"), "password": PASSWORD}
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid email or password"


# ---------- GET /auth/me ----------

def test_me_returns_current_user_with_valid_token(client, registered_emails):
    email = make_user(client, registered_emails)
    token = client.post(
        "/auth/login", json={"email": email, "password": PASSWORD}
    ).json()["access_token"]

    response = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 200
    assert response.json()["email"] == email


def test_me_without_token_returns_401(client):
    response = client.get("/auth/me")
    assert response.status_code == 401


def test_me_with_bad_token_returns_401(client):
    response = client.get(
        "/auth/me", headers={"Authorization": "Bearer not-a-real-token"}
    )
    assert response.status_code == 401


def test_me_with_token_for_missing_user_returns_401(client):
    # A valid signature, but no user row exists for this id.
    token = security.create_access_token(uuid.uuid4())

    response = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 401