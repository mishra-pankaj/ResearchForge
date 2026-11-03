# tests/test_feedback.py
import uuid

import pytest
from sqlalchemy import delete, func
from sqlalchemy.exc import IntegrityError

from backend import jobs, security
from backend.db import SessionLocal
from backend.models import Feedback, ResearchJob, User


@pytest.fixture(autouse=True)
def no_worker(monkeypatch):
    """Keep jobs from running the real pipeline during these tests."""
    monkeypatch.setattr(jobs, "enqueue_job", lambda job_id: None)


def insert_job(created_ids, owner_id, status="done", topic="feedback test topic"):
    db = SessionLocal()
    try:
        job = ResearchJob(topic=topic, status=status, user_id=owner_id)
        db.add(job)
        db.commit()
        db.refresh(job)
        created_ids.append(job.id)
        return job.id
    finally:
        db.close()


def insert_feedback(owner_id, job_id, kind="up", message="direct insert"):
    db = SessionLocal()
    try:
        row = Feedback(user_id=owner_id, job_id=job_id, kind=kind, message=message)
        db.add(row)
        db.commit()
        db.refresh(row)
        return row.id
    finally:
        db.close()


def count_feedback(job_id):
    db = SessionLocal()
    try:
        return db.query(func.count(Feedback.id)).filter(Feedback.job_id == job_id).scalar()
    finally:
        db.close()


