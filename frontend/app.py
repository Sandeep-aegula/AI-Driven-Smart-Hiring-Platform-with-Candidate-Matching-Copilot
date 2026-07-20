"""
app.py — HirePilot SPA Entry Point
=====================================
Single entry point for the entire application.

Rules:
  * st.set_page_config() is called ONCE — right here, at the top.
  * CSS is injected ONCE per browser session via services/cache.py.
  * The sidebar is rendered by shared/sidebar.py on every rerun.
  * Navigation happens by changing st.session_state["current_page"].
  * NEVER import or call st.switch_page() anywhere in this project.

Run:
    streamlit run app.py
"""

import os
import sys
import subprocess
import threading
import streamlit as st

ROOT = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(ROOT)
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

st.set_page_config(
    page_title="HirePilot AI Recruitment Copilot",
    page_icon="✨",
    layout="wide",
    initial_sidebar_state="expanded",
)


from frontend.services.app_state import AppState
from frontend.services.cache import inject_css_once
from frontend.components.bar import render_sidebar
from frontend.components.header import render_header
from frontend.components.ai_assistant import render_ai_assistant


def _start_backend():
    """Start FastAPI backend in a background thread if not already running."""
    try:
        import httpx
        httpx.get("http://localhost:8000/health", timeout=2.0)
        return  # Already running
    except Exception:
        pass

    def _run():
        backend_api = os.path.join(PROJECT_ROOT, "backend", "api", "app.py")
        if os.path.exists(backend_api):
            subprocess.Popen(
                [sys.executable, "-m", "uvicorn", "backend.api.app:app",
                 "--host", "127.0.0.1", "--port", "8000", "--reload"],
                cwd=PROJECT_ROOT,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )

    t = threading.Thread(target=_run, daemon=True)
    t.start()


def _start_ollama():
    """Start local Ollama server and run qwen2.5-coder:7b in a background thread if not already active."""
    try:
        import httpx
        httpx.get("http://localhost:11434/", timeout=2.0)
        return  # Already running
    except Exception:
        pass

    def _run():
        try:
            # Launch Ollama background service
            subprocess.Popen(
                ["ollama", "serve"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            # Give it a moment to boot
            import time
            time.sleep(2)
            # Run/pull the qwen2.5-coder:7b model to make sure it is pre-loaded
            subprocess.Popen(
                ["ollama", "run", "qwen2.5-coder:7b"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        except Exception:
            pass

    t = threading.Thread(target=_run, daemon=True)
    t.start()


# â”€â”€ Main â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
def main():
    # 1. Initialise session state (no-op on subsequent reruns)
    AppState.init()

    # 2. Inject CSS exactly once per browser session (prevents flicker)
    inject_css_once()

    # 3. Backend & Ollama are managed externally (separate terminals)
    #    - Backend: python -m uvicorn backend.api.app:app --host 127.0.0.1 --port 8000 --reload
    #    - Ollama:  ollama serve  (then: ollama pull qwen2.5-coder:7b)

    # 4. Persistent sidebar — renders on EVERY rerun, never destroyed
    render_sidebar()

    # 5. Persistent header — breadcrumb, search, notifications, date
    # Safety init for header search field
    if "search_query" not in st.session_state:
        st.session_state.search_query = ""
    render_header()

    # 5.5. Persistent AI Assistant — floating chat widget on all pages
    # render_ai_assistant()

    # 6. Content dispatch — only the content area changes
    page = st.session_state.get("current_page", "Dashboard")

    if page == "Dashboard":
        from frontend.components.dashboard import render_dashboard
        render_dashboard()

    elif page == "Jobs":
        from frontend.components.jobs import render_jobs
        render_jobs()

    elif page == "Candidates":
        from frontend.components.candidates import render_candidates
        render_candidates()

    elif page == "Resume Parser":
        from frontend.components.resume_management import render_resume_management
        render_resume_management()

    elif page == "AI Screening":
        from frontend.components.ai_screening import render_ai_screening
        render_ai_screening()

    elif page == "Interviews":
        from frontend.components.interview_management import render_interview_management
        render_interview_management()

    elif page == "Employees":
        from frontend.components.employees import render_employees
        render_employees()

    elif page == "Communications":
        from frontend.components.communications import render_communications
        render_communications()

    elif page == "Analytics":
        from frontend.components.analytics import render_analytics
        render_analytics()

    elif page == "Reports":
        from frontend.components.reports import render_reports
        render_reports()

    elif page == "AI Copilot":
       
        from frontend.views.ai_copilot import render_ai_copilot
        render_ai_copilot()


    else:
        st.error(f"Page '{page}' not found.")
    

# Light mode update and sidebar collapse fix
main()



