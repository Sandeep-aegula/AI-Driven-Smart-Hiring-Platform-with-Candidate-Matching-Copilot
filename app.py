"""
app.py — HirePilot SPA Entry Point
=====================================
Single entry point for the entire application.

Rules:
  • st.set_page_config() is called ONCE — right here, at the top.
  • CSS is injected ONCE per browser session via services/cache.py.
  • The sidebar is rendered by shared/sidebar.py on every rerun.
  • Navigation happens by changing st.session_state["current_page"].
  • NEVER import or call st.switch_page() anywhere in this project.

Run:
    streamlit run app.py
"""

import os
import sys
import subprocess
import threading
import streamlit as st

# ── Path setup ───────────────────────────────────────────────────────────────
ROOT = os.path.dirname(os.path.abspath(__file__))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

# ── Single page config ───────────────────────────────────────────────────────
st.set_page_config(
    page_title="HirePilot — AI Recruitment Copilot",
    page_icon="✈️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Core services ─────────────────────────────────────────────────────────────
from services.state import init_state
from services.cache import inject_css_once
from shared.sidebar import render_sidebar
from shared.header import render_header

# ── Page components (imported lazily inside the dispatch block) ────────────────

# ── Bootstrap ─────────────────────────────────────────────────────────────────
def _start_backend():
    """Start FastAPI backend in a background thread if not already running."""
    try:
        import httpx
        httpx.get("http://localhost:8000/health", timeout=2.0)
        return  # Already running
    except Exception:
        pass

    def _run():
        backend_main = os.path.join(ROOT, "backend", "main.py")
        if os.path.exists(backend_main):
            subprocess.Popen(
                [sys.executable, "-m", "uvicorn", "backend.main:app",
                 "--host", "127.0.0.1", "--port", "8000", "--reload"],
                cwd=ROOT,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )

    t = threading.Thread(target=_run, daemon=True)
    t.start()


# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    # 1. Initialise session state (no-op on subsequent reruns)
    init_state()

    # 2. Inject CSS exactly once per browser session (prevents flicker)
    inject_css_once()

    # 3. Attempt to start backend (silently, if not already running)
    if not st.session_state.get("__backend_started__"):
        _start_backend()
        st.session_state["__backend_started__"] = True

    # 4. Persistent sidebar — renders on EVERY rerun, never destroyed
    render_sidebar()

    # 5. Persistent header — breadcrumb, search, notifications, date
    render_header()

    # 6. Content dispatch — only the content area changes
    page = st.session_state.get("current_page", "Dashboard")

    if page == "Dashboard":
        from components.dashboard import render_dashboard
        render_dashboard()

    elif page == "Jobs":
        from components.jobs import render_jobs
        render_jobs()

    elif page == "Candidates":
        from components.candidates import render_candidates
        render_candidates()

    elif page == "Resume Parser":
        from components.resume_parser import render_resume_parser
        render_resume_parser()

    elif page == "AI Screening":
        from components.ai_screening import render_ai_screening
        render_ai_screening()

    elif page == "Interviews":
        from components.interviews import render_interviews
        render_interviews()

    elif page == "Employees":
        from components.employees import render_employees
        render_employees()

    elif page == "Analytics":
        from components.analytics import render_analytics
        render_analytics()

    elif page == "Reports":
        from components.reports import render_reports
        render_reports()

    elif page == "AI Copilot":
        from components.ai_copilot import render_ai_copilot
        render_ai_copilot()

    else:
        st.error(f"Page '{page}' not found.")


main()
