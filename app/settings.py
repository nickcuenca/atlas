import os

REDIS_HOST = os.getenv("REDIS_HOST", "redis")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
QUEUE_NAME = os.getenv("QUEUE_NAME", "job_queue")

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+psycopg2://atlas:atlas@postgres:5432/atlas",
)

# If a job is RUNNING longer than this, assume worker died and requeue it
RUNNING_TIMEOUT_SECONDS = int(os.getenv("RUNNING_TIMEOUT_SECONDS", "60"))