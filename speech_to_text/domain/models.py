"""Core domain models. No framework or I/O dependencies live here."""

from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum
from uuid import uuid4

from pydantic import BaseModel, Field


class Segment(BaseModel):
    """A contiguous span of transcribed speech with its time boundaries."""

    start: float  # seconds from start of audio
    end: float
    text: str


class TranscriptionResult(BaseModel):
    """The full outcome of transcribing one audio file."""

    language: str
    duration: float  # total audio length in seconds
    segments: list[Segment]

    @property
    def full_text(self) -> str:
        """All segment texts joined into a single readable transcript."""
        return " ".join(segment.text.strip() for segment in self.segments).strip()


class JobStatus(StrEnum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class TranscriptionJob(BaseModel):
    """Tracks one transcription request through its lifecycle."""

    id: str = Field(default_factory=lambda: uuid4().hex)
    filename: str
    status: JobStatus = JobStatus.PENDING
    progress: float = 0.0  # 0.0 -> 1.0, based on processed audio duration
    result: TranscriptionResult | None = None
    error: str | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
