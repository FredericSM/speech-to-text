"""Transcriber adapter backed by faster-whisper (CTranslate2)."""

from __future__ import annotations

import logging
import threading
from pathlib import Path

from faster_whisper import WhisperModel

from speech_to_text.config import ComputeType, ModelSize
from speech_to_text.domain.models import Segment, TranscriptionResult
from speech_to_text.domain.ports import ProgressFn

logger = logging.getLogger(__name__)


class FasterWhisperTranscriber:
    """Implements TranscriberPort using locally loaded Whisper models.

    Models are loaded lazily and cached by size, so each one is loaded at
    most once and reused across jobs. The configured default is warm-loaded
    up front to keep the first request fast. Transcription is a blocking,
    CPU-bound call (CTranslate2 releases the GIL), so callers should run it
    off the event loop.
    """

    def __init__(self, default_model: ModelSize, device: str, compute_type: ComputeType) -> None:
        self._default_model = default_model
        self._device = device
        self._compute_type = compute_type
        self._models: dict[str, WhisperModel] = {}
        self._lock = threading.Lock()
        self._get_model(default_model)  # warm-load the default so the first job isn't slow

    def _get_model(self, model_size: str) -> WhisperModel:
        # Serialize loading so two concurrent jobs don't load the same model twice.
        with self._lock:
            model = self._models.get(model_size)
            if model is None:
                logger.info(
                    "Loading Whisper model '%s' on %s (%s)",
                    model_size,
                    self._device,
                    self._compute_type,
                )
                model = WhisperModel(
                    model_size, device=self._device, compute_type=self._compute_type
                )
                self._models[model_size] = model
            return model

    def transcribe(
        self,
        audio_path: Path,
        language: str | None,
        on_progress: ProgressFn,
        model: str | None = None,
    ) -> TranscriptionResult:
        whisper = self._get_model(model or self._default_model)
        # `segments` is a lazy generator: work happens as we iterate it.
        segments_iter, info = whisper.transcribe(
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
