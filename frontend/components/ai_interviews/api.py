"""
AI Interview module — isolated API client.

Talks only to the new /api/ai-interviews/* backend surface (plus, for the
first screen's list, the existing GET /interviews read endpoint via the
existing frontend.components.api_client.get_interviews -- reused, not
modified). No other existing API client function is touched here.
"""
from __future__ import annotations

import httpx

API_URL = "http://localhost:8000"

# AI calls (question generation, transcription, evaluation) can each take up
# to ~90s on CPU-only Ollama inference -- give them room rather than timing
# out mid-call.
_LONG_TIMEOUT = 240.0


def get_context(interview_id: int) -> dict | None:
    try:
        resp = httpx.get(f"{API_URL}/api/ai-interviews/{interview_id}/context", timeout=15.0)
        if resp.status_code == 200:
            return resp.json()
        return None
    except Exception:
        return None


def start_or_resume_session(interview_id: int, fresh: bool = False) -> dict:
    """fresh=True discards any existing in-progress session and starts a
    brand new interview (use for an explicit "Start Interview" click).
    fresh=False (default) resumes an existing in-progress session unchanged
    -- use for recovering session state lost to e.g. a page refresh, where
    silently wiping the candidate's progress would be wrong."""
    resp = httpx.post(
        f"{API_URL}/api/ai-interviews/{interview_id}/session",
        params={"fresh": fresh},
        timeout=_LONG_TIMEOUT,
    )
    resp.raise_for_status()
    return resp.json()


def get_session(session_id: int) -> dict | None:
    try:
        resp = httpx.get(f"{API_URL}/api/ai-interviews/sessions/{session_id}", timeout=15.0)
        if resp.status_code == 200:
            return resp.json()
        return None
    except Exception:
        return None


def submit_answer(session_id: int, audio_bytes: bytes) -> dict:
    """Fallback path (recorded audio, server-side STT) -- kept for browsers
    without live speech recognition support. Raises on failure."""
    files = {"audio": ("answer.wav", audio_bytes, "audio/wav")}
    resp = httpx.post(f"{API_URL}/api/ai-interviews/sessions/{session_id}/answer", files=files, timeout=_LONG_TIMEOUT)
    return _unwrap(resp)


def submit_answer_text(session_id: int, transcript: str) -> dict:
    """Primary path for the live interview: the candidate's speech was
    already transcribed live in the browser (Web Speech API). Raises on
    failure; caller is responsible for turning the exception message into a
    friendly retry prompt (the backend already returns the exact
    user-facing strings for each known failure mode)."""
    resp = httpx.post(
        f"{API_URL}/api/ai-interviews/sessions/{session_id}/answer-text",
        json={"transcript": transcript},
        timeout=_LONG_TIMEOUT,
    )
    return _unwrap(resp)


def _unwrap(resp: httpx.Response) -> dict:
    if resp.status_code >= 400:
        try:
            detail = resp.json().get("detail", "Something went wrong. Please try again.")
        except Exception:
            detail = "Something went wrong. Please try again."
        raise RuntimeError(detail)
    return resp.json()
