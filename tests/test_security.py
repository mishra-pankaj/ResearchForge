# tests/test_security.py
from datetime import datetime, timedelta, timezone

import jwt
import pytest

from backend import security


def test_password_round_trip():
    hashed = security.hash_password("correct-password")
    assert security.verify_password("correct-password", hashed)


def test_wrong_password_fails():
    hashed = security.hash_password("correct-password")
    assert not security.verify_password("wrong-password", hashed)


def test_hash_is_not_plain_password():
    hashed = security.hash_password("correct-password")
    assert hashed != "correct-password"
    assert hashed.startswith("$2")  # bcrypt format


def test_token_round_trip():
    token = security.create_access_token("11111111-2222-3333-4444-555555555555")
    assert security.decode_access_token(token) == "11111111-2222-3333-4444-555555555555"


def test_tampered_token_is_rejected():
    token = security.create_access_token("user-1")
    tampered = token[:-2] + ("aa" if token[-2:] != "aa" else "bb")
    with pytest.raises(jwt.InvalidTokenError):
        security.decode_access_token(tampered)


def test_expired_token_is_rejected():
    payload = {
        "sub": "user-1",
        "iat": datetime.now(timezone.utc) - timedelta(hours=48),
        "exp": datetime.now(timezone.utc) - timedelta(hours=24),
    }
    expired = jwt.encode(payload, security.JWT_SECRET, algorithm=security.JWT_ALGORITHM)
    with pytest.raises(jwt.ExpiredSignatureError):
        security.decode_access_token(expired)