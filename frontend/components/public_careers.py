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

    with st.spinner("Loading job listings..."):
        all_jobs = get_public_jobs(search="", department=dept_api, location=loc_api, employment_type=etype_api) or []

    if not all_jobs:
        st.markdown(
            '<div class="hp-container"><div class="hp-no-jobs"><p>No job openings match your filters right now. Try broadening your search, or check back again soon.</p></div></div>',
            unsafe_allow_html=True,
        )
        return

    # Build all job cards first, then render once
    job_cards = ""
    for i, job in enumerate(all_jobs):
        title = job.get("title") or "Role"
        dept = job.get("department") or ""
        loc = job.get("location") or ""
        etype = job.get("employment_type") or ""
        desc = job.get("short_description") or job.get("description") or ""
        desc = (desc[:140] + "...") if len(desc) > 140 else desc
        job_id = job.get("id", i)
        job_cards += f"""
        <div class="hp-job-card">
          <div class="hp-job-header">
            <h3>{title}</h3>
            <span class="hp-job-badge">{etype}</span>
          </div>
          <div class="hp-job-meta">
            <div class="hp-job-meta-item">
              <span class="hp-job-meta-icon">🏢</span>
              <span>{dept}</span>
            </div>
            <div class="hp-job-meta-item">
              <span class="hp-job-meta-icon">📍</span>
              <span>{loc}</span>
            </div>
            <div class="hp-job-meta-item">
              <span class="hp-job-meta-icon">💼</span>
              <span>{etype}</span>
            </div>
          </div>
          <div class="hp-job-description">
            <p>{desc}</p>
          </div>
          <div class="hp-job-footer">
            <button class="hp-btn hp-btn-primary hp-btn-sm" onclick="window.location.href='#apply'">Apply Now</button>
          </div>
        </div>
        """

    st.markdown(
        f"""
        <section class="hp-section hp-section-alt" id="featured-jobs">
          <div class="hp-container">
            <div class="hp-section-header">
              <div class="hp-section-tag">{J["tag"]}</div>
              <h2>{J["title"]}</h2>
              <p>{J["subtitle"]}</p>
            </div>
            <div class="hp-jobs-grid" id="featured-jobs-grid">
              {job_cards}
            </div>
            <div class="hp-jobs-cta">
              <a href="#careers" class="hp-btn hp-btn-secondary hp-btn-lg">View All Open Positions</a>
            </div>
          </div>
        </section>
        """,
        unsafe_allow_html=True,
    )