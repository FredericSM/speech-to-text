"""Output formatters. Add new formats by implementing TranscriptFormatter."""

from __future__ import annotations

import textwrap

from speech_to_text.domain.models import TranscriptionResult


class TxtFormatter:
    """Plain-text transcript, soft-wrapped into readable paragraphs."""

    extension = "txt"
    media_type = "text/plain; charset=utf-8"

    def __init__(self, wrap_width: int = 100) -> None:
        self._wrap_width = wrap_width

    def format(self, result: TranscriptionResult) -> str:
        wrapped = textwrap.fill(result.full_text, width=self._wrap_width)
        return wrapped + "\n"
