# backend/main.py
import os
import uuid
from contextlib import asynccontextmanager
from backend.auth import get_current_user
from backend.models import ResearchJob, User
from dotenv import load_dotenv
from fastapi import Depends, FastAPI, HTTPException, Query, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.orm import Session

from backend import jobs
from backend.auth import router as auth_router
from backend.db import engine, get_db
from backend.models import ResearchJob
from backend.schemas import (
    ResearchCreate,
    ResearchCreated,
    ResearchListItem,
    ResearchResult,
    ResearchStatus,
    Review,
    ScrapedSource,
)

load_dotenv()

# A job counts as finished when it has stopped running, either successfully or not.
FINISHED_STATUSES = ("done", "failed")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Runs once when the server starts, before it accepts requests.
    failed_count = jobs.mark_stale_jobs_failed()
    if failed_count:
        print(f"Marked {failed_count} leftover job(s) from a previous run as failed.")
    jobs.start_worker()
    yield
    # Nothing to clean up on shutdown: the worker is a daemon thread.


app = FastAPI(title="Multi-Agent Research API", lifespan=lifespan)

# Lets the React dev server (Vite, port 5173) call this API from the browser.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
def current_llm_info() -> tuple[str, str]:
    """Return the provider and model name that will be used for new jobs."""
    provider = os.getenv("LLM_PROVIDER", "ollama")
    if provider == "ollama":
        model = os.getenv("OLLAMA_MODEL", "qwen2.5:7b")
    else:
        model = os.getenv("LLM_MODEL", "unknown")
    return provider, model


def build_result(job: ResearchJob) -> ResearchResult:
    """Turn a finished job row into the full result response.

    The report, sources, and review live inside the JSON `result` column,
    so we unpack them here into named fields.
    """
    data = job.result or {}

    scraped = [
        ScrapedSource(
            url=item.get("url", ""),
            ok=item.get("ok", False),
            text=item.get("text", ""),
        )
        for item in data.get("scraped", [])
    ]
    # Sources are the pages that were actually read successfully.
    sources = [item.url for item in scraped if item.ok]

    review = data.get("review") or {}

    return ResearchResult(
        id=job.id,
        topic=job.topic,
        status=job.status,
        llm_provider=job.llm_provider,
        llm_model=job.llm_model,
        created_at=job.created_at,
        finished_at=job.finished_at,
        sources=sources,
        scraped=scraped,
        report=data.get("report", ""),
        review=Review(score=review.get("score"), text=review.get("text", "")),
    )


@app.get("/health")
def health():
    """Checks that the API is running and can reach PostgreSQL."""
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return {"status": "ok", "database": "ok"}
    except Exception:
        return JSONResponse(
            status_code=503,
            content={"status": "error", "database": "unreachable"},
        )


@app.post("/research", response_model=ResearchCreated, status_code=202)
def create_research(
    body: ResearchCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)):

    """Save a new job as queued and hand it to the background worker."""
    provider, model = current_llm_info()

    job = ResearchJob(
        topic=body.topic,
        status="queued",
        llm_provider=provider,
        llm_model=model,
        user_id=current_user.id
    )
    db.add(job)
    db.commit()       # save first, so the worker can find the row
    db.refresh(job)

    jobs.enqueue_job(job.id)  # returns immediately

    return ResearchCreated(id=job.id, status=job.status)


@app.get("/research/{job_id}")
def get_research(
    job_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Return progress while the job runs, or the full result once it is done."""
    job = db.get(ResearchJob, job_id)
    if job is None or job.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Research job not found")

    if job.status == "done":
        return build_result(job)

    # queued, running, or failed: return the light progress view.
    return ResearchStatus.model_validate(job)


@app.get("/research", response_model=list[ResearchListItem])
def list_research(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List finished jobs, newest first, with paging."""
    rows = (
        db.query(ResearchJob)
        .filter(ResearchJob.user_id == current_user.id)
        .filter(ResearchJob.status.in_(FINISHED_STATUSES))
        .order_by(ResearchJob.created_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )
    return rows


@app.delete("/research/{job_id}", status_code=204)
def delete_research(
    job_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)):
    """Delete one of this user's jobs. Refused while that job is running."""
    job = db.get(ResearchJob, job_id)
    if job is None or job.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Research job not found")

    if jobs.get_running_job_id() == job_id or job.status == "running":
        raise HTTPException(
            status_code=409,
            detail="This job is running right now and cannot be deleted yet",
        )

    db.delete(job)
    db.commit()
    return Response(status_code=204)