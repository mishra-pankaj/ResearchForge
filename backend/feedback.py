# backend/feedback.py
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from backend.auth import get_current_user
from backend.db import get_db
from backend.models import Feedback, ResearchJob, User
from backend.schemas import FeedbackCreate, FeedbackOut

router = APIRouter(prefix="/research", tags=["feedback"])


def get_owned_job(db: Session, job_id: uuid.UUID, user: User) -> ResearchJob:
    """Return the job only if it belongs to this user. Otherwise 404."""
    job = db.get(ResearchJob, job_id)
    if job is None or job.user_id != user.id:
        raise HTTPException(status_code=404, detail="Research job not found")
    return job


@router.post("/{job_id}/feedback", response_model=FeedbackOut, status_code=201)
def create_feedback(
    job_id: uuid.UUID,
    body: FeedbackCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    job = get_owned_job(db, job_id, current_user)

    if job.status != "done":
        raise HTTPException(
            status_code=409,
            detail="Feedback can only be given once the report is finished",
        )

    existing = (
        db.query(Feedback)
        .filter(Feedback.user_id == current_user.id, Feedback.job_id == job_id)
        .first()
    )
    if existing is not None:
        raise HTTPException(
            status_code=409,
            detail="You have already given feedback on this report",
        )

    row = Feedback(
        user_id=current_user.id,
        job_id=job_id,
        kind=body.kind,
        message=body.message,
    )
    db.add(row)
    try:
        db.commit()
    except IntegrityError:
        # A concurrent request saved feedback between the check and the insert.
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="You have already given feedback on this report",
        )
    db.refresh(row)
    return row


@router.get("/{job_id}/feedback", response_model=FeedbackOut)
def get_feedback(
    job_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    get_owned_job(db, job_id, current_user)

    row = (
        db.query(Feedback)
        .filter(Feedback.user_id == current_user.id, Feedback.job_id == job_id)
        .first()
    )
    if row is None:
        raise HTTPException(status_code=404, detail="No feedback given yet")
    return row