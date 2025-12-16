import redis
from .settings import REDIS_HOST, REDIS_PORT, QUEUE_NAME

r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)

def enqueue(job_id: str) -> None:
    r.rpush(QUEUE_NAME, job_id)

def dequeue_blocking():
    return r.blpop(QUEUE_NAME)  # returns (queue_name, job_id)

def lock_key(job_id: str) -> str:
    return f"lock:job:{job_id}"

def acquire_lock(job_id: str, ttl_seconds: int = 120) -> bool:
    # set NX with TTL to prevent duplicate execution
    return bool(r.set(lock_key(job_id), "1", nx=True, ex=ttl_seconds))

def release_lock(job_id: str) -> None:
    r.delete(lock_key(job_id))