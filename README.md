# Atlas

Atlas is a lightweight job execution API built with FastAPI, designed to explore backend and distributed systems concepts through incremental, hands-on development.

## Current Capabilities (v0)
- REST API for asynchronous job submission via JSON payloads
- UUID-based job identification
- In-memory job storage and state tracking
- Job retrieval by ID
- Basic job lifecycle state (`PENDING`)
- Input validation for supported job types

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

Returns the full job object including payload and current state.

## Architecture (v0)
- FastAPI application
- In-memory job store (Python dictionary)
- Stateless API layer
- No persistence or background workers yet

> Note: Jobs are stored in memory and will be lost on server restart.

## Roadmap
- Strict job payload validation
- Background worker loop
- Dynamic job state transitions (`RUNNING`, `SUCCESS`, `FAILED`)
- Retry and failure handling
- Persistent storage (PostgreSQL)
- Redis-backed job queue
- Horizontal worker scaling

## Goals
Atlas is a learning-focused project aimed at building real-world backend and distributed systems intuition, starting from first principles and evolving toward production-grade architecture.