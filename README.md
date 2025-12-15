# Atlas

Atlas is a lightweight job execution platform built with FastAPI, designed to explore distributed systems concepts through incremental development.

## Current Capabilities (v0)
- REST API for job submission via JSON payloads
- UUID-based job identification
- In-memory job storage and state tracking
- Job retrieval by ID
- Basic job lifecycle state (`PENDING`)

## API Endpoints
- `POST /jobs` — submit a new job
- `GET /jobs/{job_id}` — retrieve job details and state

## Architecture (v0)
- FastAPI application
- In-memory job store (Python dictionary)
- No persistence or background workers yet

## Roadmap
- Explicit job types (e.g. sleep, compute)
- Background worker loop
- Job state transitions (`RUNNING`, `SUCCESS`, `FAILED`)
- Retry and failure handling
- Persistent storage (PostgreSQL)
- Redis-backed job queue
- Horizontal worker scaling

## Goals
Atlas is a learning-focused project aimed at building real-world backend and distributed systems intuition, starting from first principles.
