"""Run the app:  uv run python -m speech_to_text.web"""

from __future__ import annotations

import uvicorn

from speech_to_text.config import settings

if __name__ == "__main__":
    uvicorn.run("speech_to_text.web.api:app", host=settings.host, port=settings.port)
