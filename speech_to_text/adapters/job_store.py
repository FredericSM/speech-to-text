"""In-memory job store. Sufficient for a single-process local app."""

from __future__ import annotations

import threading

from speech_to_text.domain.models import TranscriptionJob


class InMemoryJobStore:
    """Thread-safe job repository implementing JobStorePort.

    A lock guards the dict because jobs are mutated from worker threads
    while the event loop reads them for status polling.
    """

    def __init__(self) -> None:
        self._jobs: dict[str, TranscriptionJob] = {}
        self._lock = threading.Lock()

    def add(self, job: TranscriptionJob) -> None:
        with self._lock:
            self._jobs[job.id] = job

    def get(self, job_id: str) -> TranscriptionJob | None:
        with self._lock:
            return self._jobs.get(job_id)

    def update(self, job: TranscriptionJob) -> None:
        with self._lock:
            self._jobs[job.id] = job
