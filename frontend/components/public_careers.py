import streamlit as st
from frontend.components.api_client import get_public_jobs


def render_careers_page(C, jobs=None):
    """Render the Careers page content."""
    J = C["featured_jobs"]

    st.markdown(
        f"""
        <section class="hp-hero" style="padding: 6rem 0 2rem;">
          <div class="hp-container">
            <div class="hp-section-header" style="margin-bottom: 2rem;">
              <div class="hp-section-tag">Open Roles</div>
              <h2>Explore Career Opportunities</h2>
              <p>Find a role that matches your skills, experience and career goals. We update this page daily as new positions open up.</p>
            </div>
          </div>
        </section>
        """,
        unsafe_allow_html=True,
    )

    f1, f2, f3 = st.columns(3)
    with f1:
        department = st.selectbox("Department",
            ["All Departments", "Engineering", "Technology", "Human Resources", "Operations", "Product", "Data"],
            key="career_department")
    with f2:
        location = st.selectbox("Location",
            ["All Locations", "Hyderabad", "Bengaluru", "Chennai", "Mumbai", "Remote"],
            key="career_location")
    with f3:
        employment_type = st.selectbox("Employment Type",
            ["All Types", "Full-Time", "Part-Time", "Internship", "Contract"],
            key="career_employment_type")

    dept_api = "All" if department == "All Departments" else department
    loc_api = "All" if location == "All Locations" else location
    etype_api = "All" if employment_type == "All Types" else employment_type

    all_jobs = []
    try:
        with st.spinner("Loading job listings..."):
            all_jobs = get_public_jobs(search="", department=dept_api, location=loc_api, employment_type=etype_api) or []
    except Exception:
        all_jobs = []

    if not all_jobs:
        st.markdown(
            '<div class="hp-container"><div class="hp-no-jobs"><p>No job openings match your filters right now. Try broadening your search, or check back again soon.</p></div></div>',
            unsafe_allow_html=True,
        )
        return

    # Render job cards using the same pattern as _render_featured_jobs_section
    for i, job in enumerate(all_jobs):
        title = job.get("title") or "Role"
        dept = job.get("department") or ""
        loc = job.get("location") or ""
        etype = job.get("employment_type") or ""
        desc = job.get("short_description") or job.get("description") or ""
        desc = (desc[:140] + "…") if len(desc) > 140 else desc
        with st.container(border=True):
            st.markdown(f"**{title}**")
            st.markdown(f"<small><i>{dept} · {loc} · {etype}</i></small>", unsafe_allow_html=True)
            st.caption(desc)
            if st.button("View Job", key=f"career_job_{job.get('id')}_{i}", type="primary"):
                st.session_state.selected_public_job = job.get("id")
                st.session_state.public_page = "JobDetail"
                st.rerun()