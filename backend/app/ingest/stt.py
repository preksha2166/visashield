"""Speech-to-text for voicemails and call recordings (Whisper via an OpenAI-compatible API).

Defaults to Groq's hosted whisper-large-v3-turbo, so no audio model runs locally (the
lite runtime stays ~270 MB). Audio is sent to the STT provider and never stored.
"""
import os
from functools import lru_cache

from app import config

STT_MODEL = os.getenv("STT_MODEL", "whisper-large-v3-turbo")
STT_BASE_URL = os.getenv("STT_BASE_URL") or config.LLM_BASE_URL
STT_API_KEY = os.getenv("STT_API_KEY") or config.LLM_API_KEY
AUDIO_EXTS = {".mp3", ".m4a", ".wav", ".ogg", ".opus", ".webm", ".flac", ".mp4", ".mpeg", ".mpga", ".aac", ".amr", ".3gp"}


def available() -> bool:
    return bool(STT_API_KEY)


@lru_cache(maxsize=1)
def _client():
    from openai import OpenAI

    return OpenAI(api_key=STT_API_KEY, base_url=STT_BASE_URL, timeout=60, max_retries=1)


def transcribe(audio: bytes, filename: str) -> tuple[str, str | None]:
    """Return (transcript, detected_language)."""
    resp = _client().audio.transcriptions.create(
        model=STT_MODEL,
        file=(filename, audio),
        response_format="verbose_json",
        temperature=0.0,
    )
    text = (getattr(resp, "text", "") or "").strip()
    return text, getattr(resp, "language", None)
