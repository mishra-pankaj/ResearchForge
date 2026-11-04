# backend/limits.py
import os
from datetime import datetime, timedelta, timezone

from sqlalchemy import func
from sqlalchemy.orm import Session

from backend.models import ResearchJob

GLOBAL_DAILY_JOB_CAP = int(os.getenv("GLOBAL_DAILY_JOB_CAP", "15"))
WINDOW = timedelta(hours=24)
ACTIVE_STATUSES = ("queued", "running")


def now() -> datetime:
    """Current UTC time. Tests replace this to move time forward."""
    return datetime.now(timezone.utc)


def jobs_in_window(db: Session) -> int:
    """Count every accepted job, from any user, in the last 24 hours."""
    cutoff = now() - WINDOW
    return (
        db.query(func.count(ResearchJob.id))
        .filter(ResearchJob.created_at >= cutoff)
        .scalar()
    )


def global_cap_reached(db: Session) -> bool:
    return jobs_in_window(db) >= GLOBAL_DAILY_JOB_CAP


def user_has_active_job(db: Session, user_id) -> bool:
    return (
        db.query(ResearchJob.id)
        .filter(ResearchJob.user_id == user_id)
        .filter(ResearchJob.status.in_(ACTIVE_STATUSES))
        .first()
        is not None
    )