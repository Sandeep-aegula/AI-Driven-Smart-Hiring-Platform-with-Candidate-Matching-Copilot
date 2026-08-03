from frontend.components.api_client import get_public_job_details, submit_public_application
import streamlit as st



def _render_job_detail_page() -> None:
    job_id = st.session_state.get("selected_public_job")
    if not job_id:
        st.warning("No job selected.")
        if st.button("Back to Careers", type="primary"):
            st.session_state.public_page = "Careers"
            st.rerun()
        return
    job = get_public_job_details(job_id)
    if not job:
        st.error("This job is no longer available.")
        if st.button("Back to Careers", type="primary"):
            st.session_state.public_page = "Careers"
            st.rerun()
        return

    title = job.get("title") or "Role"
    dept = job.get("department") or ""
    loc = job.get("location") or ""
    etype = job.get("employment_type") or ""
    wmode = job.get("work_mode") or "Remote"
    exp = job.get("experience_required") or ""
    openings = job.get("openings") or ""
    deadline = job.get("deadline") or ""
    description = job.get("description") or ""
    responsibilities = job.get("responsibilities") or []
    requirements = job.get("requirements") or []
    preferred = job.get("preferred_skills") or []
    qualifications = job.get("qualifications") or []
    benefits = job.get("benefits") or []

    st.markdown(
        f"""
        <section class="hp-hero" style="padding: 5rem 0 2rem;">
          <div class="hp-container">
            <div style="margin-top: 1.5rem;">
              <div class="hp-section-tag">{dept}</div>
              <h1 style="font-size:2.25rem;margin:0.5rem 0;">{title}</h1>
              <div style="display:flex; flex-wrap:wrap; gap:1rem; color:#475569; font-weight:500;">
                <span>🏢 {dept}</span>
                <span>📍 {loc}</span>
                <span>💼 {etype}</span>
                <span>🖥️ {wmode}</span>
                {f'<span>⏱️ {exp}</span>' if exp else ''}
                {f'<span>👥 {openings} openings</span>' if openings else ''}
              </div>
            </div>
          </div>
        </section>
        """,
        unsafe_allow_html=True,
    )

    _, content_col, _ = st.columns([1, 6, 1])
    with content_col:
        st.markdown(f"### Job Description\n{description}")
        if responsibilities:
            st.markdown("### Responsibilities")
            for r in responsibilities:
                st.markdown(f"- {r}")
        if requirements:
            st.markdown("### Requirements")
            for r in requirements:
                st.markdown(f"- {r}")
        if preferred:
            st.markdown("### Preferred Skills")
            for s in preferred:
                st.markdown(f"- {s}")
        if qualifications:
            st.markdown("### Qualifications")
            for q in qualifications:
                st.markdown(f"- {q}")
        if benefits:
            st.markdown("### What We Offer")
            for b in benefits:
                st.markdown(f"- {b}")
        if deadline:
            st.caption(f"Application Deadline: {deadline}")
        st.markdown("---")

        st.subheader("Apply for this Position")
        with st.form(key=f"application_form_{job_id}", clear_on_submit=False):
            st.markdown("**Personal Information**")
            c1, c2 = st.columns(2)
            with c1:
                full_name = st.text_input("Full Name *")
                email = st.text_input("Email Address *")
                phone = st.text_input("Phone Number")
            with c2:
                location = st.text_input("Current Location")
                linkedin = st.text_input("LinkedIn URL")
                portfolio = st.text_input("Portfolio URL")
            st.markdown("**Professional Information**")
            c3, c4 = st.columns(2)
            with c3:
                current_title = st.text_input("Current Job Title")
                years_experience = st.number_input("Years of Experience", min_value=0, step=1)
            with c4:
                current_company = st.text_input("Current Company")
                github = st.text_input("GitHub URL")
            st.markdown("**Application Information**")
            cover_letter = st.text_area("Cover Letter (optional)", height=100)
            st.markdown("**Resume**")
            resume_file = st.file_uploader(
                "Upload Resume *",
                type=["pdf", "docx"],
                accept_multiple_files=False,
            )
            consent = st.checkbox("I consent to the processing of my application data.")
            submitted = st.form_submit_button("Submit Application", type="primary", use_container_width=True)
            if submitted:
                if not full_name or not email:
                    st.error("Please fill in Full Name and Email Address.")
                elif not resume_file:
                    st.error("Please upload a resume.")
                elif not consent:
                    st.error("Please accept the consent checkbox.")
                else:
                    try:
                        file_bytes = resume_file.getvalue()
                        result = submit_public_application(
                            job_id=job_id,
                            payload={
                                "full_name": full_name, "email": email, "phone": phone,
                                "location": location, "linkedin": linkedin, "portfolio": portfolio,
                                "current_title": current_title, "years_experience": years_experience,
                                "current_company": current_company, "github": github,
                                "skills": [], "cover_letter": cover_letter,
                            },
                            file_bytes=file_bytes,
                            filename=resume_file.name,
                            mime_type=resume_file.type or "application/octet-stream",
                        )
                        if result:
                            st.success(result.get("message") or "Application submitted successfully.")
                            st.session_state.selected_public_job = None
                            st.session_state.public_page = "Careers"
                            st.rerun()
                        else:
                            st.error("Failed to submit application. Please try again later.")
                    except Exception as exc:
                        st.error(f"An error occurred: {exc}")

        if st.button("← Back to Careers", use_container_width=False):
            st.session_state.selected_public_job = None
            st.session_state.public_page = "Careers"
            st.rerun()
    # _render_public_footer()