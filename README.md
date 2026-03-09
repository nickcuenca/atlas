# Atlas

Atlas is a **distributed, asynchronous job execution platform** built with FastAPI, Redis, and PostgreSQL.
It models real-world backend and distributed systems patterns including stateless APIs, durable state,
worker-based execution, retries, and crash recovery.

Atlas intentionally evolves from a simple prototype into a production-style architecture, prioritizing
clarity, correctness, and debuggability over shortcuts.

---

## ✨ Key Features

- **Stateless FastAPI API** for asynchronous job submission
- **Redis-backed job queue** for decoupled dispatch
- **Dedicated worker process** for background execution
- **PostgreSQL-backed durable job state**
- **Explicit job lifecycle state machine**:
  ```
  PENDING → RUNNING → SUCCESS | FAILED | RETRYING
  ```
- **Bounded retries with exponential backoff and jitter**
- **Crash-safe execution** via durable state and locking
- **Execution metadata**:
  - attempt count
  - timestamps (created, started, finished)
  - execution duration
- **Fully Dockerized local development environment**

---

## 🧱 Architecture Overview

```
Client
  │
  ▼
FastAPI API (stateless)
  │
  ├── PostgreSQL (job state, metadata, results)
  │
  └── Redis Queue (job IDs)
           │
           ▼
     Worker Process
       ├── Pulls job IDs from Redis
       ├── Executes handler
       ├── Applies retry + backoff on failure
       └── Updates job state in PostgreSQL
```

### Components
- **API**: validates requests, creates jobs, enqueues work
- **Redis**: FIFO queue and lightweight locking
- **PostgreSQL**: source of truth for job lifecycle and results
- **Worker**: executes jobs independently of the API

---

## 🔌 Supported Job Types

### `echo`
Immediately returns a message (useful for testing and demos).

```json
{
  "type": "echo",
  "payload": {
    "message": "hello world"
  }
}
```

---

### `sleep`
Simulates long-running work.

```json
{
  "type": "sleep",
  "payload": {
    "seconds": 3
  }
}
```

---

## 🚀 API Endpoints

### Create Job
**POST** `/jobs`

```json
{
  "type": "echo",
  "payload": { "message": "hello" },
  "max_retries": 2,
  "retry_delay_seconds": 1
}
```

**Response**
```json
{
  "id": "<job_id>",
  "state": "PENDING"
}
```

---

### Get Job Status
**GET** `/jobs/{job_id}`

Returns the full job record, including:
- state
- attempt count
- timestamps
- execution duration
- result (if completed)
- last error (if failed)

---

### Health Check
**GET** `/health`

```json
{
  "status": "ok"
}
```

---

## 🔁 Retry & Backoff Strategy

Atlas implements **bounded retries with exponential backoff and jitter** to safely handle transient failures
without overwhelming workers or infrastructure.

### Behavior
- Each job defines:
  - `max_retries`
  - `retry_delay_seconds` (base delay)
- On failure:
  - The job transitions to `RETRYING`
  - Delay grows exponentially per attempt:
    ```
    delay = min(base_delay * 2^(attempt-1), 30s)
    ```
  - Random jitter is applied to prevent synchronized retries
- Retries stop once `max_retries` is exceeded and the job is marked `FAILED`

### Why this matters
- Prevents retry storms under load
- Avoids thundering herd effects
- Mirrors industry-standard retry patterns in distributed systems

---

## 📊 Performance

Load tested with [Artillery](https://www.artillery.io/) across three phases: warm-up (10 req/s), sustained load (50 req/s), and peak load (100 req/s).

| Metric | Result |
|---|---|
| Total requests | 25,200 |
| Error rate | **0%** |
| p95 API latency | **6ms** |
| p99 API latency | **15ms** |
| Peak throughput | **200 req/sec** |
| Failed virtual users | **0** |

All requests returned HTTP 200. No dropped connections or worker failures under peak load.

---

## 🐳 Local Development (Docker)

### Prerequisites
- Docker
- Docker Compose

### Start the system
```bash
docker compose up --build
```

This starts:
- FastAPI API (`localhost:8000`)
- Redis
- PostgreSQL
- Worker process

### Run the load test
```bash
artillery run load-test/load-test.yml
```

### Test manually
```bash
# Submit a job
curl -X POST http://localhost:8000/jobs \
  -H "Content-Type: application/json" \
  -d '{"type": "echo", "payload": {"message": "hello atlas"}}'

# Check job status
curl http://localhost:8000/jobs/<job_id>
```

---

## 🧪 Reliability Guarantees

- At-least-once execution semantics
- Duplicate execution prevented via Redis locks
- Job state persisted independently of worker lifecycle
- Retry attempts tracked and bounded
- Execution timing measured per job

---

## 🎯 Design Philosophy

- Build distributed systems incrementally
- Favor explicit state machines over implicit behavior
- Treat infrastructure as part of the application
- Prefer debuggability and observability over cleverness

---

## 🛣️ Future Improvements

- Job prioritization
- Scheduled / delayed jobs
- Dead-letter queues
- Metrics & Prometheus instrumentation
- Authentication & rate limiting
- Web UI for job inspection
- Horizontal worker autoscaling

---

Atlas is intentionally designed to resemble how real systems are built, debugged, and evolved —
not how tutorials oversimplify them.
