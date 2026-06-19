"""Application configuration, sourced from environment variables."""

from __future__ import annotations

from pathlib import Path
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict

ModelSize = Literal["tiny", "base", "small", "medium", "large-v3"]
ComputeType = Literal["int8", "int8_float16", "float16", "float32"]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="STT_", env_file=".env")

    # Whisper model to load. Larger = more accurate but slower.
    whisper_model: ModelSize = "small"
    # CPU-friendly default; faster-whisper has no Metal backend on macOS.
    device: Literal["cpu", "cuda", "auto"] = "cpu"
    compute_type: ComputeType = "int8"

    # Local server bind. 8000 is often already in use, so default higher.
    host: str = "127.0.0.1"
    port: int = 8011

    # Where uploaded audio is buffered while a job runs.
    upload_dir: Path = Path(".uploads")

    # Reject uploads larger than this (MB). ~2h MP3 at 128kbps ≈ 115 MB.
    max_upload_mb: int = 500


settings = Settings()
