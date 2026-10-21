# backend/auth.py
import uuid

import jwt
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from backend import security
from backend.db import get_db
from backend.models import User
from backend.schemas import LoginRequest, RegisterRequest, TokenResponse, UserPublic

router = APIRouter(prefix="/auth", tags=["auth"])
bearer = HTTPBearer(auto_error=False)

INVALID_LOGIN = "Invalid email or password"


@router.post("/register", response_model=UserPublic, status_code=201)
def register(body: RegisterRequest, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.email == body.email).first()
    if existing:
        raise HTTPException(status_code=409, detail="This email is already registered")

    user = User(email=body.email, password_hash=security.hash_password(body.password))
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.post("/login", response_model=TokenResponse)
def login(body: LoginRequest, db: Session = Depends(get_db)):
    email = body.email.strip().lower()
    user = db.query(User).filter(User.email == email).first()

    # Same message for unknown email and wrong password.
    if user is None or not security.verify_password(body.password, user.password_hash):
        raise HTTPException(status_code=401, detail=INVALID_LOGIN)

    return TokenResponse(access_token=security.create_access_token(user.id))


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer),
    db: Session = Depends(get_db),
) -> User:
    unauthorized = HTTPException(
        status_code=401,
        detail="Not authenticated",
        headers={"WWW-Authenticate": "Bearer"},
    )
    if credentials is None:
        raise unauthorized

    try:
        user_id = uuid.UUID(security.decode_access_token(credentials.credentials))
    except (jwt.InvalidTokenError, ValueError):
        raise unauthorized

    user = db.get(User, user_id)
    if user is None:
        raise unauthorized
    return user


@router.get("/me", response_model=UserPublic)
def me(current_user: User = Depends(get_current_user)):
    return current_user