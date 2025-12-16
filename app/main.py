from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from uuid import uuid4
from datetime import datetime, timezone

from .db import Base, engine, get_db
from .models import Job
from .schemas import JobCreate, JobOut
from .queue import enqueue

app = FastAPI(title="Atlas")

# Create tables (fine for MVP demo; you can swap to Alembic later)
Base.metadata.create_all(bind=engine)

@app.get("/health")
def health():
    return {"status": "ok"}

def now_utc():
    return datetime.now(timezone.utc)

def validate_job(job: JobCreate) -> None:
    if job.max_retries < 0:
        raise HTTPException(400, "max_retries must be >= 0")
    if job.retry_delay_seconds < 0:
        raise HTTPException(400, "retry_delay_seconds must be >= 0")

    t = job.type
    p = job.payload

    if t == "sleep":
        seconds = p.get("seconds")
        if seconds is None or not isinstance(seconds, (int, float)) or seconds <= 0:
            raise HTTPException(400, "sleep requires payload.seconds > 0")
    elif t == "echo":
        message = p.get("message")
        if message is None or not isinstance(message, str) or not message.strip():
            raise HTTPException(400, "echo requires payload.message (non-empty string)")
    else:
        raise HTTPException(400, f"Unsupported job type: {t}")

@app.post("/jobs", response_model=JobOut)
def create_job(body: JobCreate, db: Session = Depends(get_db)):
    validate_job(body)

    job_id = str(uuid4())
    record = Job(
        id=job_id,
        type=body.type,
        state="PENDING",
        payload=body.payload,
        result=None,
        attempt=0,
        max_retries=body.max_retries,
        retry_delay_seconds=float(body.retry_delay_seconds),
        last_error=None,
        created_at=now_utc(),
        started_at=None,
        finished_at=None,
        duration_seconds=None,
    )
    db.add(record)
    db.commit()

    enqueue(job_id)

    db.refresh(record)  # after commit
    return JobOut.model_validate(record)

@app.get("/jobs/{job_id}", response_model=JobOut)
def get_job(job_id: str, db: Session = Depends(get_db)):
    job = db.get(Job, job_id)
    if not job:
        raise HTTPException(404, "Job not found")
    return JobOut.model_validate(job)
