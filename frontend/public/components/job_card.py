"""Reusable job card component for the public website."""

import streamlit as st

def render_job_card(job):
    """
    Render a single job card.

    Args:
        job (dict): A dictionary containing job details from mock_jobs.py
    """
    st.markdown(
        f"""
        <div class="hp-job-card" style="border: 1px solid #E2E8F0; padding: 1.5rem; border-radius: 8px; margin-bottom: 1rem; background: white; box-shadow: 0 1px 3px rgba(0,0,0,0.1);">
            <h3 style="margin-top: 0; color: #0F172A;">{job['title']}</h3>
            <div class="hp-job-meta" style="margin-bottom: 1rem; display: flex; gap: 0.5rem; flex-wrap: wrap;">
                <span class="hp-badge" style="background: #F1F5F9; color: #334155; padding: 0.25rem 0.5rem; border-radius: 4px; font-size: 0.875rem;">🏢 {job['department']}</span>
                <span class="hp-badge" style="background: #F1F5F9; color: #334155; padding: 0.25rem 0.5rem; border-radius: 4px; font-size: 0.875rem;">📍 {job['location']}</span>
                <span class="hp-badge" style="background: #F1F5F9; color: #334155; padding: 0.25rem 0.5rem; border-radius: 4px; font-size: 0.875rem;">⏱️ {job['employment_type']}</span>
            </div>
            <div class="hp-job-skills" style="margin-bottom: 1rem; font-size: 0.875rem; color: #475569;">
                <strong>Skills:</strong> {', '.join(job['required_skills'])}
            </div>
            <p class="hp-job-desc" style="color: #475569;">{job['short_description']}</p>
        </div>
        """,
        unsafe_allow_html=True
    )
    
    # We use a Streamlit button for the "View Job" action so we can intercept it
    # and update the session state/query params.
    if st.button("View Job", key=f"view_job_{job['id']}"):
        st.session_state.selected_job_id = job['id']
        st.session_state.public_page = "job_details"
        st.query_params["public_page"] = "job_details"
        st.rerun()
