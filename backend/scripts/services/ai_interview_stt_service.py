"""
AI Interview module — isolated speech-to-text service.

No speech-to-text service exists elsewhere in this application, so this is a
self-contained implementation using faster-whisper (local, CPU-friendly
Whisper inference). It is not reused by, and does not modify, any other
module.

transcribeAnswer() -> transcribe_answer(): candidate voice (WAV bytes) -> transcript text.
"""
from __future__ import annotations

import asyncio
import io
import logging

logger = logging.getLogger(__name__)

_model = None
_model_lock = asyncio.Lock()


def _load_model():
    """Lazily load the Whisper model once per process (blocking; only ever
    called from a worker thread, never on the event loop)."""
    global _model
    if _model is None:
        from faster_whisper import WhisperModel
        logger.info("Loading faster-whisper 'tiny.en' model (first use only)...")
        _model = WhisperModel("tiny.en", device="cpu", compute_type="int8")
        logger.info("faster-whisper model loaded.")
    return _model


def _transcribe_sync(audio_bytes: bytes) -> str:
    model = _load_model()
    segments, _info = model.transcribe(io.BytesIO(audio_bytes), beam_size=1, vad_filter=True)
    return " ".join(segment.text.strip() for segment in segments).strip()


async def transcribe_answer(audio_bytes: bytes) -> str:
    """Transcribe a candidate's recorded answer (WAV bytes) into text.

    Runs the (CPU-bound, blocking) Whisper inference in a worker thread so it
    never blocks the asyncio event loop / other in-flight requests.
    """
    if not audio_bytes:
        return ""
    try:
        return await asyncio.to_thread(_transcribe_sync, audio_bytes)
    except Exception:
        logger.exception("Speech-to-text transcription failed")
        raise
