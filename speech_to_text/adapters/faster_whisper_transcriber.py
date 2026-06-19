"""Transcriber adapter backed by faster-whisper (CTranslate2)."""

from __future__ import annotations

import logging
from pathlib import Path

from faster_whisper import WhisperModel

from speech_to_text.config import ComputeType, ModelSize
from speech_to_text.domain.models import Segment, TranscriptionResult
from speech_to_text.domain.ports import ProgressFn

logger = logging.getLogger(__name__)


class FasterWhisperTranscriber:
    """Implements TranscriberPort using a locally loaded Whisper model.

    The model is loaded once and reused across jobs. Transcription is a
    blocking, CPU-bound call (CTranslate2 releases the GIL), so callers
    should run it off the event loop.
    """

    def __init__(self, model_size: ModelSize, device: str, compute_type: ComputeType) -> None:
        logger.info("Loading Whisper model '%s' on %s (%s)", model_size, device, compute_type)
        self._model = WhisperModel(model_size, device=device, compute_type=compute_type)

    def transcribe(
        self,
        audio_path: Path,
        language: str | None,
        on_progress: ProgressFn,
    ) -> TranscriptionResult:
        # `segments` is a lazy generator: work happens as we iterate it.
        segments_iter, info = self._model.transcribe(
            str(audio_path),
            language=language,
            vad_filter=True,  # skip silence — big win on long recordings
        )

        total_duration = max(info.duration, 1e-6)
        collected: list[Segment] = []
        for raw in segments_iter:
            collected.append(Segment(start=raw.start, end=raw.end, text=raw.text))
            on_progress(min(raw.end / total_duration, 1.0))

        on_progress(1.0)
        return TranscriptionResult(
            language=info.language,
            duration=info.duration,
            segments=collected,
        )
