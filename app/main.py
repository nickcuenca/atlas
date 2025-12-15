from fastapi import FastAPI, HTTPException, BackgroundTasks
from datetime import datetime, timezone
from uuid import uuid4
from enum import Enum
import time

app = FastAPI()

JOBS = {}  # job_id -> job dict


class JobState(str, Enum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"


def now_utc():
    return datetime.now(timezone.utc)


def run_sleep_job(job_id: str) -> None:
    job = JOBS.get(job_id)
    if job is None:
        return
    if job["state"] != JobState.PENDING:
        return

    job["state"] = JobState.RUNNING
    job["started_at"] = now_utc()

    try:
        seconds = job["payload"]["seconds"]
        time.sleep(seconds)
        job["state"] = JobState.SUCCESS
        job["result"] = {"slept_seconds": seconds}

    except Exception as e:
        job["state"] = JobState.FAILED
        job["error"] = str(e)

    finally:
        job["finished_at"] = now_utc()
        if job["started_at"] is not None:
            job["duration_seconds"] = (job["finished_at"] - job["started_at"]).total_seconds()


def run_echo_job(job_id: str) -> None:
    job = JOBS.get(job_id)
    if job is None:
        return
    if job["state"] != JobState.PENDING:
        return

    job["state"] = JobState.RUNNING
    job["started_at"] = now_utc()

    try:
        # simplest echo: return the payload as-is
        job["result"] = job["payload"]
        job["state"] = JobState.SUCCESS

    except Exception as e:
        job["state"] = JobState.FAILED
        job["error"] = str(e)

    finally:
        job["finished_at"] = now_utc()
        if job["started_at"] is not None:
            job["duration_seconds"] = (job["finished_at"] - job["started_at"]).total_seconds()


JOB_HANDLERS = {
    "sleep": run_sleep_job,
    "echo": run_echo_job,
}


@app.post("/jobs")
def create_job(job: dict, background_tasks: BackgroundTasks):
    job_id = str(uuid4())

    job_type = job.get("type")
    if not job_type:
        raise HTTPException(status_code=400, detail="Job type is required")

    handler = JOB_HANDLERS.get(job_type)
    if handler is None:
        raise HTTPException(status_code=400, detail=f"Unsupported job type: {job_type}")

    # Job-specific validation
    if job_type == "sleep":
        seconds = job.get("seconds")
        if seconds is None:
            raise HTTPException(status_code=400, detail="seconds is required")
        if not isinstance(seconds, (int, float)):
            raise HTTPException(status_code=400, detail="seconds must be a number")
        if seconds <= 0:
            raise HTTPException(status_code=400, detail="seconds must be > 0")

    JOBS[job_id] = {
        "id": job_id,
        "type": job_type,
        "state": JobState.PENDING,
        "payload": job,
        "result": None,
        "error": None,
        "created_at": now_utc(),
        "started_at": None,
        "finished_at": None,
        "duration_seconds": None,
    }

    background_tasks.add_task(handler, job_id)

    return {"id": job_id, "state": JobState.PENDING}


@app.get("/jobs/{job_id}")
def get_job(job_id: str):
    job = JOBS.get(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")
    return job
