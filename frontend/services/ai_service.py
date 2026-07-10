"""
services/ai_service.py — HirePilot Cached AI Service
======================================================
Wraps the Ollama client as a singleton resource (created once per server
process) and caches repeated identical prompts in session state so that
navigating back to the AI Screening page doesn't re-run the model.
"""

import streamlit as st
from typing import Optional


@st.cache_resource(show_spinner=False)
def _get_ollama_client():
    """
    Create ONE OllamaClient for the lifetime of the Streamlit server process.
    cache_resource ensures this is shared across all user sessions and page reruns.
    """
    import os, sys
    root = os.path.normpath(
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..")
    )
    if root not in sys.path:
        sys.path.insert(0, root)
    try:
        from backend.ai.ollama_client import OllamaClient
        client = OllamaClient()
        return client
    except Exception as e:
        return None


def get_client():
    """Public accessor for the cached Ollama client."""
    return _get_ollama_client()


@st.cache_data(ttl=300, show_spinner=False)
def cached_screen(candidate_id: str, job_id: str) -> Optional[dict]:
    """
    Cache AI screening result for (candidate_id, job_id) pairs.
    TTL = 5 min — enough to avoid re-running while user reviews the result,
    but fresh enough to reflect any manual edits.
    """
    try:
        import httpx
        resp = httpx.get(
            "http://localhost:8000/ai-screening",
            params={"candidate_id": candidate_id, "job_id": job_id},
            timeout=120.0,
        )
        return resp.json() if resp.status_code == 200 else None
    except Exception:
        return None


@st.cache_data(ttl=600, show_spinner=False)
def cached_generate_questions(stage: str, skills_key: str) -> list:
    """
    Cache generated interview questions for (stage, skills) pairs.
    TTL = 10 min.
    """
    try:
        import httpx, json
        skills = json.loads(skills_key)
        resp = httpx.post(
            "http://localhost:8000/interviews/generate-questions",
            json={"stage": stage, "skills": skills},
            timeout=90.0,
        )
        return resp.json() if resp.status_code == 200 else []
    except Exception:
        return []


def invalidate_screening(candidate_id: str, job_id: str):
    """Call after manual status overrides to force a fresh screening result."""
    cached_screen.clear()


def invalidate_questions():
    cached_generate_questions.clear()
