# Speech to Text

Local browser app to transcribe long MP3 files (e.g. a 2-hour recording) into a
downloadable plain-text file, using [faster-whisper](https://github.com/SYSTRAN/faster-whisper).

Runs entirely on your machine — no audio leaves your computer.

## Architecture

Hexagonal (ports & adapters). The domain has no I/O dependencies:

```
domain/        models + ports (interfaces)        ← pure, no framework
application/   TranscriptionService               ← orchestrates ports
adapters/      faster-whisper, formatters, store  ← implement the ports
web/           FastAPI + a single static page     ← drives the application
```

Flow: upload → `job_id` → poll progress → download `.txt`. Transcription runs in
a background thread (faster-whisper releases the GIL), so the UI stays responsive
and the request never times out on a long file.

## Setup

Requires `ffmpeg` (decoding), `uv`, and optionally `yt-dlp` (to grab audio from a video URL):

```bash
brew install ffmpeg yt-dlp   # if not already installed
uv sync
cp .env.example .env  # optional — tweak model / device
```

## Get an MP3 from a video

To transcribe a video (YouTube, etc.), extract its audio as MP3 first:

```bash
yt-dlp -x --audio-format mp3 "VIDEO_URL"
```

## Run

```bash
uv run python -m speech_to_text.web
```

Open <http://127.0.0.1:8011>, pick an MP3, and transcribe.

## Configuration

Set via environment variables / `.env` (prefix `STT_`). Defaults: `small` model,
`cpu`, `int8`. On the first run the chosen model is downloaded and cached.
Larger models (`medium`, `large-v3`) are more accurate but slower.

## Test

```bash
uv run pytest
```
