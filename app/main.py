from fastapi import FastAPI, HTTPException, BackgroundTasks
from datetime import datetime, timezone
from uuid import uuid4
import time  # Don't forget to import time for sleep

app = FastAPI()  # created the fast API server

JOBS = {}  # job_id -> {id, state, payload, ...}

def now_utc():
    return datetime.now(timezone.utc)

def run_sleep_job(job_id: str) -> None:
    """
    Worker logic for a sleep job.
    Runs in the background after the request returns.
    """
    job = JOBS.get(job_id)
    if job is None:
        return
    
    if job["state"] != "PENDING":
        return  # job was deleted or never existed
    
    # Move to RUNNING
    job["state"] = "RUNNING"
    job["started_at"] = now_utc()


    try:
        seconds = job["payload"]["seconds"]
        time.sleep(seconds)
        job["state"] = "SUCCESS"

    except Exception as e:
        job["state"] = "FAILED"
        job["error"] = str(e)
    finally:
        job["finished_at"] = now_utc()
        job["duration_seconds"] = (
            job["finished_at"] - job["started_at"]
        ).total_seconds()

JOB_HANDLERS = {
    "sleep": run_sleep_job,
}

@app.post("/jobs")  # Handle POST requests sent to /jobs
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
        "state": "PENDING",
        "payload": job,
        "created_at": now_utc(),
        "started_at": None,
        "finished_at": None,
    }

    background_tasks.add_task(handler, job_id)

    return {
        "id": job_id,
        "state": "PENDING",
    }

@app.get("/jobs/{job_id}")
def get_job(job_id: str):  # gets a job that currently exists
    job = JOBS.get(job_id)  # dynamically create the job we need
    if job is None:  # if no job
        raise HTTPException(status_code=404, detail="Job not found")  # display code 404 not found
    return job  # return the job
