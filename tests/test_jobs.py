# tests/test_jobs.py
import sys
import threading
import types
import uuid

from backend import jobs
from backend.db import SessionLocal
from backend.models import ResearchJob


def use_fake_pipeline(monkeypatch, fake_run):
    """Replace pipeline.run_research with a fake, without loading LangChain.

    _run_job imports run_research at call time, so it picks up this fake.
    """
    module = types.ModuleType("pipeline")
    module.run_research = fake_run
    monkeypatch.setitem(sys.modules, "pipeline", module)


def insert_job(created_ids, **fields):
    db = SessionLocal()
    try:
        job = ResearchJob(topic=fields.pop("topic", "job test topic"), **fields)
        db.add(job)
        db.commit()
        db.refresh(job)
        created_ids.append(job.id)
        return job.id
    finally:
        db.close()


def read_job(job_id):
    db = SessionLocal()
    try:
        job = db.get(ResearchJob, job_id)
        return {
            "status": job.status,
            "current_step": job.current_step,
            "error": job.error,
            "result": job.result,
            "finished_at": job.finished_at,
        }
    finally:
        db.close()


# ---------- _run_job: success and failure ----------

def test_successful_run_saves_result(monkeypatch, created_ids):
    seen_steps = []

    def fake_run(topic, on_step):
        for step in ("search", "scrape", "write", "critique"):
            on_step(step)
            seen_steps.append(step)
        return {
            "search_results": "s",
            "scraped": [],
            "report": "the report",
            "review": {"score": 7, "text": "good"},
        }

    use_fake_pipeline(monkeypatch, fake_run)
    job_id = insert_job(created_ids, topic="success topic")

    jobs._run_job(job_id)

    data = read_job(job_id)
    assert seen_steps == ["search", "scrape", "write", "critique"]
    assert data["status"] == "done"
    assert data["current_step"] is None
    assert data["result"]["report"] == "the report"
    assert data["finished_at"] is not None


def test_failed_run_saves_error(monkeypatch, created_ids):
    def fake_run(topic, on_step):
        on_step("search")
        raise RuntimeError("model unreachable")

    use_fake_pipeline(monkeypatch, fake_run)
    job_id = insert_job(created_ids, topic="failing topic")

    jobs._run_job(job_id)

    data = read_job(job_id)
    assert data["status"] == "failed"
    assert data["error"] == "model unreachable"
    assert data["finished_at"] is not None


def test_error_without_message_uses_exception_name(monkeypatch, created_ids):
    def fake_run(topic, on_step):
        raise ValueError()  # str(exc) is empty here

    use_fake_pipeline(monkeypatch, fake_run)
    job_id = insert_job(created_ids, topic="silent failure")

    jobs._run_job(job_id)

    assert read_job(job_id)["error"] == "ValueError"


# ---------- _run_job: tracking the running job ----------

def test_current_job_is_tracked_during_run(monkeypatch, created_ids):
    observed = []

    def fake_run(topic, on_step):
        observed.append(jobs.get_running_job_id())
        return {"report": "r"}

    use_fake_pipeline(monkeypatch, fake_run)
    job_id = insert_job(created_ids, topic="tracked topic")

    jobs._run_job(job_id)

    assert observed == [job_id]
    assert jobs.get_running_job_id() is None


def test_current_job_is_cleared_after_failure(monkeypatch, created_ids):
    def fake_run(topic, on_step):
        raise RuntimeError("boom")

    use_fake_pipeline(monkeypatch, fake_run)
    job_id = insert_job(created_ids, topic="failing tracked topic")

    jobs._run_job(job_id)

    assert jobs.get_running_job_id() is None


def test_delete_refused_while_job_is_running(monkeypatch, client, created_ids):
    started = threading.Event()
    release = threading.Event()

    def fake_run(topic, on_step):
        started.set()
        release.wait(timeout=10)  # hold the job open until the test says so
        return {"report": "r"}

    use_fake_pipeline(monkeypatch, fake_run)
    job_id = insert_job(created_ids, topic="busy job")

    worker = threading.Thread(target=jobs._run_job, args=(job_id,))
    worker.start()
    try:
        assert started.wait(timeout=10), "job never started"
        response = client.delete(f"/research/{job_id}")
        assert response.status_code == 409
    finally:
        release.set()
        worker.join(timeout=10)

    assert read_job(job_id)["status"] == "done"


# ---------- _run_job: edge cases ----------

def test_run_job_ignores_missing_job(monkeypatch):
    called = []

    def fake_run(topic, on_step):
        called.append(topic)
        return {}

    use_fake_pipeline(monkeypatch, fake_run)

    jobs._run_job(uuid.uuid4())  # no row exists for this id

    assert called == []


# ---------- mark_stale_jobs_failed ----------

def test_stale_jobs_are_marked_failed(created_ids):
    running_id = insert_job(created_ids, topic="stale running", status="running")
    queued_id = insert_job(created_ids, topic="stale queued", status="queued")

    count = jobs.mark_stale_jobs_failed()

    assert count >= 2  # may include other stale rows in the real database
    for job_id in (running_id, queued_id):
        data = read_job(job_id)
        assert data["status"] == "failed"
        assert data["error"] == "server restarted before the job finished"