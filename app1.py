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
VIEW_MAP = {
    # "Dashboard": "frontend.views.dashboard",
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
    if "token" not in st.session_state:
        st.session_state.token = None
    if "show_login" not in st.session_state:
        st.session_state.show_login = False
    
    # NEW ROUTING LOGIC (app_mode)
    if "app_mode" not in st.session_state:
        st.session_state["app_mode"] = "public"
        
    # Check if a login was performed recently and token exists
    if st.session_state.token and st.session_state["app_mode"] == "public":
        st.session_state["app_mode"] = "hr_portal"

    # --- ROUTING ---
    if st.session_state["app_mode"] == "public":
        # Handle query parameter routing for public pages
        query = st.query_params
        
        # In Streamlit >= 1.30, st.query_params acts like a dictionary of strings
        # We handle both list and string returns just in case
        public_page_param = query.get('public_page', 'home')
        if isinstance(public_page_param, list):
            public_page = public_page_param[0]
        else:
            public_page = public_page_param
            
        st.session_state.public_page = public_page
        
        # Route to the appropriate public view
        if public_page == 'home':
            from frontend.public.views.home import render_page as render_home
            render_home()
        elif public_page == 'about':
            from frontend.public.views.about import render_page as render_about
            render_about()
        elif public_page == 'careers':
            from frontend.public.views.careers import render_page as render_careers
            render_careers()
        elif public_page == 'job_details':
            from frontend.public.views.job_details import render_page as render_job_details
            render_job_details()
        elif public_page == 'apply':
            from frontend.public.views.apply import render_page as render_apply
            render_apply()
        elif public_page == 'hr_login':
            from frontend.public.views.hr_login import render_page as render_hr_login
            render_hr_login()
        else:
            # Fallback to home
            from frontend.public.views.home import render_page as render_home
            render_home()
            
        # We do NOT render the HR sidebar or header when in public mode
        return

    # -------------------------------------------------------------
    # HR / RECRUITER PORTAL MODE
    # -------------------------------------------------------------
    
    # If in HR mode but no token, we shouldn't be here realistically (unless testing)
    # but we can enforce it:
    if st.session_state["app_mode"] == "hr_portal" and not st.session_state.token:
        st.session_state["app_mode"] = "public"
        st.rerun()

    # Render HR Layout
    render_header()
    # If the project relies on sidebar navigation, render it
    # Currently sidebar is commented out in original file, but we should uncomment if needed, 
    # but the original had `# render_sidebar()`. Let's keep it commented if it was.
    # Wait, the user said "The HR sidebar must not appear on the public website."
    # Let's import and render the sidebar since HR portal relies on it to change `st.session_state.current_page`
    render_sidebar()
    
    # Render Current HR View
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
    elif page == "Communications":
        from frontend.components.communications import render_communications
        render_communications()
    elif page == "Onboarding":
        from frontend.components.onboarding import render_onboarding
        render_onboarding()
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

    # Render HR AI Assistant
    render_ai_assistant()


if __name__ == "__main__":
    main()
