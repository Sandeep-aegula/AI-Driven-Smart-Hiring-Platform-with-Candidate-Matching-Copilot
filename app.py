"""
app.py - Main entry point for the HirePilot Streamlit SPA.
"""
import streamlit as st
import os
import sys

# --- PATH SETUP ---
# Add the project root to the Python path
# This allows us to import modules from the 'frontend' directory
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

from frontend.components.sidebar import render_sidebar
from frontend.components.header import render_header
from frontend.components.ai_assistant import render_ai_assistant
from frontend.services.cache import inject_css_once

# --- VIEW MAPPING ---
# Maps the page name from the sidebar to the corresponding view module
# We will add the view functions here as we refactor them.
VIEW_MAP = {
    # "Dashboard": "frontend.views.dashboard",
    # "Jobs": "frontend.views.jobs",
    # "Candidates": "frontend.views.candidates",
    # "Resume Parser": "frontend.views.resume_parser",
    # "AI Screening": "frontend.views.ai_screening",
    # "Interviews": "frontend.views.interviews",
    # "Employees": "frontend.views.employees",
    # "Analytics": "frontend.views.analytics",
    # "Reports": "frontend.views.reports",
    # "AI Copilot": "frontend.views.ai_copilot",
}

def main():
    """Main function to render the HirePilot application."""
    st.set_page_config(
        page_title="HirePilot - AI Recruitment Copilot",
        page_icon="✈️",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # --- HIDE STREAMLIT'S DEFAULT UI ---
    hide_streamlit_style = """
                <style>
                #MainMenu {visibility: hidden;}
                footer {visibility: hidden;}
                header {visibility: hidden;}
                </style>
                """
    st.markdown(hide_streamlit_style, unsafe_allow_html=True)
    
    # --- INITIALIZE SESSION STATE ---
    if "current_page" not in st.session_state:
        st.session_state.current_page = "Dashboard"

    # --- LOAD APP STYLES AND FORCE SIDEBAR OPEN ---
    inject_css_once()

    # --- RENDER LAYOUT ---
    # render_sidebar()
    render_header()

# --- RENDER CURRENT VIEW ---
    page = st.session_state.current_page
    
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
    elif page == "Analytics":
        from frontend.components.analytics import render_analytics
        render_analytics()
    elif page == "Reports":
        from frontend.components.reports import render_reports
        render_reports()
    elif page == "AI Copilot":
        import importlib
        import frontend.views.ai_copilot as ai_copilot_view

        if not hasattr(ai_copilot_view, "render_ai_copilot"):
            ai_copilot_view = importlib.reload(ai_copilot_view)

        ai_copilot_view.render_ai_copilot()
    else:
        st.error(f"View not found! {page}")

    # --- RENDER AI ASSISTANT (Floating Chat Widget) ---
    render_ai_assistant()


if __name__ == "__main__":
    main()


# Light mode update and sidebar collapse fix
if __name__ == "__main__":
    main()
