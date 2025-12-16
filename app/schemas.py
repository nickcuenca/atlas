from pydantic import BaseModel, ConfigDict, Field
from typing import Optional, Literal, Any

JobState = Literal["PENDING", "RUNNING", "SUCCESS", "FAILED", "RETRYING"]

class JobCreate(BaseModel):
    type: str
    payload: dict = Field(default_factory=dict)
    max_retries: int = 0
    retry_delay_seconds: float = 0.0

class JobOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    type: str
    state: JobState

    payload: dict
    result: Optional[dict] = None

    attempt: int
    max_retries: int
    retry_delay_seconds: float

    last_error: Optional[str] = None

    created_at: Any
    started_at: Any = None
    finished_at: Any = None
    duration_seconds: Optional[float] = None