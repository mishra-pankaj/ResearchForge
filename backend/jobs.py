# backend/jobs.py
import logging
import queue
import threading
import traceback
import uuid
from datetime import datetime, timezone

from backend.db import SessionLocal
from backend.models import ResearchJob
# from pipeline import run_research

logger = logging.getLogger("jobs")

# Jobs waiting to run. Holds job ids only, never the job data itself.
_job_queue: "queue.Queue[uuid.UUID]" = queue.Queue()

# Protects the shared state below, since the API and the worker
# run in different threads.
_state_lock = threading.Lock()
_current_job_id: uuid.UUID | None = None
_worker_started = False


def _set_fields(job_id: uuid.UUID, **fields) -> None:
    """Update one job row in its own short-lived session and commit at once."""
    db = SessionLocal()
    try:
        job = db.get(ResearchJob, job_id)
        if job is None:
            return
        for name, value in fields.items():
            setattr(job, name, value)
        db.commit()
    finally:
        db.close()


def _run_job(job_id: uuid.UUID) -> None:
    """Run one job from start to finish and record each state change."""
    global _current_job_id
    from pipeline import run_research

    db = SessionLocal()
    try:
        job = db.get(ResearchJob, job_id)
        if job is None:
            return
        topic = job.topic
    finally:
        db.close()

    with _state_lock:
        _current_job_id = job_id

    try:
        _set_fields(job_id, status="running")

        def on_step(step_name: str) -> None:
            _set_fields(job_id, current_step=step_name)

        output = run_research(topic, on_step=on_step)

        _set_fields(
            job_id,
            status="done",
            current_step=None,
            result=output,
            finished_at=datetime.now(timezone.utc),
        )
    except Exception as exc:
        logger.error("Job %s failed:\n%s", job_id, traceback.format_exc())
        _set_fields(
            job_id,
            status="failed",
            error=str(exc) or exc.__class__.__name__,
            finished_at=datetime.now(timezone.utc),
        )
    finally:
        with _state_lock:
            _current_job_id = None


def _worker_loop() -> None:
    """Runs forever in a background thread, taking one job at a time."""
    while True:
        job_id = _job_queue.get()
        try:
            _run_job(job_id)
        except Exception:
            # _run_job handles its own errors; this only guards the loop.
            logger.error("Worker crashed on job %s:\n%s", job_id, traceback.format_exc())
        finally:
            _job_queue.task_done()


def start_worker() -> None:
    """Start the single worker thread. Safe to call more than once."""
    global _worker_started
    with _state_lock:
        if _worker_started:
            return
        _worker_started = True
    thread = threading.Thread(target=_worker_loop, name="job-worker", daemon=True)
    thread.start()


def enqueue_job(job_id: uuid.UUID) -> None:
    """Add a saved job to the queue. Returns immediately."""
    _job_queue.put(job_id)


def get_running_job_id() -> uuid.UUID | None:
    """Return the id of the job currently running, or None."""
    with _state_lock:
        return _current_job_id


def mark_stale_jobs_failed() -> int:
    """On startup, fail jobs left as running or queued by a previous crash.

    Returns the number of jobs updated.
    """
    db = SessionLocal()
    try:
        stale = (
            db.query(ResearchJob)
            .filter(ResearchJob.status.in_(["running", "queued"]))
            .all()
        )
        for job in stale:
            job.status = "failed"
            job.error = "server restarted before the job finished"
            job.finished_at = datetime.now(timezone.utc)
        db.commit()
        return len(stale)
    finally:
        db.close()