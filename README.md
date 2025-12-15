# Atlas

Atlas is a lightweight job execution API built with FastAPI, designed to explore backend and distributed systems concepts through incremental, hands-on development.

## Current Capabilities (v0.3)
- REST API for asynchronous job submission via JSON payloads
- UUID-based job identification
- In-memory job storage and state tracking
- Background job execution using FastAPI BackgroundTasks
- Job lifecycle states: PENDING → RUNNING → SUCCESS / FAILED
- Job timing metadata (created_at, started_at, finished_at, duration)
- Handler-based job dispatch architecture

## Supported Job Types
### sleep
Simulates long-running work.

Example payload:
```json
{
  "type": "sleep",
  "seconds": 3
}
```

### echo
Echoes a provided message immediately (useful for testing and extensibility).

Example payload:
```json
{
  "type": "echo",
  "message": "hello world"
}
```

## API Endpoints

### Create Job
POST /jobs

Returns:
```json
{
  "id": "<job_id>",
  "state": "PENDING"
}
```

### Get Job
GET /jobs/{job_id}

Returns the full job object, including:
- id
- type
- state
- payload
- timestamps
- duration (when complete)

## Architecture (Current)
- FastAPI application
- Stateless API layer
- In-memory job store (Python dict)
- Background task execution
- Job handler registry (JOB_HANDLERS)

> Note: Jobs are stored in memory and will be lost on server restart.

## Design Goals
- Learn backend systems from first principles
- Model real-world job orchestration patterns
- Maintain clarity and correctness over premature complexity

## Roadmap
- Retry logic and failure policies
- Persistent storage (PostgreSQL)
- Redis-backed job queues
- Dedicated worker processes
- Horizontal scaling
- Authentication and rate limiting

---
Atlas is intentionally built step-by-step to reflect how real systems evolve, not how tutorials shortcut.