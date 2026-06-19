"""FastAPI adapter: HTTP endpoints wired to the transcription service."""

from __future__ import annotations

import asyncio
import logging
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Annotated, get_args
from urllib.parse import quote

from fastapi import FastAPI, Form, HTTPException, UploadFile
from fastapi.responses import HTMLResponse, PlainTextResponse, Response
from pydantic import BaseModel

from speech_to_text.adapters.faster_whisper_transcriber import FasterWhisperTranscriber
from speech_to_text.adapters.formatters import TxtFormatter
from speech_to_text.adapters.job_store import InMemoryJobStore
from speech_to_text.application.transcription_service import TranscriptionService
from speech_to_text.config import ModelSize, settings
from speech_to_text.domain.models import JobStatus

_ALLOWED_MODELS: frozenset[str] = frozenset(get_args(ModelSize))

logger = logging.getLogger(__name__)

_STATIC_DIR = Path(__file__).parent / "static"

# Composed at startup; the heavy model load happens in the lifespan handler.
service: TranscriptionService
formatter = TxtFormatter()


@asynccontextmanager
async def lifespan(app: FastAPI):
    global service
    settings.upload_dir.mkdir(parents=True, exist_ok=True)
    transcriber = FasterWhisperTranscriber(
        default_model=settings.whisper_model,
        device=settings.device,
        compute_type=settings.compute_type,
    )
    service = TranscriptionService(transcriber=transcriber, jobs=InMemoryJobStore())
    logger.info("Service ready")
    yield


app = FastAPI(title="Speech to Text", lifespan=lifespan)


class JobCreated(BaseModel):
    job_id: str


class JobState(BaseModel):
    job_id: str
    status: JobStatus
    progress: float
    language: str | None = None
    error: str | None = None


@app.get("/", response_class=HTMLResponse)
async def index() -> str:
    return (_STATIC_DIR / "index.html").read_text(encoding="utf-8")


@app.get("/favicon.ico")
async def favicon() -> Response:
    return Response(status_code=204)


@app.post("/jobs", response_model=JobCreated)
async def create_job(
    file: UploadFile,
    language: Annotated[str | None, Form()] = None,
    model: Annotated[str | None, Form()] = None,
) -> JobCreated:
    if not file.filename:
        raise HTTPException(status_code=400, detail="Missing file")

    chosen_model = model or None  # empty string from the form means "server default"
    if chosen_model is not None and chosen_model not in _ALLOWED_MODELS:
        raise HTTPException(status_code=400, detail=f"Unknown model '{chosen_model}'")

    job = service.create_job(file.filename)
    dest = settings.upload_dir / f"{job.id}_{Path(file.filename).name}"
    await _save_upload(file, dest)

    lang = language or None  # empty string from the form means auto-detect
    # CPU-bound work runs in a thread so the event loop stays responsive.
    asyncio.create_task(asyncio.to_thread(service.run, job.id, dest, lang, chosen_model))
    return JobCreated(job_id=job.id)


@app.get("/jobs/{job_id}", response_model=JobState)
async def get_job(job_id: str) -> JobState:
    job = service.get_job(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Unknown job")
    language = job.result.language if job.result else None
    return JobState(
        job_id=job.id,
        status=job.status,
        progress=job.progress,
        language=language,
        error=job.error,
    )


@app.get("/jobs/{job_id}/download")
async def download(job_id: str) -> Response:
    job = service.get_job(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Unknown job")
    if job.status is not JobStatus.COMPLETED or job.result is None:
        raise HTTPException(status_code=409, detail="Job not completed")

    body = formatter.format(job.result)
    filename = f"{Path(job.filename).stem}.{formatter.extension}"
    headers = {"Content-Disposition": _content_disposition(filename)}
    return PlainTextResponse(body, media_type=formatter.media_type, headers=headers)


def _content_disposition(filename: str) -> str:
    """Build an RFC 6266 header that survives non-latin-1 filenames.

    HTTP headers are latin-1 only, so a Unicode filename (accents, fancy
    quotes from a video title, emoji) would crash the response. We send an
    ASCII fallback plus a UTF-8 `filename*` that modern browsers prefer.
    """
    ascii_name = filename.encode("ascii", "replace").decode("ascii").replace('"', "'")
    quoted_utf8 = quote(filename, safe="")
    return f"attachment; filename=\"{ascii_name}\"; filename*=UTF-8''{quoted_utf8}"


async def _save_upload(file: UploadFile, dest: Path) -> None:
    max_bytes = settings.max_upload_mb * 1024 * 1024
    written = 0
    with dest.open("wb") as out:
        while chunk := await file.read(1024 * 1024):
            written += len(chunk)
            if written > max_bytes:
                out.close()
                dest.unlink(missing_ok=True)
                raise HTTPException(
                    status_code=413,
                    detail=f"File exceeds {settings.max_upload_mb} MB limit",
                )
            out.write(chunk)
