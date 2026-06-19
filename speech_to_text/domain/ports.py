"""Ports: the interfaces the domain depends on. Adapters implement these."""

from __future__ import annotations

from pathlib import Path
from typing import Protocol

from speech_to_text.domain.models import TranscriptionJob, TranscriptionResult


class ProgressFn(Protocol):
    """Called by a transcriber after each chunk with a 0.0..1.0 fraction."""

    def __call__(self, fraction: float) -> None: ...


class TranscriberPort(Protocol):
    """Turns an audio file into a structured transcription."""

    def transcribe(
        self,
        audio_path: Path,
        language: str | None,
        on_progress: ProgressFn,
    ) -> TranscriptionResult: ...


class TranscriptFormatter(Protocol):
    """Renders a transcription result into a downloadable file body."""

    extension: str
    media_type: str

    def format(self, result: TranscriptionResult) -> str: ...


class JobStorePort(Protocol):
    """Stores and retrieves transcription jobs."""

    def add(self, job: TranscriptionJob) -> None: ...

    def get(self, job_id: str) -> TranscriptionJob | None: ...

    def update(self, job: TranscriptionJob) -> None: ...
