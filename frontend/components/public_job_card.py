import streamlit as st

def render_job_card(job: dict, key: str = None):
    """Render a simple job summary card using the public portal CSS.

    Args:
        job: Dictionary containing job data (as defined in mock_jobs).
        key: Optional Streamlit key to ensure uniqueness when rendering multiple cards.
    """
    job_id = job.get("id")
    # Use the existing feature‑card styling for consistency
    st.markdown(
        f"""
        <div class=\"hp-feature-card\" style=\"margin-bottom: 1.5rem;\">
          <h4>{job.get('title')}</h4>
          <p>{job.get('short_description')}</p>
          <ul style=\"list-style:none; padding:0; margin:0;\">
            <li><b>Department:</b> {job.get('department')}</li>
            <li><b>Location:</b> {job.get('location')}</li>
            <li><b>Type:</b> {job.get('employment_type')}</li>
          </ul>
          <a href=\"?public_page=job_details&job_id={job_id}\" class=\"hp-btn hp-btn-primary hp-btn-sm\">View Job</a>
        </div>
        """,
        unsafe_allow_html=True,
        key=key,
    )
