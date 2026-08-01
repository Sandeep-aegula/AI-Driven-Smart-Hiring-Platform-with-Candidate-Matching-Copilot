"""
app.py — HirePilot Application Entry Point
==========================================

Application flow:

1. Public Company Website
   - Home
   - Careers
   - About Us
   - Contact
   - HR Sign In

2. HR / Recruiter Portal
   - Dashboard
   - Jobs
   - Candidates
   - Resume Parser
   - AI Screening
   - Interviews
   - Employees
   - Communications
   - Analytics
   - Reports
   - AI Copilot

Important rules:
- st.set_page_config() is called only once.
- Navigation uses st.session_state.
- Do not use st.switch_page().
- Public pages do not display the HR sidebar.
- HR portal pages display the existing sidebar and header.
- Backend and Ollama are started separately.
"""

import os
import sys
import streamlit as st

ROOT = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(ROOT)

if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)


# ============================================================
# STREAMLIT CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="HirePilot | AI Recruitment Platform",
    page_icon="H",
    layout="wide",
    initial_sidebar_state="collapsed",
)


# ============================================================
# IMPORT EXISTING APPLICATION SERVICES
# ============================================================

from frontend.services.app_state import AppState
from frontend.services.cache import inject_css_once
from frontend.components.api_client import (
    get_public_jobs,
    get_public_job_details,
    submit_public_application,
)


# ============================================================
# SESSION STATE INITIALIZATION
# ============================================================

def initialize_application_state():
    """
    Initialize the application navigation state.

    The public company website is the first page shown when
    the application opens.
    """

    if "app_mode" not in st.session_state:
        st.session_state.app_mode = "public"

    if "public_page" not in st.session_state:
        st.session_state.public_page = "Home"

    if "current_page" not in st.session_state:
        st.session_state.current_page = "Dashboard"

    if "is_authenticated" not in st.session_state:
        st.session_state.is_authenticated = False

    if "search_query" not in st.session_state:
        st.session_state.search_query = ""

    if "selected_public_job" not in st.session_state:
        st.session_state.selected_public_job = None


# ============================================================
# NAVIGATION FUNCTIONS
# ============================================================

def open_public_page(page_name: str):
    """
    Open a page in the public company website.
    """

    st.session_state.app_mode = "public"
    st.session_state.public_page = page_name
    st.rerun()


def open_hr_login():
    """
    Open the HR login interface.
    """

    st.session_state.app_mode = "hr_login"
    st.rerun()


def open_hr_portal():
    """
    Open the HR / Recruiter portal.

    Authentication will be connected here later.
    """

    st.session_state.app_mode = "hr_portal"
    st.session_state.current_page = "Dashboard"
    st.rerun()


def return_to_company_website():
    """
    Return from the HR portal to the public company website.
    """

    st.session_state.app_mode = "public"
    st.session_state.public_page = "Home"
    st.rerun()


# ============================================================
# PUBLIC COMPANY WEBSITE
# ============================================================

