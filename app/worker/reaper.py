import time
from datetime import datetime, timezone, timedelta
from sqlalchemy import select

from app.db import SessionLocal
from app.models import Job
from app.queue import enqueue
from app.settings import RUNNING_TIMEOUT_SECONDS

def now_utc():
    return datetime.now(timezone.utc)

def main():
    print("Reaper started. Scanning for stuck RUNNING jobs...")
    while True:
        cutoff = now_utc() - timedelta(seconds=RUNNING_TIMEOUT_SECONDS)

        db = SessionLocal()
        try:
            stmt = select(Job).where(Job.state == "RUNNING").where(Job.started_at != None).where(Job.started_at < cutoff)
            stuck = db.execute(stmt).scalars().all()

            for job in stuck:
                # Requeue only if retries remain, else fail it.
                if job.attempt <= job.max_retries:
                    job.state = "RETRYING"
                    job.last_error = "Worker timeout detected; requeued"
                    db.commit()
                    enqueue(job.id)
                else:
                    job.state = "FAILED"
                    job.last_error = "Worker timeout detected; no retries left"
                    job.finished_at = now_utc()
                    db.commit()
        finally:
            db.close()

        time.sleep(5)

if __name__ == "__main__":
    main()