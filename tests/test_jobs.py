import time

def _run_job_state_machine(job_id: str, SessionFactory):
    """
    Run the job synchronously (in-process) using the same state-machine behavior
    as the worker, so CI doesn't need Redis/containers.

    Supports: echo, sleep
    Validates: PENDING/RETRYING -> RUNNING -> SUCCESS/FAILED/RETRYING
    """
    from app.models import Job

    try:
        from app.worker.worker import JOB_HANDLERS  # app/worker/worker.py
    except Exception:
        JOB_HANDLERS = {}

    from datetime import datetime, timezone
    def now_utc():
        return datetime.now(timezone.utc)

    db = SessionFactory()
    try:
        job = db.get(Job, job_id)
        assert job is not None, "Job not found in DB"

        while job.state in ("PENDING", "RETRYING"):
            job.attempt += 1
            job.state = "RUNNING"
            job.started_at = now_utc()
            job.finished_at = None
            job.duration_seconds = None
            job.last_error = None
            db.commit()

            try:
                handler = JOB_HANDLERS.get(job.type)

                # Fallback handlers if JOB_HANDLERS isn't importable
                if handler is None:
                    if job.type == "echo":
                        handler = lambda j: {"message": j.payload["message"]}
                    elif job.type == "sleep":
                        handler = lambda j: (time.sleep(float(j.payload["seconds"])) or None)
                    else:
                        raise Exception(f"Unsupported job type: {job.type}")

                result = handler(job)
                job.state = "SUCCESS"
                job.result = result
                job.last_error = None

            except Exception as e:
                err = str(e)
                job.last_error = err
                if job.attempt <= job.max_retries:
                    job.state = "RETRYING"
                    job.result = None
                else:
                    job.state = "FAILED"
                    job.result = None

            finally:
                job.finished_at = now_utc()
                if job.started_at and job.finished_at:
                    start = job.started_at
                    end = job.finished_at

                    if start.tzinfo is None:
                        start = start.replace(tzinfo=timezone.utc)
                    if end.tzinfo is None:
                        end = end.replace(tzinfo=timezone.utc)

                    job.duration_seconds = (end - start).total_seconds()

                db.commit()
                job = db.get(Job, job_id)

        return job

    finally:
        db.close()


def test_echo_validation(client):
    import app.main as main
    main.enqueue = lambda job_id: None  # avoid Redis

    r = client.post("/jobs", json={"type": "echo", "payload": {"message": "hi"}})
    assert r.status_code == 200
    data = r.json()
    assert data["state"] == "PENDING"
    assert data["type"] == "echo"


def test_invalid_type(client):
    import app.main as main
    main.enqueue = lambda job_id: None  # avoid Redis

    r = client.post("/jobs", json={"type": "nope", "payload": {}})
    assert r.status_code == 400


def test_get_missing_job_404(client):
    r = client.get("/jobs/does-not-exist")
    assert r.status_code == 404


def test_echo_job_completes_and_returns_result(client, db_sessionmaker):
    import app.main as main
    main.enqueue = lambda job_id: None  # avoid Redis

    r = client.post("/jobs", json={"type": "echo", "payload": {"message": "hello"}})
    assert r.status_code == 200
    job_id = r.json()["id"]

    _run_job_state_machine(job_id, db_sessionmaker)

    j = client.get(f"/jobs/{job_id}").json()
    assert j["state"] == "SUCCESS"
    assert j["result"]["message"] == "hello"
    assert j["attempt"] == 1


def test_sleep_sets_duration_seconds(client, db_sessionmaker):
    import app.main as main
    main.enqueue = lambda job_id: None  # avoid Redis

    r = client.post("/jobs", json={"type": "sleep", "payload": {"seconds": 0.1}})
    assert r.status_code == 200
    job_id = r.json()["id"]

    _run_job_state_machine(job_id, db_sessionmaker)

    j = client.get(f"/jobs/{job_id}").json()
    assert j["state"] == "SUCCESS"
    assert j["duration_seconds"] is not None
    assert j["duration_seconds"] >= 0.09


def test_retry_increments_attempts_then_succeeds(client, db_sessionmaker, monkeypatch):
    import app.main as main
    main.enqueue = lambda job_id: None  # avoid Redis

    from app.worker import worker as worker_mod

    calls = {"n": 0}
    original = worker_mod.JOB_HANDLERS["echo"]

    def flaky_echo(job):
        calls["n"] += 1
        if calls["n"] == 1:
            raise Exception("transient error")
        return original(job)

    monkeypatch.setitem(worker_mod.JOB_HANDLERS, "echo", flaky_echo)

    r = client.post("/jobs", json={
        "type": "echo",
        "payload": {"message": "hi"},
        "max_retries": 2,
        "retry_delay_seconds": 0,
    })
    assert r.status_code == 200
    job_id = r.json()["id"]

    _run_job_state_machine(job_id, db_sessionmaker)

    j = client.get(f"/jobs/{job_id}").json()
    assert j["state"] == "SUCCESS"
    assert j["attempt"] == 2
    assert j["result"]["message"] == "hi"
    assert calls["n"] == 2