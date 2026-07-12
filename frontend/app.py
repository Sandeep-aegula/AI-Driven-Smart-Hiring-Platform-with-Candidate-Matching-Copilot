"""
app.py â€” HirePilot SPA Entry Point
=====================================
Single entry point for the entire application.

Rules:
  â€¢ st.set_page_config() is called ONCE â€” right here, at the top.
  â€¢ CSS is injected ONCE per browser session via services/cache.py.
  â€¢ The sidebar is rendered by shared/sidebar.py on every rerun.
  â€¢ Navigation happens by changing st.session_state["current_page"].
  â€¢ NEVER import or call st.switch_page() anywhere in this project.

Run:
    streamlit run app.py
"""

import os
import sys
import subprocess
import threading
import streamlit as st

# â”€â”€ Path setup â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
ROOT = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(ROOT)
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# â”€â”€ Single page config â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
st.set_page_config(
    page_title="HirePilot â€” AI Recruitment Copilot",
    page_icon="âœˆï¸",
    layout="wide",
    initial_sidebar_state="expanded",
)

# â”€â”€ Core services â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
from frontend.services.app_state import AppState
from frontend.services.cache import inject_css_once
from frontend.components.sidebar import render_sidebar
from frontend.components.header import render_header

# â”€â”€ Page components (imported lazily inside the dispatch block) â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

# â”€â”€ Bootstrap â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
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

    # â”€â”€ Global Footer (Rendered first to bypass lazy-loading scroll virtualization) â”€â”€
    st.markdown("""
    <div class="hp-footer" id="hp-global-footer">
        <i class="fa-solid fa-paper-plane" style="color: #6366F1;"></i>
        <span style="font-weight: 700; color: #475569;">HirePilot</span>
        <span style="color: #CBD5E1;">â€¢</span>
        <i class="fa-solid fa-shield-halved" style="color: #6366F1;"></i>
        <span style="font-weight: 700; color: #475569;">Enterprise SaaS</span>
        <span style="color: #CBD5E1;">â€¢</span>
        <i class="fa-solid fa-server" style="color: #6366F1;"></i>
        <span style="font-weight: 700; color: #475569;">Local Ollama (qwen2.5-coder:7b)</span>
    </div>
    """, unsafe_allow_html=True)

    # 3. Attempt to start backend & Ollama AI server (silently, if not already running)
    if not st.session_state.get("__backend_started__"):
        _start_backend()
        _start_ollama()
        st.session_state["__backend_started__"] = True

    # 4. Persistent sidebar â€” renders on EVERY rerun, never destroyed
    render_sidebar()

    # 5. Persistent header â€” breadcrumb, search, notifications, date
    render_header()

    # 6. Content dispatch â€” only the content area changes
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



