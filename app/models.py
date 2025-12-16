from sqlalchemy import String, Integer, Float, DateTime, JSON, Text
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime, timezone
from .db import Base

def now_utc():
    return datetime.now(timezone.utc)

class Job(Base):
    __tablename__ = "jobs"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    type: Mapped[str] = mapped_column(String, nullable=False)

    state: Mapped[str] = mapped_column(String, nullable=False, index=True)  # PENDING/RUNNING/SUCCESS/FAILED/RETRYING
    payload: Mapped[dict] = mapped_column(JSON, nullable=False)
    result: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    attempt: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    max_retries: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    retry_delay_seconds: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)

    last_error: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=now_utc)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    duration_seconds: Mapped[float | None] = mapped_column(Float, nullable=True)