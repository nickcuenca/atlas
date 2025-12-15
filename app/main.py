from fastapi import FastAPI
from uuid import uuid4

app = FastAPI() #created the fast API server

JOBS = {} # created empty JOB dict to hold the id, state, and payload of each index later

@app.post("/jobs") # Handle POST requests sent to /jobs

def create_job(job: dict): # create a new job from request payload
    job_id = str(uuid4()) #create an id for the job

    JOBS[job_id] = {  # job id index of job dict updates its id, state, and payload.
        "id" : job_id,
        "state" : "PENDING",
        "payload" : job
    }

    return { #returns the ID and the state of the job.
        "id" : job_id,
        "state" : "PENDING"
    }