def render_company_website():
    """
    Render the public HirePilot company website.

    This is separate from the HR portal.
    The HR sidebar and HR dashboard are not shown here.
    """

    public_page = st.session_state.get("public_page", "Home")

    # --------------------------------------------------------
    # Try to load the dedicated company website component.
    # --------------------------------------------------------

    try:
        from frontend.components.company_website import (
            render_company_website as render_company_page
        )

        render_company_page()
        return

    except ImportError:
        pass

    # --------------------------------------------------------
    # Public navigation
    # --------------------------------------------------------

    nav_col_1, nav_col_2, nav_col_3, nav_col_4, nav_col_5, nav_col_6 = (
        st.columns([2.5, 1, 1, 1, 1, 1.2])
    )

    with nav_col_1:
        st.markdown(
            "<div class='hirepilot-logo'>HIREPILOT</div>",
            unsafe_allow_html=True,
        )

    with nav_col_2:
        if st.button(
            "Home",
            key="public_home_button",
            width="stretch",
        ):
            open_public_page("Home")

    with nav_col_3:
        if st.button(
            "Careers",
            key="public_careers_button",
            width="stretch",
        ):
            open_public_page("Careers")

    with nav_col_4:
        if st.button(
            "About Us",
            key="public_about_button",
            width="stretch",
        ):
            open_public_page("About Us")

    with nav_col_5:
        if st.button(
            "Contact",
            key="public_contact_button",
            width="stretch",
        ):
            open_public_page("Contact")

    with nav_col_6:
        if st.button(
            "HR Sign In",
            key="public_hr_login_button",
            type="primary",
            width="stretch",
        ):
            open_hr_login()

    # --------------------------------------------------------
    # Home page
    # --------------------------------------------------------

    if public_page == "Home":

        st.markdown(
            """
            <div class="public-title">
                Build Your Career With Us
            </div>

            <div class="public-subtitle">
                Explore exciting career opportunities and join a team
                that builds innovative, scalable, and intelligent
                technology solutions.
            </div>
            """,
            unsafe_allow_html=True,
        )

        search_col, button_col = st.columns([5, 1])

        with search_col:
            st.text_input(
                "Search jobs",
                placeholder="Search jobs, skills, or keywords...",
                label_visibility="collapsed",
                key="public_job_search",
            )

        with button_col:
            if st.button(
                "Search",
                key="public_search_button",
                type="primary",
                width="stretch",
            ):
                open_public_page("Careers")

        st.markdown("<br>", unsafe_allow_html=True)

        st.subheader("Why Join HirePilot?")

        feature_1, feature_2, feature_3 = st.columns(3)

        with feature_1:
            st.info(
                """
                **Innovative Work**

                Build AI-powered solutions that improve
                recruitment and talent management.
                """
            )

        with feature_2:
            st.info(
                """
                **Career Growth**

                Develop your technical and professional
                skills through meaningful projects.
                """
            )

        with feature_3:
            st.info(
                """
                **Collaborative Culture**

                Work with talented teams in an inclusive
                and supportive environment.
                """
            )

    # --------------------------------------------------------
    # Careers page
    # --------------------------------------------------------

    elif public_page == "Careers":
        st.title("Explore Career Opportunities")
        st.write(
            "Find a role that matches your skills, experience, "
            "and career goals."
        )

        # Filters
        filter_1, filter_2, filter_3 = st.columns(3)
        with filter_1:
            department = st.selectbox(
                "Department",
                [
                    "All Departments",
                    "Engineering",
                    "Technology",
                    "Human Resources",
                    "Operations",
                ],
                key="career_department",
            )
        with filter_2:
            location = st.selectbox(
                "Location",
                [
                    "All Locations",
                    "Hyderabad",
                    "Bengaluru",
                    "Chennai",
                    "Remote",
                ],
                key="career_location",
            )
        with filter_3:
            employment_type = st.selectbox(
                "Employment Type",
                [
                    "All Types",
                    "Full-Time",
                    "Part-Time",
                    "Internship",
                ],
                key="career_employment_type",
            )

        # Convert filter values for API
        dept_api = "All" if department == "All Departments" else department
        loc_api = "All" if location == "All Locations" else location
        emp_type_api = "All" if employment_type == "All Types" else employment_type

        # Fetch jobs from API
        with st.spinner("Loading job listings..."):
            jobs = get_public_jobs(
                search="",
                department=dept_api,
                location=loc_api,
                employment_type=emp_type_api,
            )

        if not jobs:
            st.info("No job openings found.")
        else:
            for job in jobs:
                # Create a card for each job
                col1, col2 = st.columns([5, 1])
                with col1:
                    st.subheader(job["title"])
                    st.write(
                        f"{job['department']} | {job['location']} | {job['employment_type']}"
                    )
                    if job.get("experience_required"):
                        st.caption(f"Experience: {job['experience_required']}")
                    if job.get("short_description"):
                        st.caption(job["short_description"])
                with col2:
                    if st.button(
                        "View Job",
                        key=f"view_job_{job['id']}",
                        width="stretch",
                    ):
                        st.session_state.selected_public_job = job["id"]
                        st.session_state.public_page = "JobDetail"
                        st.rerun()
                st.markdown("---")

    # --------------------------------------------------------
    # Job Detail page
    # --------------------------------------------------------

    elif public_page == "JobDetail":
        job_id = st.session_state.get("selected_public_job")
        if not job_id:
            st.error("No job selected.")
            if st.button("Back to Careers"):
                st.session_state.public_page = "Careers"
                st.rerun()
        else:
            job = get_public_job_details(job_id)
            if not job:
                st.error("Job not found or not available.")
                if st.button("Back to Careers"):
                    st.session_state.public_page = "Careers"
                    st.rerun()
            else:
                # Display job details
                st.title(job["title"])
                st.write(
                    f"{job['department']} | {job['location']} | {job['employment_type']} | {job.get('work_mode', 'Remote')}"
                )
                if job.get("experience_required"):
                    st.write(f"Experience: {job['experience_required']}")
                if job.get("openings"):
                    st.write(f"Openings: {job['openings']}")
                if job.get("deadline"):
                    st.write(f"Application Deadline: {job['deadline']}")
                st.write("---")
                st.subheader("Job Description")
                st.write(job["description"])
                st.subheader("Responsibilities")
                for resp in job["responsibilities"]:
                    st.write(f"- {resp}")
                st.subheader("Requirements")
                for req in job["requirements"]:
                    st.write(f"- {req}")
                if job.get("preferred_skills"):
                    st.subheader("Preferred Skills")
                    for skill in job["preferred_skills"]:
                        st.write(f"- {skill}")
                if job.get("qualifications"):
                    st.subheader("Qualifications")
                    for qual in job["qualifications"]:
                        st.write(f"- {qual}")
                if job.get("benefits"):
                    st.subheader("Benefits")
                    for benefit in job["benefits"]:
                        st.write(f"- {benefit}")
                st.write("---")
                st.subheader("Apply for this Position")
                # Application form
                with st.form(key=f"application_form_{job_id}"):
                    # Personal information
                    st.write("Personal Information")
                    col1, col2 = st.columns(2)
                    with col1:
                        full_name = st.text_input("Full Name *")
                        email = st.text_input("Email Address *")
                        phone = st.text_input("Phone Number")
                    with col2:
                        location = st.text_input("Current Location")
                        linkedin = st.text_input("LinkedIn URL (optional)")
                        portfolio = st.text_input("Portfolio URL (optional)")
                    # Professional information
                    st.write("Professional Information")
                    col3, col4 = st.columns(2)
                    with col3:
                        current_title = st.text_input("Current Job Title")
                        years_experience = st.number_input(
                            "Years of Experience", min_value=0, step=1
                        )
                    with col4:
                        current_company = st.text_input("Current Company")
                        github = st.text_input("GitHub URL (optional)")
                    # Application information
                    st.write("Application Information")
                    cover_letter = st.text_area("Cover Letter (optional)", height=100)
                    # Resume upload
                    st.write("Resume Upload")
                    resume_file = st.file_uploader(
                        "Upload your resume (PDF or DOCX)", type=["pdf", "docx"]
                    )
                    # Consent
                    consent = st.checkbox(
                        "I consent to the processing of my application data."
                    )
                    # Submit button
                    submitted = st.form_submit_button("Submit Application")
                    if submitted:
                        # Validate
                        if not full_name or not email:
                            st.error("Please fill in all required fields (Full Name, Email).")
                        elif not resume_file:
                            st.error("Please upload a resume.")
                        elif not consent:
                            st.error("Please consent to the processing of your application data.")
                        else:
                            # Call the API to submit the application
                            try:
                                # Read the file
                                file_bytes = resume_file.getvalue()
                                result = submit_public_application(
                                    job_id=job_id,
                                    payload={
                                        "full_name": full_name,
                                        "email": email,
                                        "phone": phone,
                                        "location": location,
                                        "linkedin": linkedin,
                                        "portfolio": portfolio,
                                        "current_title": current_title,
                                        "years_experience": years_experience,
                                        "current_company": current_company,
                                        "github": github,
                                        "skills": [],
                                        "cover_letter": cover_letter,
                                    },
                                    file_bytes=file_bytes,
                                    filename=resume_file.name,
                                    mime_type=resume_file.type or "application/octet-stream",
                                )
                                if result:
                                    st.success(result.get("message", "Application submitted successfully!"))
                                    # Clear the selected job and go back to careers or show a success message?
                                    # We'll reset the selected job and go to careers.
                                    st.session_state.selected_public_job = None
                                    st.session_state.public_page = "Careers"
                                    st.rerun()
                                else:
                                    st.error("Failed to submit application.")
                            except Exception as e:
                                st.error(f"An error occurred: {str(e)}")
                # Back to careers button outside the form
                if st.button("Back to Careers"):
                    st.session_state.selected_public_job = None
                    st.session_state.public_page = "Careers"
                    st.rerun()

    # --------------------------------------------------------
    # About Us page
    # --------------------------------------------------------

    elif public_page == "About Us":

        st.title("About HirePilot")

        st.write(
            """
            HirePilot is an AI-powered Recruitment and Talent
            Management platform designed to improve the complete
            hiring lifecycle.
            """
        )

        st.markdown(
            """
            ### Our Mission

            To help organizations reduce manual recruitment work,
            improve candidate evaluation, and make better
            data-driven hiring decisions.

            ### Our Platform

            HirePilot supports job management, resume parsing,
            ATS scoring, candidate screening, interview management,
            recruitment communication, employee management,
            analytics, reporting, and AI-powered assistance.
            """
        )

    # --------------------------------------------------------
    # Contact page
    # --------------------------------------------------------

    elif public_page == "Contact":

        st.title("Contact Us")

        st.write(
            "Send a message to the HirePilot team."
        )

        with st.form("contact_form"):

            st.text_input(
                "Full Name",
                key="contact_name",
            )

            st.email_input(
                "Email Address",
                key="contact_email",
            )

            st.text_area(
                "Message",
                key="contact_message",
                height=150,
            )

            submitted = st.form_submit_button(
                "Send Message",
                type="primary",
                width="stretch",
            )

            if submitted:
                st.success(
                    "Your message has been submitted."
                )


