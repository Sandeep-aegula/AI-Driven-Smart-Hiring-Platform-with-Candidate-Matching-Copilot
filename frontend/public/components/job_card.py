"""Reusable job card component for the public website."""

import streamlit as st

def render_job_card(job):
    """
    Render a single job card.

    Args:
        job (dict): A dictionary containing job details from mock_jobs.py
    """
    # Build the complete job card HTML including the button in a single string
    card_html = f"""
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
        <div style="margin-top: 1rem; padding-top: 1rem; border-top: 1px solid #E2E8F0;">
            <a href="?public_page=job_details&job_id={job['id']}" class="hp-btn hp-btn-primary hp-btn-sm" style="text-decoration: none; display: inline-block;">View Job</a>
        </div>
    </div>
    """
    
    st.markdown(card_html, unsafe_allow_html=True)
