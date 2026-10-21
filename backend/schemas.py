# backend/schemas.py
import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator,EmailStr


JobStatus = Literal["queued", "running", "done", "failed"]


class ResearchCreate(BaseModel):
    """Request body for POST /research."""
    topic: str = Field(..., min_length=3, max_length=300)

    @field_validator("topic")
    @classmethod
    def strip_topic(cls, value: str) -> str:
        value = value.strip()
        if len(value) < 3:
            raise ValueError("topic must be at least 3 characters after trimming")
        return value


class ResearchCreated(BaseModel):
    """Response after a job is submitted."""
    id: uuid.UUID
    status: JobStatus


class ResearchStatus(BaseModel):
    """Response for GET /research/{id} while the job is in progress."""
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    topic: str
    status: JobStatus
    current_step: str | None = None
    error: str | None = None
    created_at: datetime
    finished_at: datetime | None = None


class Review(BaseModel):
    score: int | None = None
    text: str = ""


class ScrapedSource(BaseModel):
    url: str
    ok: bool
    text: str


class ResearchResult(BaseModel):
    """Response for GET /research/{id} once the job is done."""
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    topic: str
    status: JobStatus
    llm_provider: str | None = None
    llm_model: str | None = None
    created_at: datetime
    finished_at: datetime | None = None
    sources: list[str] = []
    scraped: list[ScrapedSource] = []
    report: str = ""
    review: Review = Review()


class ResearchListItem(BaseModel):
    """One row in GET /research (history list)."""
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    topic: str
    status: JobStatus
    created_at: datetime

class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)

    @field_validator("email")
    @classmethod
    def lowercase_email(cls, value: str) -> str:
        return value.strip().lower()


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    email: str