# tests/test_limits.py
import uuid
from datetime import timedelta

import pytest
from sqlalchemy import delete

from backend import jobs, limits
from backend.db import SessionLocal
from backend.models import ResearchJob

HIGH_CAP = 10_000


@pytest.fixture(autouse=True)
def no_worker_and_high_cap(monkeypatch):
    """Keep jobs queued, and keep the global cap out of the way by default.

    The real database may already hold today's jobs, so tests that are not
    about the global cap use a cap far above that count.
    """
    monkeypatch.setattr(jobs, "enqueue_job", lambda job_id: None)
    monkeypatch.setattr(limits, "GLOBAL_DAILY_JOB_CAP", HIGH_CAP)


def window_count():
    db = SessionLocal()
    try:
        return limits.jobs_in_window(db)
    finally:
        db.close()


def cap_at(monkeypatch, value):
    monkeypatch.setattr(limits, "GLOBAL_DAILY_JOB_CAP", value)


def insert_job(owner_id, status="done", created_at=None):
    db = SessionLocal()
    try:
        job = ResearchJob(topic="limit test", status=status, user_id=owner_id)
        if created_at is not None:
            job.created_at = created_at
        db.add(job)
        db.commit()
        db.refresh(job)
        return job.id
    finally:
        db.close()


def remove_jobs(job_ids):
    db = SessionLocal()
    try:
        db.execute(delete(ResearchJob).where(ResearchJob.id.in_(job_ids)))
        db.commit()
    finally:
        db.close()


def test_one_active_job_per_user_returns_409(auth_client, created_ids):
    first = auth_client.post("/research", json={"topic": "first topic"})
    assert first.status_code == 202
    created_ids.append(uuid.UUID(first.json()["id"]))

    second = auth_client.post("/research", json={"topic": "second topic"})
    assert second.status_code == 409


def test_global_cap_returns_429(auth_client, monkeypatch):
    # Cap equal to today's count: the next accepted job must be refused.
    cap_at(monkeypatch, window_count())

    response = auth_client.post("/research", json={"topic": "over the cap"})

    assert response.status_code == 429
    assert "Retry-After" in response.headers


def test_rejected_request_creates_no_job(auth_client, monkeypatch):
    cap_at(monkeypatch, window_count())
    before = window_count()

    auth_client.post("/research", json={"topic": "rejected"})

    assert window_count() == before


def test_jobs_older_than_24_hours_do_not_count(
    auth_client, test_user, created_ids, monkeypatch
):
    # Cap is today's count plus one. If the old jobs counted, they would
    # push the total over the cap and the request would be refused.
    cap_at(monkeypatch, window_count() + 1)
    old_time = limits.now() - timedelta(hours=25)
    old_ids = [insert_job(test_user["id"], created_at=old_time) for _ in range(2)]
    try:
        response = auth_client.post("/research", json={"topic": "after the window"})
        assert response.status_code == 202
        created_ids.append(uuid.UUID(response.json()["id"]))
    finally:
        remove_jobs(old_ids)