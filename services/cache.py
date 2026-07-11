"""
services/cache.py — HirePilot Performance Cache Layer
=======================================================
• CSS files are read from disk ONCE per server process via @st.cache_resource
• CSS is injected into the DOM ONCE per browser session via a session flag
• API data is cached with short TTL via @st.cache_data
• Ollama client is a singleton via @st.cache_resource
"""

from __future__ import annotations

import os
import streamlit as st


# ── Resolve project root ─────────────────────────────────────────────────────
_ROOT = os.path.normpath(
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
)
_ASSETS_CSS = os.path.join(_ROOT, "assets", "css")
_FONT_AWESOME = (
    '<link rel="stylesheet" '
    'href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">'
)


# ── CSS Cache ────────────────────────────────────────────────────────────────

@st.cache_resource(show_spinner=False)
def _load_css_bundle() -> str:
    """Read ALL CSS files from assets/css/ once per server process."""
    files = ["global.css", "sidebar.css", "header.css", "animations.css"]
    combined = ""
    for name in files:
        path = os.path.join(_ASSETS_CSS, name)
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                combined += f"\n/* ── {name} ── */\n" + f.read()
    return combined


def inject_css_once() -> None:
    """
    Inject the combined CSS bundle into Streamlit exactly ONE time per
    browser session. Subsequent reruns (page switches, filter changes, etc.)
    skip this entirely — eliminating the main cause of flickering.
    """
    if st.session_state.get("__css_injected__"):
        return
    css = _load_css_bundle()
    st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)
    st.markdown(_FONT_AWESOME, unsafe_allow_html=True)
    st.session_state["__css_injected__"] = True


# ── Ollama / AI Client Singleton ─────────────────────────────────────────────

@st.cache_resource(show_spinner=False)
def get_ollama_client():
    """
    Create ONE OllamaClient for the lifetime of the Streamlit server process.
    cache_resource shares it across all user sessions and page reruns.
    """
    import sys
    if _ROOT not in sys.path:
        sys.path.insert(0, _ROOT)
    try:
        from backend.ai.ollama_client import OllamaClient
        return OllamaClient()
    except Exception:
        return None


# ── Data Caches — short TTL prevents stale UI without spamming the API ───────

@st.cache_data(ttl=30, show_spinner=False)
def get_jobs_cached(search="", department="All", status="All", sort_by="updated_at"):
    """Cached job list. Refreshes every 30 s."""
    try:
        import httpx
        r = httpx.get(
            "http://localhost:8000/jobs",
            params={"search": search, "department": department,
                    "status": status, "sort_by": sort_by},
            timeout=5.0,
        )
        return r.json() if r.status_code == 200 else []
    except Exception:
        return []


@st.cache_data(ttl=30, show_spinner=False)
def get_candidates_cached(search="", status="All", skill="All"):
    """Cached candidate list. Refreshes every 30 s."""
    try:
        import httpx
        r = httpx.get(
            "http://localhost:8000/candidates",
            params={"search": search, "status": status, "skill": skill},
            timeout=5.0,
        )
        return r.json() if r.status_code == 200 else []
    except Exception:
        return []


@st.cache_data(ttl=30, show_spinner=False)
def get_interviews_cached():
    """Cached interview list. Refreshes every 30 s."""
    try:
        import httpx
        r = httpx.get("http://localhost:8000/interviews", timeout=5.0)
        return r.json() if r.status_code == 200 else []
    except Exception:
        return []


@st.cache_data(ttl=30, show_spinner=False)
def get_employees_cached():
    """Cached employee list. Refreshes every 30 s."""
    try:
        import httpx
        r = httpx.get("http://localhost:8000/employees", timeout=5.0)
        return r.json() if r.status_code == 200 else []
    except Exception:
        return []


@st.cache_data(ttl=30, show_spinner=False)
def get_uploads_cached():
    """Cached upload history. Refreshes every 30 s."""
    try:
        import httpx
        r = httpx.get("http://localhost:8000/resume/history", timeout=5.0)
        return r.json() if r.status_code == 200 else []
    except Exception:
        return []


@st.cache_data(ttl=300, show_spinner=False)
def cached_screen(candidate_id: str, job_id: str):
    """Cache AI screening result for (candidate_id, job_id) pairs. TTL=5 min."""
    try:
        import httpx
        r = httpx.get(
            "http://localhost:8000/ai-screening",
            params={"candidate_id": candidate_id, "job_id": job_id},
            timeout=120.0,
        )
        return r.json() if r.status_code == 200 else None
    except Exception:
        return None


# ── Cache Invalidators ───────────────────────────────────────────────────────

def invalidate_jobs():       get_jobs_cached.clear()
def invalidate_candidates(): get_candidates_cached.clear()
def invalidate_interviews():  get_interviews_cached.clear()
def invalidate_employees():   get_employees_cached.clear()
def invalidate_uploads():     get_uploads_cached.clear()
def invalidate_screening():   cached_screen.clear()
