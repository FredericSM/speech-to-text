"""Unit tests for the pure domain + formatter logic."""

from __future__ import annotations

from speech_to_text.adapters.formatters import TxtFormatter
from speech_to_text.domain.models import Segment, TranscriptionResult


def _result() -> TranscriptionResult:
    return TranscriptionResult(
        language="en",
        duration=12.0,
        segments=[
            Segment(start=0.0, end=4.0, text="  Hello there. "),
            Segment(start=4.0, end=12.0, text="This is a test."),
        ],
    )


def test_full_text_joins_and_strips_segments() -> None:
    assert _result().full_text == "Hello there. This is a test."


def test_txt_formatter_wraps_and_terminates_with_newline() -> None:
    formatter = TxtFormatter(wrap_width=100)
    body = formatter.format(_result())
    assert body == "Hello there. This is a test.\n"
    assert formatter.extension == "txt"


def test_txt_formatter_wraps_long_text() -> None:
    long = TranscriptionResult(
        language="en",
        duration=1.0,
        segments=[Segment(start=0.0, end=1.0, text="word " * 60)],
    )
    body = TxtFormatter(wrap_width=40).format(long)
    assert all(len(line) <= 40 for line in body.splitlines())
