# Atlas

Atlas is a lightweight job execution API built with FastAPI, designed to explore backend and distributed systems concepts through incremental, hands-on development.

## Current Capabilities (v0.2)
- REST API for asynchronous job submission via JSON payloads
- UUID-based job identification
- In-memory job storage and state tracking
- Job retrieval by ID
- Input validation for supported job types
- Background execution using FastAPI `BackgroundTasks`
- Job lifecycle state transitions: `PENDING` → `RUNNING` → `SUCCESS` / `FAILED`

## Supported Job Types
- `sleep` — placeholder job type used to model long-running work

## API Endpoints

### Create Job
`POST /jobs`

Example request:
```json
{
  "type": "sleep",
  "seconds": 3
}
```

Example response:
```json
{
  "id": "<job_id>",
  "state": "PENDING"
}
```

### Get Job
`GET /jobs/{job_id}`

Example response (shape):
```json
{
  "id": "<job_id>",
  "state": "RUNNING",
  "payload": {
    "type": "sleep",
    "seconds": 3
  }
}
```

If an error occurs during execution, the job will return:
```json
{
  "id": "<job_id>",
  "state": "FAILED",
  "payload": { "...": "..." },
  "error": "<error_message>"
}
```

## How It Works (v0.2)
1. `POST /jobs` validates the incoming JSON payload.
2. A job record is stored in-memory in the `JOBS` dictionary.
3. The API schedules `run_sleep_job(job_id)` using `BackgroundTasks` so the request can return immediately.
4. The background task updates state to `RUNNING`, sleeps for `seconds`, then marks the job `SUCCESS` (or `FAILED` with an error).

> Note: This version is intentionally simple and learning-focused. It is not yet a true distributed system.

## Architecture (v0.2)
- FastAPI application
- In-memory job store (Python dictionary)
- Background execution via FastAPI `BackgroundTasks` (runs in the same process)
- No persistence (jobs are lost on server restart)
- No external queue or separate worker process yet

## Local Development

### Run the server
From the project root:
```bash
uvicorn app.main:app --reload
```

Then open:
- Swagger UI: `http://127.0.0.1:8000/docs`

### Quick Test (Swagger)
1. Go to `/docs`
2. Use `POST /jobs` with:
   ```json
   {"type":"sleep","seconds":3}
   ```
3. Copy the returned job id
4. Use `GET /jobs/{job_id}` to watch the state transition

## Roadmap
- Pydantic models for strict request/response schemas
- Job type dispatch system (cleanly add more job handlers)
- Persistent storage (PostgreSQL) so jobs survive restarts
- Redis-backed queue + separate worker process (true distributed execution)
- Retries, timeouts, idempotency, and cancellation
- Metrics + structured logging + tests + load testing

## Goals
Atlas is a learning-focused project aimed at building real-world backend and distributed systems intuition, starting from first principles and evolving toward production-grade architecture.