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
def _load_css_files(css_revision: float = 0) -> str:
    """Read ALL CSS files from assets/css/ once per server process."""
    _ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
    _ASSETS_CSS = os.path.join(_ROOT, "assets", "css")
    files = ["global.css", "sidebar.css", "header.css", "cards.css", "forms.css", "tables.css", "animations.css"]
    combined = ""
    for name in files:
        path = os.path.join(_ASSETS_CSS, name)
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                combined += f"\n/* ── {name} ── */\n" + f.read()
    return combined


def inject_css_once():
    """
    Inject the combined CSS bundle into the page on every rerun.
    """
    css_dir = os.path.normpath(
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "assets", "css")
    )
    css_revision = max(
        (os.path.getmtime(os.path.join(css_dir, name)) for name in os.listdir(css_dir)),
        default=0,
    )
    css = _load_css_files(css_revision)
    if css:
        st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)
    st.markdown(
        '<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">',
        unsafe_allow_html=True
    )



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


def get_gemini_client():
    """Compatibility alias for the AI Copilot page's Gemini client import."""
    return get_ollama_client()


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
    """Cached candidate list. Refreshes every 30 seconds.

    Returns a list of candidate dictionaries.
    """
    def _normalize_response(data):
        """Normalize API response to list of candidates."""
        if isinstance(data, list):
            return data
        if isinstance(data, dict):
            # Check for items first (from get_candidates api_client)
            items = data.get("items")
            if isinstance(items, list):
                return items
            # Check other common keys
            for key in ("data", "candidates", "results"):
                val = data.get(key)
                if isinstance(val, list):
                    return val
        return []

    try:
        import httpx
        resp = httpx.get(
            "http://localhost:8000/candidates",
            params={"search": search, "status": status, "skill": skill},
            timeout=5.0,
        )
        if resp.status_code != 200:
            return []
        data = resp.json()
        return _normalize_response(data)
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


@st.cache_data(ttl=30, show_spinner=False)
def get_job_cached(job_id):
    """Cached single job retrieval. Refreshes every 30 seconds."""
    try:
        import httpx
        resp = httpx.get(f"http://localhost:8000/jobs/{job_id}", timeout=5.0)
        return resp.json() if resp.status_code == 200 else None
    except Exception:
        return None


@st.cache_data(ttl=30, show_spinner=False)
def get_candidate_cached(candidate_id):
    """Cached single candidate retrieval. Refreshes every 30 seconds."""
    try:
        import httpx
        resp = httpx.get(f"http://localhost:8000/candidates/{candidate_id}", timeout=5.0)
        return resp.json() if resp.status_code == 200 else None
    except Exception:
        return None


@st.cache_data(ttl=30, show_spinner=False)
def get_employee_cached(employee_id):
    """Cached single employee retrieval. Refreshes every 30 seconds."""
    try:
        import httpx
        resp = httpx.get(f"http://localhost:8000/employees/{employee_id}", timeout=5.0)
        return resp.json() if resp.status_code == 200 else None
    except Exception:
        return None


@st.cache_data(ttl=300, show_spinner=False)
def cached_screen(candidate_id: str, job_id: str):
    """Cache AI screening result for (candidate_id, job_id) pairs. TTL=5 min."""
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


def invalidate_jobs():
    """Call after any write operation to jobs to bust the cache."""
    get_jobs_cached.clear()
    get_job_cached.clear()


def invalidate_candidates():
    """Call after any write operation to candidates to bust the cache."""
    get_candidates_cached.clear()
    get_candidate_cached.clear()


def invalidate_interviews():
    get_interviews_cached.clear()


def invalidate_employees():
    get_employees_cached.clear()
    get_employee_cached.clear()


def invalidate_uploads():
    get_uploads_cached.clear()


def invalidate_screening():
    cached_screen.clear()

