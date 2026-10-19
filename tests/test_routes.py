# tests/test_routes.py
import uuid

import pytest

from backend import jobs
from backend.db import SessionLocal
from backend.models import ResearchJob


@pytest.fixture(autouse=True)
def no_worker(monkeypatch):
    """Keep jobs queued so the real pipeline never runs during route tests."""
    monkeypatch.setattr(jobs, "enqueue_job", lambda job_id: None)


def create_job(client, created_ids, topic="route test topic"):
    response = client.post("/research", json={"topic": topic})
    assert response.status_code == 202
    job_id = uuid.UUID(response.json()["id"])
    created_ids.append(job_id)
    return job_id


def insert_job(created_ids, **fields):
    """Insert a job row directly, for tests that need a specific status."""
    db = SessionLocal()
    try:
        job = ResearchJob(topic=fields.pop("topic", "direct insert"), **fields)
        db.add(job)
        db.commit()
        db.refresh(job)
        created_ids.append(job.id)
        return job.id
    finally:
        db.close()


# ---------- GET /health ----------

def test_health_reports_ok(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "database": "ok"}


# ---------- POST /research ----------

def test_create_returns_202_with_queued_status(client, created_ids):
    response = client.post("/research", json={"topic": "impact of war"})
    assert response.status_code == 202

    body = response.json()
    assert body["status"] == "queued"
    created_ids.append(uuid.UUID(body["id"]))


def test_create_saves_job_with_provider_and_model(client, created_ids):
    job_id = create_job(client, created_ids)

    db = SessionLocal()
    try:
        job = db.get(ResearchJob, job_id)
        assert job.status == "queued"
        assert job.topic == "route test topic"
        assert job.llm_provider is not None
        assert job.llm_model is not None
    finally:
        db.close()


def test_create_rejects_blank_topic(client):
    response = client.post("/research", json={"topic": "   "})
    assert response.status_code == 422


def test_create_rejects_missing_topic(client):
    response = client.post("/research", json={})
    assert response.status_code == 422


# ---------- GET /research/{id} ----------

def test_get_queued_job_returns_progress_view(client, created_ids):
    job_id = create_job(client, created_ids)

    response = client.get(f"/research/{job_id}")
    assert response.status_code == 200

    body = response.json()
    assert body["status"] == "queued"
    assert "report" not in body
    assert "sources" not in body


def test_get_unknown_job_returns_404(client):
    response = client.get(f"/research/{uuid.uuid4()}")
    assert response.status_code == 404


def test_get_done_job_returns_full_result(client, created_ids):
    job_id = insert_job(
        created_ids,
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

    response = client.get(f"/research/{job_id}")
    assert response.status_code == 200

    body = response.json()
    assert body["report"] == "the report"
    assert body["sources"] == ["https://a.example"]
    assert body["review"]["score"] == 7


def test_get_failed_job_returns_error(client, created_ids):
    job_id = insert_job(
        created_ids,
        status="failed",
        error="something broke",
    )

    response = client.get(f"/research/{job_id}")
    assert response.status_code == 200
    assert response.json()["error"] == "something broke"


# ---------- GET /research ----------

def test_list_returns_only_finished_jobs(client, created_ids):
    queued_id = insert_job(created_ids, topic="list queued", status="queued")
    done_id = insert_job(created_ids, topic="list done", status="done")

    response = client.get("/research", params={"limit": 100})
    assert response.status_code == 200

    ids = [item["id"] for item in response.json()]
    assert str(done_id) in ids
    assert str(queued_id) not in ids


def test_list_rejects_limit_over_100(client):
    response = client.get("/research", params={"limit": 101})
    assert response.status_code == 422


# ---------- DELETE /research/{id} ----------

def test_delete_finished_job_returns_204_then_404(client, created_ids):
    job_id = insert_job(created_ids, topic="to delete", status="done")

    assert client.delete(f"/research/{job_id}").status_code == 204
    assert client.get(f"/research/{job_id}").status_code == 404


def test_delete_unknown_job_returns_404(client):
    response = client.delete(f"/research/{uuid.uuid4()}")
    assert response.status_code == 404


def test_delete_running_job_returns_409(client, created_ids):
    job_id = insert_job(created_ids, topic="busy", status="running")

    response = client.delete(f"/research/{job_id}")
    assert response.status_code == 409