"""
services/cache.py  — HirePilot Performance Cache Layer
=========================================================
All expensive resources are initialized ONCE per server process using
st.cache_resource(), and all data fetches are memoized using
st.cache_data() with a short TTL so stale data is never served.

Import pattern in pages:
    from frontend.services.cache import get_css, get_api_data, get_ollama_client
"""

import os
import streamlit as st


# ---------------------------------------------------------------------------
# CSS CACHE — loaded from disk once, never again
# ---------------------------------------------------------------------------

@st.cache_resource(show_spinner=False)
def _load_css_files() -> str:
    """Read all CSS files from disk ONCE and cache the combined string."""
    styles_dir = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "styles"
    )
    css_files = ["style.css", "cards.css", "forms.css", "tables.css", "animations.css"]
    combined = ""
    for filename in css_files:
        filepath = os.path.join(styles_dir, filename)
        if os.path.exists(filepath):
            with open(filepath, "r", encoding="utf-8") as f:
                combined += f"\n/* --- {filename} --- */\n" + f.read()
    return combined


def inject_css_once():
    """
    Inject CSS into the page. Uses session_state to avoid re-injecting on
    every rerun of the SAME page, and cache_resource to avoid disk I/O.
    """
    if not st.session_state.get("__css_injected__"):
        css = _load_css_files()
        st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)
        st.markdown(
            '<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">',
            unsafe_allow_html=True,
        )
        st.session_state["__css_injected__"] = True


# ---------------------------------------------------------------------------
# OLLAMA / AI CLIENT — singleton per server process
# ---------------------------------------------------------------------------

@st.cache_resource(show_spinner=False)
def get_ollama_client():
    """Return a cached singleton OllamaClient. Created only once per server."""
    try:
        import sys
        root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        if root not in sys.path:
            sys.path.insert(0, root)
        from backend.ai.ollama_client import OllamaClient
        return OllamaClient()
    except Exception:
        return None


# ---------------------------------------------------------------------------
# DATA CACHE — API responses memoized with short TTL
# ---------------------------------------------------------------------------

@st.cache_data(ttl=30, show_spinner=False)
def get_jobs_cached(search="", department="All", status="All", sort_by="updated_at"):
    """Cached job list. Refreshes every 30 seconds."""
    try:
        import httpx
        resp = httpx.get(
            "http://localhost:8000/jobs",
            params={"search": search, "department": department,
                    "status": status, "sort_by": sort_by},
            timeout=5.0
        )
        return resp.json() if resp.status_code == 200 else []
    except Exception:
        return []


@st.cache_data(ttl=30, show_spinner=False)
def get_candidates_cached(search="", status="All", skill="All"):
    """Cached candidate list. Refreshes every 30 seconds."""
    try:
        import httpx
        resp = httpx.get(
            "http://localhost:8000/candidates",
            params={"search": search, "status": status, "skill": skill},
            timeout=5.0
        )
        return resp.json() if resp.status_code == 200 else []
    except Exception:
        return []


@st.cache_data(ttl=30, show_spinner=False)
def get_interviews_cached():
    """Cached interview list. Refreshes every 30 seconds."""
    try:
        import httpx
        resp = httpx.get("http://localhost:8000/interviews", timeout=5.0)
        return resp.json() if resp.status_code == 200 else []
    except Exception:
        return []


@st.cache_data(ttl=30, show_spinner=False)
def get_employees_cached():
    """Cached employee list. Refreshes every 30 seconds."""
    try:
        import httpx
        resp = httpx.get("http://localhost:8000/employees", timeout=5.0)
        return resp.json() if resp.status_code == 200 else []
    except Exception:
        return []


@st.cache_data(ttl=30, show_spinner=False)
def get_uploads_cached():
    """Cached upload history. Refreshes every 30 seconds."""
    try:
        import httpx
        resp = httpx.get("http://localhost:8000/resume/history", timeout=5.0)
        return resp.json() if resp.status_code == 200 else []
    except Exception:
        return []


def invalidate_jobs():
    """Call after any write operation to jobs to bust the cache."""
    get_jobs_cached.clear()


def invalidate_candidates():
    """Call after any write operation to candidates to bust the cache."""
    get_candidates_cached.clear()


def invalidate_interviews():
    get_interviews_cached.clear()


def invalidate_employees():
    get_employees_cached.clear()


def invalidate_uploads():
    get_uploads_cached.clear()