def _make_stranger():
    db = SessionLocal()
    try:
        user = User(
            email=f"stranger-{uuid.uuid4().hex[:10]}@example.com",
            password_hash=security.hash_password("another-password-1"),
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        return {"id": user.id}
    finally:
        db.close()


def _remove_user(user_id):
    db = SessionLocal()
    try:
        db.execute(delete(User).where(User.id == user_id))
        db.commit()
    finally:
        db.close()


# ---------- POST /research/{id}/feedback ----------

def test_post_creates_feedback_for_finished_job(auth_client, created_ids, test_user):
    job_id = insert_job(created_ids, test_user["id"])

    response = auth_client.post(
        f"/research/{job_id}/feedback",
        json={"kind": "up", "message": "clear report"},
    )

    assert response.status_code == 201
    body = response.json()
    assert body["kind"] == "up"
    assert body["message"] == "clear report"
    assert body["job_id"] == str(job_id)


def test_post_trims_message(auth_client, created_ids, test_user):
    job_id = insert_job(created_ids, test_user["id"])

    response = auth_client.post(
        f"/research/{job_id}/feedback",
        json={"kind": "down", "message": "   missing sources   "},
    )

    assert response.status_code == 201
    assert response.json()["message"] == "missing sources"


def test_post_second_time_returns_409(auth_client, created_ids, test_user):
    job_id = insert_job(created_ids, test_user["id"])
    auth_client.post(f"/research/{job_id}/feedback", json={"kind": "up", "message": "first"})

    response = auth_client.post(
        f"/research/{job_id}/feedback", json={"kind": "down", "message": "second"}
    )

    assert response.status_code == 409
    assert response.json()["detail"] == "You have already given feedback on this report"


def test_post_on_queued_job_returns_409(auth_client, created_ids, test_user):
    job_id = insert_job(created_ids, test_user["id"], status="queued")

    response = auth_client.post(
        f"/research/{job_id}/feedback", json={"kind": "up", "message": "too early"}
    )

    assert response.status_code == 409
    assert response.json()["detail"] == "Feedback can only be given once the report is finished"


def test_post_on_running_job_returns_409(auth_client, created_ids, test_user):
    job_id = insert_job(created_ids, test_user["id"], status="running")

    response = auth_client.post(
        f"/research/{job_id}/feedback", json={"kind": "up", "message": "still going"}
    )

    assert response.status_code == 409


def test_post_on_failed_job_returns_409(auth_client, created_ids, test_user):
    job_id = insert_job(created_ids, test_user["id"], status="failed")

    response = auth_client.post(
        f"/research/{job_id}/feedback", json={"kind": "down", "message": "it failed"}
    )

    assert response.status_code == 409


def test_post_on_other_users_job_returns_404(client, created_ids, test_user):
    owner_job = insert_job(created_ids, test_user["id"])

    stranger = _make_stranger()
    try:
        client.headers.update({
            "Authorization": f"Bearer {security.create_access_token(stranger['id'])}"
        })
        response = client.post(
            f"/research/{owner_job}/feedback", json={"kind": "up", "message": "not mine"}
        )
        assert response.status_code == 404
    finally:
        _remove_user(stranger["id"])


def test_post_with_invalid_kind_returns_422(auth_client, created_ids, test_user):
    job_id = insert_job(created_ids, test_user["id"])

    response = auth_client.post(
        f"/research/{job_id}/feedback", json={"kind": "maybe", "message": "x"}
    )

    assert response.status_code == 422


def test_post_with_blank_message_returns_422(auth_client, created_ids, test_user):
    job_id = insert_job(created_ids, test_user["id"])

    response = auth_client.post(
        f"/research/{job_id}/feedback", json={"kind": "up", "message": "   "}
    )

    assert response.status_code == 422


def test_post_with_message_over_1000_chars_returns_422(auth_client, created_ids, test_user):
    job_id = insert_job(created_ids, test_user["id"])

    response = auth_client.post(
        f"/research/{job_id}/feedback", json={"kind": "up", "message": "x" * 1001}
    )

    assert response.status_code == 422


def test_post_without_token_returns_401(client, created_ids, test_user):
    job_id = insert_job(created_ids, test_user["id"])

    response = client.post(
        f"/research/{job_id}/feedback", json={"kind": "up", "message": "no token"}
    )

    assert response.status_code == 401


# ---------- GET /research/{id}/feedback ----------

def test_get_returns_saved_feedback(auth_client, created_ids, test_user):
    job_id = insert_job(created_ids, test_user["id"])
    auth_client.post(
        f"/research/{job_id}/feedback", json={"kind": "up", "message": "helpful"}
    )

    response = auth_client.get(f"/research/{job_id}/feedback")

    assert response.status_code == 200
    body = response.json()
    assert body["kind"] == "up"
    assert body["message"] == "helpful"


def test_get_without_feedback_returns_404(auth_client, created_ids, test_user):
    job_id = insert_job(created_ids, test_user["id"])

    response = auth_client.get(f"/research/{job_id}/feedback")

    assert response.status_code == 404


def test_get_on_other_users_job_returns_404(client, created_ids, test_user):
    owner_job = insert_job(created_ids, test_user["id"])
    insert_feedback(test_user["id"], owner_job)

    stranger = _make_stranger()
    try:
        client.headers.update({
            "Authorization": f"Bearer {security.create_access_token(stranger['id'])}"
        })
        response = client.get(f"/research/{owner_job}/feedback")
        assert response.status_code == 404
    finally:
        _remove_user(stranger["id"])


# ---------- Database rules ----------

def test_unique_constraint_blocks_second_row_for_same_user_and_job(created_ids, test_user):
    job_id = insert_job(created_ids, test_user["id"])
    insert_feedback(test_user["id"], job_id)

    db = SessionLocal()
    try:
        db.add(Feedback(user_id=test_user["id"], job_id=job_id, kind="down", message="dup"))
        with pytest.raises(IntegrityError):
            db.commit()
        db.rollback()
    finally:
        db.close()

    assert count_feedback(job_id) == 1


def test_deleting_job_removes_its_feedback(created_ids, test_user):
    job_id = insert_job(created_ids, test_user["id"])
    insert_feedback(test_user["id"], job_id)
    assert count_feedback(job_id) == 1

    db = SessionLocal()
    try:
        db.execute(delete(ResearchJob).where(ResearchJob.id == job_id))
        db.commit()
    finally:
        db.close()

    assert count_feedback(job_id) == 0