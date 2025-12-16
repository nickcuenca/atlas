import time
import random
from datetime import datetime, timezone
from sqlalchemy.orm import Session

from app.db import SessionLocal
from app.models import Job
from app.queue import dequeue_blocking, acquire_lock, release_lock, enqueue


def now_utc():
    return datetime.now(timezone.utc)


def compute_backoff_seconds(base_delay: float, attempt: int, cap_seconds: float = 30.0) -> float:
    """
    Exponential backoff with jitter.

    attempt is 1-based (1,2,3...):
      attempt=1 -> base_delay
      attempt=2 -> base_delay * 2
      attempt=3 -> base_delay * 4
    Jitter prevents thundering herd under load.
    """
    if base_delay <= 0:
        return 0.0

    # attempt=1 => multiplier 1, attempt=2 => 2, attempt=3 => 4, ...
    exp = base_delay * (2 ** (attempt - 1))
    backoff = min(exp, cap_seconds)

    # Full jitter in [0, backoff]
    return random.uniform(0.0, backoff)


# ----------------------------
# Job handlers
# ----------------------------
def run_sleep(job: Job) -> dict | None:
    seconds = job.payload["seconds"]
    time.sleep(seconds)
    return None


def run_echo(job: Job) -> dict:
    return {"message": job.payload["message"]}


JOB_HANDLERS = {
    "sleep": run_sleep,
    "echo": run_echo,
}


def mark_running(db: Session, job: Job) -> None:
    job.attempt += 1
    job.state = "RUNNING"
    job.started_at = now_utc()
    job.finished_at = None
    job.duration_seconds = None
    job.last_error = None
    db.commit()


def finalize(db: Session, job: Job, state: str, result: dict | None, error: str | None) -> None:
    job.state = state
    job.result = result
    job.last_error = error
    job.finished_at = now_utc()

    if job.started_at and job.finished_at:
        job.duration_seconds = (job.finished_at - job.started_at).total_seconds()

    db.commit()


def main():
    print("Worker started. Waiting for jobs...", flush=True)

    while True:
        _, job_id = dequeue_blocking()

        # Lock prevents duplicates if job got requeued twice
        if not acquire_lock(job_id, ttl_seconds=180):
            continue

        db = SessionLocal()
        try:
            job: Job | None = db.get(Job, job_id)
            if not job:
                continue

            if job.state not in ("PENDING", "RETRYING"):
                continue

            if job.type not in JOB_HANDLERS:
                finalize(db, job, "FAILED", None, f"Unsupported job type: {job.type}")
                continue

            mark_running(db, job)

            try:
                result = JOB_HANDLERS[job.type](job)
                finalize(db, job, "SUCCESS", result, None)

            except Exception as e:
                err = str(e)

                # If retries remain, mark RETRYING, backoff, and re-enqueue
                if job.attempt <= job.max_retries:
                    finalize(db, job, "RETRYING", None, err)

                    delay = compute_backoff_seconds(
                        base_delay=float(job.retry_delay_seconds),
                        attempt=int(job.attempt),
                        cap_seconds=30.0,
                    )

                    if delay > 0:
                        time.sleep(delay)

                    enqueue(job.id)

                else:
                    finalize(db, job, "FAILED", None, err)

        finally:
            db.close()
            release_lock(job_id)


if __name__ == "__main__":
    main()