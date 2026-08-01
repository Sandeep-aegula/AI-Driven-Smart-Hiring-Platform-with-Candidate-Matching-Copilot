import streamlit as st
from frontend.public.utils import inject_public_css
from frontend.public.components.public_navbar import render_public_navbar
from frontend.public.components.public_footer import render_public_footer
from frontend.components.api_client import get_public_job_details, submit_public_application

def render_page():
    """Render the Job Application page for the public website."""
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

    st.markdown(
        f"""
        <section class="hp-section" style="padding: 4rem 1rem 2rem 1rem; text-align: center; background: linear-gradient(135deg, #F8FAFC 0%, #E2E8F0 100%);">
          <div class="hp-container">
            <h1 style="font-size: 2.5rem; color: #0F172A; margin-bottom: 0.5rem;">Apply for {job['title']}</h1>
            <p style="font-size: 1.125rem; color: #475569;">
              {job['department']} &middot; {job['location']}
            </p>
          </div>
        </section>
        """,
        unsafe_allow_html=True,
    )
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        if st.session_state.get("application_submitted"):
            st.success("Your application has been submitted successfully! Our team will review it and get back to you soon.")
            if st.button("Return to Careers", type="primary", width="stretch"):
                st.session_state.application_submitted = False
                st.session_state.public_page = "careers"
                st.query_params["public_page"] = "careers"
                st.rerun()
        else:
            with st.form("job_application_form"):
                st.markdown("<h3 style='color: #0F172A; margin-bottom: 1rem;'>Personal Information</h3>", unsafe_allow_html=True)
                full_name = st.text_input("Full Name *")
                email = st.text_input("Email Address *")
                phone = st.text_input("Phone Number *")
                location = st.text_input("Current Location *")
                
                st.markdown("<h3 style='color: #0F172A; margin-bottom: 1rem; margin-top: 2rem;'>Professional Information</h3>", unsafe_allow_html=True)
                current_title = st.text_input("Current Job Title")
                experience = st.number_input("Total Years of Experience", min_value=0, max_value=50, value=0)
                skills = st.text_input("Key Skills (comma separated)")
                linkedin = st.text_input("LinkedIn Profile URL")
                github = st.text_input("GitHub Profile URL")
                portfolio = st.text_input("Portfolio or Personal Website URL")
                st.markdown("<h3 style='color: #0F172A; margin-bottom: 1rem; margin-top: 2rem;'>Resume</h3>", unsafe_allow_html=True)
                resume = st.file_uploader("Resume Upload *", type=["pdf", "doc", "docx"])
                
                st.markdown("<h3 style='color: #0F172A; margin-bottom: 1rem; margin-top: 2rem;'>Additional Information</h3>", unsafe_allow_html=True)
                cover_letter = st.text_area("Cover Letter (Optional)")
                
                st.markdown("<br>", unsafe_allow_html=True)
                submitted = st.form_submit_button("Submit Application", type="primary", width="stretch")
                
                if submitted:
                    phone_value = phone.strip() if phone else ""
                    if not full_name or not email or not phone_value or not location or not resume:
                        st.error("Please fill in all required fields and upload a resume.")
                    elif "@" not in email:
                        st.error("Please provide a valid email address.")
                    elif not phone_value:
                        st.error("Please enter your phone number.")
                    else:
                        with st.spinner("Submitting your application..."):
                            payload = {
                                "full_name": full_name,
                                "email": email,
                                "phone": phone_value,
                                "current_title": current_title,
                                "years_experience": int(experience),
                                "skills": skills,
                                "linkedin": linkedin,
                                "github": github,
                                "portfolio": portfolio,
                                "cover_letter": cover_letter,
                            }
                            res = submit_public_application(
                                job_id,
                                payload,
                                resume.getvalue(),
                                resume.name,
                                filename=resume.name,
                                mime_type=resume.type or "application/octet-stream",
                            )
                            if res and not res.get("error"):
                                st.session_state.application_submitted = True
                                st.rerun()
                            elif res and res.get("error"):
                                st.error(f"Application failed: {res['error']}")
                            else:
                                st.error("Failed to submit application. Please try again.")
                        
            if st.button("Cancel", width="stretch"):
                st.session_state.public_page = "job_details"
                st.query_params["public_page"] = "job_details"
                st.rerun()

    st.markdown("<br><br>", unsafe_allow_html=True)
    render_public_footer()
