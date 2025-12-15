from fastapi import FastAPI, HTTPException
from uuid import uuid4

app = FastAPI() #created the fast API server

JOBS = {} # created empty JOB dict to hold the id, state, and payload of each index later

@app.post("/jobs") # Handle POST requests sent to /jobs

def create_job(job: dict): # create a new job from request payload
    job_id = str(uuid4()) #create an id for the job

    if "type" not in job:
        raise HTTPException(status_code=400, detail="Job type is required")

    if job["type"] != "sleep":
        raise HTTPException(status_code=400, detail="Unsupported job type")
    
    if "seconds" not in job:
        raise HTTPException(status_code=400, detail="seconds is required")

    if not isinstance(job["seconds"], (int, float)):
        raise HTTPException(status_code=400, detail="seconds must be a number")

    if job["seconds"] <= 0:
        raise HTTPException(status_code=400, detail="seconds must be > 0")



    JOBS[job_id] = {  # job id index of job dict updates its id, state, and payload.
        "id" : job_id,
        "state" : "PENDING",
        "payload" : job
    }

    return { #returns the ID and the state of the job.
        "id" : job_id,
        "state" : "PENDING"
    }

@app.get("/jobs/{job_id}")
def get_job(job_id: str): # gets a job that currently exsits
    job = JOBS.get(job_id) # dynamically create the job we need
    if job is None: #if no job
        raise HTTPException(status_code=404, detail="Job not found") #display code 404 not found
    return job #return the job
    