"""Use-case orchestration. Depends only on domain ports, not on adapters."""

from __future__ import annotations

import logging
from pathlib import Path

from speech_to_text.domain.models import JobStatus, TranscriptionJob
from speech_to_text.domain.ports import JobStorePort, TranscriberPort

logger = logging.getLogger(__name__)


class TranscriptionService:
    def __init__(self, transcriber: TranscriberPort, jobs: JobStorePort) -> None:
        self._transcriber = transcriber
        self._jobs = jobs

    def create_job(self, filename: str) -> TranscriptionJob:
        job = TranscriptionJob(filename=filename)
        self._jobs.add(job)
        return job

    def get_job(self, job_id: str) -> TranscriptionJob | None:
        return self._jobs.get(job_id)

    def run(self, job_id: str, audio_path: Path, language: str | None) -> None:
        """Execute a transcription to completion. Blocking; run off-loop.

        Updates the stored job's status/progress as it goes and always
        cleans up the buffered audio file.
        """
        job = self._jobs.get(job_id)
        if job is None:
            logger.error("run() called for unknown job %s", job_id)
            return

        job.status = JobStatus.PROCESSING
        self._jobs.update(job)

        def report(fraction: float) -> None:
            job.progress = fraction
            self._jobs.update(job)

        try:
            result = self._transcriber.transcribe(audio_path, language, report)
            job.result = result
            job.status = JobStatus.COMPLETED
            job.progress = 1.0
        except Exception as exc:  # adapter boundary: surface failure to the client
            logger.exception("Transcription failed for job %s", job_id)
            job.status = JobStatus.FAILED
            job.error = str(exc)
        finally:
            self._jobs.update(job)
            audio_path.unlink(missing_ok=True)
