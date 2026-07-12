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

    # --- RENDER LAYOUT ---
    render_sidebar()
    render_header()

    # --- RENDER CURRENT VIEW ---
    # current_view_module = VIEW_MAP.get(st.session_state.current_page)
    # if current_view_module:
    #     module = __import__(current_view_module, fromlist=['render'])
    #     module.render()
    # else:
    #     st.error("View not found!")

    st.info("Refactoring in progress. Views will be connected here.")


if __name__ == "__main__":
    main()