# ============================================================
# HR LOGIN PAGE
# ============================================================

def render_hr_login():
    """
    Render the temporary HR login page.

    MySQL authentication will replace the temporary login
    logic in the next implementation phase.
    """

    st.markdown(
        """
        <style>

        [data-testid="stSidebar"] {
            display: none;
        }

        .login-title {
            text-align: center;
            font-size: 38px;
            font-weight: 800;
            margin-top: 50px;
        }

        .login-description {
            text-align: center;
            color: #6b7280;
            margin-bottom: 30px;
        }

        </style>
        """,
        unsafe_allow_html=True,
    )

    top_left, top_center, top_right = st.columns(
        [1, 2, 1]
    )

    with top_left:
        if st.button(
            "Back to Website",
            key="login_back_button",
        ):
            return_to_company_website()

    with top_center:
        st.markdown(
            """
            <div class="login-title">
                HR / Recruiter Sign In
            </div>

            <div class="login-description">
                Access the HirePilot Recruitment and Talent
                Management Portal
            </div>
            """,
            unsafe_allow_html=True,
        )

    _, login_column, _ = st.columns([1, 1.2, 1])

    with login_column:

        with st.form("hr_login_form"):

            email = st.text_input(
                "HR Email Address",
                placeholder="hr@company.com",
                key="hr_login_email",
            )

            password = st.text_input(
                "Password",
                type="password",
                placeholder="Enter your password",
                key="hr_login_password",
            )

            login_submitted = st.form_submit_button(
                "Sign In",
                type="primary",
                width="stretch",
            )

            if login_submitted:

                if not email or not password:
                    st.error(
                        "Enter both your email address and password."
                    )

                else:
                    # ------------------------------------------------
                    # TEMPORARY LOGIN
                    #
                    # Replace this with MySQL authentication later.
                    # ------------------------------------------------

                    st.session_state.is_authenticated = True
                    st.session_state.hr_email = email

                    open_hr_portal()

        st.caption(
            "MySQL-based HR authentication will be connected "
            "in the next phase."
        )


