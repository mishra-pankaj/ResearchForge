# tests/test_routes.py
import uuid

import pytest
from sqlalchemy import delete

from backend import jobs, security
from backend.db import SessionLocal
from backend.models import ResearchJob, User


@pytest.fixture(autouse=True)
def no_worker(monkeypatch):
    """Keep jobs queued so the real pipeline never runs during route tests."""
    monkeypatch.setattr(jobs, "enqueue_job", lambda job_id: None)


def create_job(auth_client, created_ids, topic="route test topic"):
    response = auth_client.post("/research", json={"topic": topic})
    assert response.status_code == 202
    job_id = uuid.UUID(response.json()["id"])
    created_ids.append(job_id)
    return job_id


def insert_job(created_ids, owner_id, **fields):
    """Insert a job row for a given owner, for tests that need a specific status."""
    db = SessionLocal()
    try:
        job = ResearchJob(
            topic=fields.pop("topic", "direct insert"),
            user_id=owner_id,
            **fields,
        )
        db.add(job)
        db.commit()
        db.refresh(job)
        created_ids.append(job.id)
        return job.id
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


# ---------- GET /health ----------

def test_health_reports_ok(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "database": "ok"}


# ---------- POST /research ----------

def test_create_returns_202_with_queued_status(auth_client, created_ids):
    response = auth_client.post("/research", json={"topic": "impact of war"})
    assert response.status_code == 202

    body = response.json()
    assert body["status"] == "queued"
    created_ids.append(uuid.UUID(body["id"]))


def test_create_saves_job_for_current_user(auth_client, created_ids, test_user):
    job_id = create_job(auth_client, created_ids)

    db = SessionLocal()
    try:
        job = db.get(ResearchJob, job_id)
        assert job.status == "queued"
        assert job.topic == "route test topic"
        assert job.user_id == test_user["id"]
        assert job.llm_provider is not None
        assert job.llm_model is not None
    finally:
        db.close()


def test_create_rejects_blank_topic(auth_client):
    response = auth_client.post("/research", json={"topic": "   "})
    assert response.status_code == 422


def test_create_rejects_missing_topic(auth_client):
    response = auth_client.post("/research", json={})
    assert response.status_code == 422


def test_create_without_token_returns_401(client):
    response = client.post("/research", json={"topic": "no token here"})
    assert response.status_code == 401


# ---------- GET /research/{id} ----------

def test_get_queued_job_returns_progress_view(auth_client, created_ids):
    job_id = create_job(auth_client, created_ids)

    response = auth_client.get(f"/research/{job_id}")
    assert response.status_code == 200

    body = response.json()
    assert body["status"] == "queued"
    assert "report" not in body
    assert "sources" not in body


def test_get_unknown_job_returns_404(auth_client):
    response = auth_client.get(f"/research/{uuid.uuid4()}")
    assert response.status_code == 404


def test_get_done_job_returns_full_result(auth_client, created_ids, test_user):
    job_id = insert_job(
        created_ids,
        test_user["id"],
        topic="finished topic",
        status="done",
        llm_provider="ollama",
        llm_model="qwen2.5:7b",
        result={
            "search_results": "search text",
            "scraped": [{"url": "https://a.example", "ok": True, "text": "page"}],
            "report": "the report",
            "review": {"score": 7, "text": "good"},
        },
    )

    response = auth_client.get(f"/research/{job_id}")
    assert response.status_code == 200

    body = response.json()
    assert body["report"] == "the report"
    assert body["sources"] == ["https://a.example"]
    assert body["review"]["score"] == 7


def test_get_failed_job_returns_error(auth_client, created_ids, test_user):
    job_id = insert_job(
        created_ids,
        test_user["id"],
        status="failed",
        error="something broke",
    )

    response = auth_client.get(f"/research/{job_id}")
    assert response.status_code == 200
    assert response.json()["error"] == "something broke"


def test_get_other_users_job_returns_404(auth_client, created_ids, test_user, client):
    owner_job = insert_job(created_ids, test_user["id"], status="done")

    stranger = _make_stranger()
    try:
        client.headers.update({
            "Authorization": f"Bearer {security.create_access_token(stranger['id'])}"
        })
        response = client.get(f"/research/{owner_job}")
        assert response.status_code == 404
    finally:
        _remove_user(stranger["id"])


# ---------- GET /research ----------

def test_list_returns_only_own_finished_jobs(auth_client, created_ids, test_user):
    queued_id = insert_job(created_ids, test_user["id"], topic="list queued", status="queued")
    done_id = insert_job(created_ids, test_user["id"], topic="list done", status="done")

    response = auth_client.get("/research", params={"limit": 100})
    assert response.status_code == 200

    ids = [item["id"] for item in response.json()]
    assert str(done_id) in ids
    assert str(queued_id) not in ids


def test_list_rejects_limit_over_100(auth_client):
    response = auth_client.get("/research", params={"limit": 101})
    assert response.status_code == 422


# ---------- DELETE /research/{id} ----------

def test_delete_finished_job_returns_204_then_404(auth_client, created_ids, test_user):
    job_id = insert_job(created_ids, test_user["id"], topic="to delete", status="done")

    assert auth_client.delete(f"/research/{job_id}").status_code == 204
    assert auth_client.get(f"/research/{job_id}").status_code == 404


def test_delete_unknown_job_returns_404(auth_client):
    response = auth_client.delete(f"/research/{uuid.uuid4()}")
    assert response.status_code == 404


def test_delete_running_job_returns_409(auth_client, created_ids, test_user):
    job_id = insert_job(created_ids, test_user["id"], topic="busy", status="running")

    response = auth_client.delete(f"/research/{job_id}")
    assert response.status_code == 409