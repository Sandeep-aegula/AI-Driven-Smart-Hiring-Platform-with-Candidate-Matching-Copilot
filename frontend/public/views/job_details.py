import streamlit as st
from frontend.public.utils import inject_public_css
from frontend.public.components.public_navbar import render_public_navbar
from frontend.public.components.public_footer import render_public_footer
from frontend.components.api_client import get_public_job_details

def render_page():
    """Render the Job Details page for the public website."""
    # Load CSS
    inject_public_css()
    # Show navbar with active page
    render_public_navbar(active_page="careers")
    
    # Check if a job is selected
    job_id = st.session_state.get("selected_job_id")
    if not job_id:
        st.warning("No job selected. Redirecting to careers...")
        st.session_state.public_page = "careers"
        st.query_params["public_page"] = "careers"
        st.rerun()
        return

    job = get_public_job_details(job_id)
    if not job:
        st.error("Job not found.")
        if st.button("Back to Careers"):
            st.session_state.public_page = "careers"
            st.query_params["public_page"] = "careers"
            st.rerun()
        return

    # Job Header
    st.markdown(
        f"""
        <section class="hp-section" style="padding: 4rem 1rem; background: linear-gradient(135deg, #F8FAFC 0%, #E2E8F0 100%);">
          <div class="hp-container">
            <h1 style="font-size: 2.5rem; color: #0F172A; margin-bottom: 1rem;">{job['title']}</h1>
            <div style="display: flex; gap: 1rem; flex-wrap: wrap; margin-bottom: 2rem;">
                <span style="background: white; color: #334155; padding: 0.5rem 1rem; border-radius: 4px; font-weight: 500; box-shadow: 0 1px 2px rgba(0,0,0,0.05);">🏢 {job.get('department', '')}</span>
                <span style="background: white; color: #334155; padding: 0.5rem 1rem; border-radius: 4px; font-weight: 500; box-shadow: 0 1px 2px rgba(0,0,0,0.05);">📍 {job.get('location', '')}</span>
                <span style="background: white; color: #334155; padding: 0.5rem 1rem; border-radius: 4px; font-weight: 500; box-shadow: 0 1px 2px rgba(0,0,0,0.05);">⏱️ {job.get('employment_type', '')}</span>
            </div>
          </div>
        </section>
        """,
        unsafe_allow_html=True,
    )
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown(
            f"""
            <div style="background: white; padding: 2rem; border-radius: 8px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); margin-top: -2rem; position: relative; z-index: 10;">
                <h2 style="color: #0F172A; margin-bottom: 1rem; font-size: 1.5rem;">Job Description</h2>
                <p style="color: #475569; font-size: 1.05rem; line-height: 1.7; margin-bottom: 2rem;">{job.get('description', '')}</p>
                
                <h2 style="color: #0F172A; margin-bottom: 1rem; font-size: 1.5rem;">Responsibilities</h2>
                <ul style="color: #475569; font-size: 1.05rem; line-height: 1.7; margin-bottom: 2rem;">
                    {''.join([f"<li>{r}</li>" for r in job.get('responsibilities', [])])}
                </ul>
                
                <h2 style="color: #0F172A; margin-bottom: 1rem; font-size: 1.5rem;">Qualifications</h2>
                <ul style="color: #475569; font-size: 1.05rem; line-height: 1.7; margin-bottom: 2rem;">
                    {''.join([f"<li>{q}</li>" for q in job.get('qualifications', [])])}
                </ul>
                
                <h2 style="color: #0F172A; margin-bottom: 1rem; font-size: 1.5rem;">Experience Requirements</h2>
                <p style="color: #475569; font-size: 1.05rem; line-height: 1.7;">{job.get('experience_required', '')}</p>
            </div>
            """,
            unsafe_allow_html=True
        )
        
    with col2:
        st.markdown(
            """
            <div style="background: white; padding: 2rem; border-radius: 8px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); margin-top: -2rem; position: relative; z-index: 10;">
                <h3 style="color: #0F172A; margin-bottom: 1rem; font-size: 1.25rem;">Interested in this role?</h3>
            </div>
            """,
            unsafe_allow_html=True
        )
        if st.button("Apply for This Job", width="stretch", type="primary"):
            st.session_state.public_page = "apply"
            st.query_params["public_page"] = "apply"
            st.rerun()
            
        st.markdown("<br>", unsafe_allow_html=True)
        
        if st.button("Back to Careers", width="stretch"):
            st.session_state.public_page = "careers"
            st.query_params["public_page"] = "careers"
            st.rerun()
            
        st.markdown(
            f"""
            <div style="background: white; padding: 2rem; border-radius: 8px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); margin-top: 1rem;">
                <h3 style="color: #0F172A; margin-bottom: 1rem; font-size: 1.1rem;">Required Skills</h3>
                <div style="display: flex; gap: 0.5rem; flex-wrap: wrap;">
                    {''.join([f'<span style="background: #E2E8F0; color: #334155; padding: 0.25rem 0.75rem; border-radius: 16px; font-size: 0.875rem;">{s}</span>' for s in job.get('required_skills', [])])}
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

    st.markdown("<br><br>", unsafe_allow_html=True)
    render_public_footer()