# ============================================================
# HR / RECRUITER PORTAL
# ============================================================

def render_hr_portal():
    """
    Render the existing HirePilot HR portal.

    Existing components are kept unchanged.
    """

    # --------------------------------------------------------
    # Existing HR portal imports
    # --------------------------------------------------------

    from frontend.components.bar import render_sidebar
    from frontend.components.header import render_header
    from frontend.components.ai_assistant import (
        render_ai_assistant
    )

    # --------------------------------------------------------
    # Persistent HR portal UI
    # --------------------------------------------------------

    render_sidebar()

    render_header()

    render_ai_assistant()

    # --------------------------------------------------------
    # HR portal content routing
    # --------------------------------------------------------

    page = st.session_state.get(
        "current_page",
        "Dashboard",
    )

    if page == "Dashboard":

        from frontend.components.dashboard import (
            render_dashboard
        )

        render_dashboard()

    elif page == "Jobs":

        from frontend.components.jobs import (
            render_jobs
        )

        render_jobs()

    elif page == "Candidates":

        from frontend.components.candidates import (
            render_candidates
        )

        render_candidates()

    elif page == "Resume Parser":

        from frontend.components.resume_management import (
            render_resume_management
        )

        render_resume_management()

    elif page == "AI Screening":

        from frontend.components.ai_screening import (
            render_ai_screening
        )

        render_ai_screening()

    elif page == "Interviews":

        from frontend.components.interview_management import (
            render_interview_management
        )

        render_interview_management()

    elif page == "Employees":

        from frontend.components.employees import (
            render_employees
        )

        render_employees()

    elif page == "Communications":

        from frontend.components.communications import (
            render_communications
        )

        render_communications()

    elif page == "Onboarding":

        from frontend.components.onboarding import (
            render_onboarding
        )

        render_onboarding()

    elif page == "Analytics":

        from frontend.components.analytics import (
            render_analytics
        )

        render_analytics()

    elif page == "Reports":

        from frontend.components.reports import (
            render_reports
        )

        render_reports()

    elif page == "AI Copilot":

        from frontend.views.ai_copilot import (
            render_ai_copilot
        )

        render_ai_copilot()

    else:

        st.error(
            f"HR portal page '{page}' was not found."
        )


# ============================================================
# MAIN APPLICATION
# ============================================================

def main():
    """
    Main HirePilot application controller.
    """

    # Existing application state
    AppState.init()

    # New public / HR application state
    initialize_application_state()

    # Existing global CSS
    inject_css_once()

    # --------------------------------------------------------
    # Select application interface
    # --------------------------------------------------------

    app_mode = st.session_state.get(
        "app_mode",
        "public",
    )

    if app_mode == "public":

        render_company_website()

    elif app_mode == "hr_login":

        render_hr_login()

    elif app_mode == "hr_portal":

        render_hr_portal()

    else:

        st.session_state.app_mode = "public"

        st.session_state.public_page = "Home"

        st.rerun()


# ============================================================
# APPLICATION START
# ============================================================

if __name__ == "__main__":
    main()