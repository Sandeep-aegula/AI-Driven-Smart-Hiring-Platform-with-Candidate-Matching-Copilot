"""
frontend/public/home.py
Public landing page for HirePilot.
Rendered when no user token is present (before login).
"""

import streamlit as st
from frontend.components.api_client import get_public_jobs
from frontend.public.components.public_navbar import render_public_navbar
from frontend.public.components.public_footer import render_public_footer


def render_page():
    """Render the full public landing page."""

    # Inject public portal CSS
    css_path = _get_public_css_path()
    if css_path:
        with open(css_path, "r", encoding="utf-8") as f:
            css = f.read()
        st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)

    # Track which public nav item is active
    if "public_nav" not in st.session_state:
        st.session_state.public_nav = "home"

    # Handle "go to login" action from query params
    query = st.query_params
    if query.get("page") == "login":
        st.session_state.show_login = True
        st.session_state.public_nav = "home"
        st.query_params.clear()
        st.rerun()

    # If login was requested, show login screen
    if st.session_state.get("show_login", False):
        _render_login_screen()
        return

    # Render public content sections (navbar and footer are handled elsewhere)
    render_public_navbar(active_page="home")
    _render_hero()
    _render_stats()
    _render_about()
    _render_features()
    _render_workflow()
    _render_featured_jobs()
    _render_for_candidates()
    _render_for_companies()
    _render_contact()
    render_public_footer()


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _get_public_css_path():
    """Return absolute path to the public portal CSS file."""
    import os
    current_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(current_dir, "styles", "public_portal.css")


# ---------------------------------------------------------------------------
# Section renderers
# ---------------------------------------------------------------------------

def _render_hero():

    st.markdown(
        """
            </div>
            <div class="hp-navbar-actions" id="hp-navbar-actions">
        """,
        unsafe_allow_html=True,
    )

    # Sign In button shows placeholder (authentication not yet implemented)
    if st.button("Sign In", key="public_signin_btn", type="primary"):
        st.info("HR portal authentication will be available soon. Please use the recruiter login when launched.")

    st.markdown("</div></div></nav>", unsafe_allow_html=True)

    # Mobile actions (hidden on desktop via CSS, shown on mobile)
    st.markdown(
        """
        <div class="hp-navbar-actions" id="hp-mobile-actions" style="display:none;">
          <button class="hp-btn hp-btn-primary hp-btn-sm" onclick="
            const ev = new Event('click');
            document.getElementById('public_signin_btn').dispatchEvent(ev);
          ">Sign In</button>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _render_login_screen():
    """Render the HR portal login screen (moved from app.py)."""
    st.markdown("<br><br><br>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns([1, 2, 1])
    with c2:
        st.markdown(
            "<h2 style='text-align: center; color: #0F172A;'>HIREPILOT HR Login</h2>",
            unsafe_allow_html=True,
        )
        with st.form("login_form"):
            email = st.text_input("Email", placeholder="admin@hirepilot.com")
            password = st.text_input("Password", type="password", placeholder="password123")
            submit = st.form_submit_button("Log In", width="stretch")
            if submit:
                from frontend.components.api_client import login_user
                token = login_user(email, password)
                if token:
                    st.session_state.token = token
                    st.session_state.show_login = False
                    st.rerun()
                else:
                    st.error("Invalid email or password.")

        if st.button("Back to Home", key="back_to_home"):
            st.session_state.show_login = False
            st.rerun()


# ---------------------------------------------------------------------------
# Section renderers
# ---------------------------------------------------------------------------

def _render_hero():
    st.markdown(
        """
        <section class="hp-hero" id="home">
          <div class="hp-container">
            <div class="hp-hero-grid">
              <div>
                <div class="hp-hero-badge">AI Recruitment Platform</div>
                <h1>Transform Recruitment with <span class="highlight">Intelligent AI</span></h1>
                <p>HirePilot helps organizations streamline recruitment, intelligently evaluate candidates, manage interviews, and make better hiring decisions through AI-powered automation.</p>
                <div class="hp-hero-actions">
                  <a href="#careers" class="hp-btn hp-btn-primary hp-btn-lg">Explore Careers</a>
                  <a href="#companies" class="hp-btn hp-btn-secondary hp-btn-lg">For Companies</a>
                </div>
              </div>
              <div class="hp-hero-visual">
                <div class="hp-hero-card">
                  <div class="stat-row">
                    <div class="stat-item">
                      <div class="stat-value">AI</div>
                      <div class="stat-label">Recruitment</div>
                    </div>
                    <div class="stat-item">
                      <div class="stat-value">ATS</div>
                      <div class="stat-label">Job Matching</div>
                    </div>
                    <div class="stat-item">
                      <div class="stat-value">HR</div>
                      <div class="stat-label">Analytics</div>
                    </div>
                  </div>
                  <p style="font-size:0.9rem; color:#64748B; text-align:center; margin-top:1rem;">
                    Intelligent hiring workflow powered by artificial intelligence.
                  </p>
                </div>
              </div>
            </div>
          </div>
        </section>
        """,
        unsafe_allow_html=True,
    )


def _render_stats():
    st.markdown(
        """
        <section class="hp-stats">
          <div class="hp-container">
            <div class="hp-stats-grid">
              <div class="hp-stat-item">
                <div class="stat-number">50%+</div>
                <div class="stat-label">Faster Candidate Screening</div>
              </div>
              <div class="hp-stat-item">
                <div class="stat-number">AI-Powered</div>
                <div class="stat-label">Candidate Evaluation</div>
              </div>
              <div class="hp-stat-item">
                <div class="stat-number">Centralized</div>
                <div class="stat-label">Centralized Recruitment Management</div>
              </div>
              <div class="hp-stat-item">
                <div class="stat-number">Secure</div>
                <div class="stat-label">HR Data Management</div>
              </div>
            </div>
          </div>
        </section>
        """,
        unsafe_allow_html=True,
    )


def _render_about():
    st.markdown(
        """
        <section class="hp-section" id="about">
          <div class="hp-container">
            <div class="hp-about-grid">
              <div class="hp-about-content">
                <div class="hp-section-tag">About HIREPILOT</div>
                <h2>Recruitment, Reimagined with AI</h2>
                <p>HirePilot is an AI-powered Recruitment and Talent Management platform designed to simplify the complete hiring lifecycle. From job creation and candidate applications to resume analysis, AI screening, interviews, onboarding, and employee management, HirePilot brings recruitment workflows into one intelligent system.</p>
                <a href="#features" class="hp-btn hp-btn-primary">Learn More</a>
              </div>
              <div class="hp-about-image">
                <svg width="120" height="120" viewBox="0 0 120 120" fill="none" xmlns="http://www.w3.org/2000/svg">
                  <rect x="10" y="20" width="100" height="80" rx="8" stroke="#1E40AF" stroke-width="4"/>
                  <circle cx="60" cy="55" r="15" stroke="#1E40AF" stroke-width="4"/>
                  <path d="M40 85 Q60 70 80 85" stroke="#1E40AF" stroke-width="4" fill="none"/>
                  <rect x="25" y="95" width="20" height="6" rx="3" fill="#1E40AF" opacity="0.3"/>
                  <rect x="75" y="95" width="20" height="6" rx="3" fill="#1E40AF" opacity="0.3"/>
                </svg>
              </div>
            </div>
          </div>
        </section>
        """,
        unsafe_allow_html=True,
    )


def _render_features():
    st.markdown(
        """
        <section class="hp-section hp-section-alt" id="features">
          <div class="hp-container">
            <div class="hp-section-header">
              <div class="hp-section-tag">Features</div>
              <h2>Everything You Need to Manage Hiring</h2>
              <p>Eight powerful modules working together to transform your recruitment process from start to finish.</p>
            </div>
            <div class="hp-features-grid">
        """,
        unsafe_allow_html=True,
    )

    features = [
        ("fa-briefcase", "Intelligent Job Management", "Create, manage, publish, pause, and close job openings."),
        ("fa-file-lines", "AI Resume Analysis", "Extract candidate information, skills, education, experience, and projects from uploaded resumes."),
        ("fa-bullseye", "ATS Scoring and Job Matching", "Compare candidate profiles with job requirements and generate intelligent suitability scores."),
        ("fa-list-check", "Smart Candidate Screening", "Rank candidates and provide AI-generated recommendations to support recruiter decisions."),
        ("fa-calendar-check", "Interview Management", "Manage multiple interview rounds, schedules, interviewers, and recruiter decisions."),
        ("fa-envelope", "AI-Powered Communication", "Generate professional recruitment emails and communicate with multiple candidates."),
        ("fa-id-card", "Digital Onboarding", "Manage document verification and onboarding progress for selected candidates."),
        ("fa-users", "Employee Talent Management", "Manage employee skills, projects, performance, and AI-generated insights."),
    ]

    for icon, title, desc in features:
        st.markdown(
            f"""
            <div class="hp-feature-card">
              <div class="hp-feature-icon"><i class="fa-solid {icon}"></i></div>
              <h4>{title}</h4>
              <p>{desc}</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("</div></div></section>", unsafe_allow_html=True)


def _render_workflow():
    st.markdown(
        """
        <section class="hp-section" id="how-it-works">
          <div class="hp-container">
            <div class="hp-section-header">
              <div class="hp-section-tag">How It Works</div>
              <h2>A Smarter Hiring Journey</h2>
              <p>From job posting to new hire onboarding, HirePilot simplifies every step.</p>
            </div>
            <div class="hp-workflow">
        """,
        unsafe_allow_html=True,
    )

    steps = [
        ("1", "HR Creates and Publishes a Job", "HR creates and publishes a job."),
        ("2", "Candidates Discover Jobs and Apply", "Candidates discover jobs and apply."),
        ("3", "Resumes Are Processed", "Resumes are processed."),
        ("4", "AI Parses Candidate Information", "AI parses candidate information."),
        ("5", "ATS Scoring and Job Matching", "ATS scoring and job matching."),
        ("6", "Recruiter Reviews Candidates", "Recruiter reviews candidates."),
        ("7", "Shortlisted Candidates Attend Interviews", "Shortlisted candidates attend interviews."),
        ("8", "Selected Candidates Complete Onboarding", "Selected candidates complete onboarding."),
        ("9", "Employee Profiles Are Created", "Employee profiles are created."),
    ]

    for num, title, desc in steps:
        st.markdown(
            f"""
            <div class="hp-workflow-step">
              <div class="hp-workflow-number">{num}</div>
              <h4>{title}</h4>
              <p>{desc}</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("</div></div></section>", unsafe_allow_html=True)


def _render_featured_jobs():
    """Render the Featured Job Openings section with live jobs from the API."""
    st.markdown(
        """
        <section class="hp-section hp-section-alt" id="featured-jobs">
          <div class="hp-container">
            <div class="hp-section-header">
              <div class="hp-section-tag">Featured Opportunities</div>
              <h2>Featured Job Openings</h2>
              <p>Explore our latest openings and find your next career move.</p>
            </div>
            <div class="hp-jobs-grid" id="featured-jobs-grid">
        """,
        unsafe_allow_html=True,
    )

    # Fetch live jobs from the API
    with st.spinner("Loading featured jobs..."):
        jobs = get_public_jobs()

    if jobs:
        # Display up to 4 featured jobs
        featured_jobs = jobs[:4]
        for job in featured_jobs:
            st.markdown(
                f"""
                <div class="hp-job-card">
                  <div class="hp-job-header">
                    <h3>{job.get('title', 'N/A')}</h3>
                    <span class="hp-job-badge">{job.get('employment_type', 'Full-time')}</span>
                  </div>
                  <div class="hp-job-meta">
                    <div class="hp-job-meta-item">
                      <span class="hp-job-meta-icon">🏢</span>
                      <span>{job.get('department', 'N/A')}</span>
                    </div>
                    <div class="hp-job-meta-item">
                      <span class="hp-job-meta-icon">📍</span>
                      <span>{job.get('location', 'N/A')}</span>
                    </div>
                    <div class="hp-job-meta-item">
                      <span class="hp-job-meta-icon">💼</span>
                      <span>{job.get('experience_required', 'N/A')}</span>
                    </div>
                  </div>
                  <div class="hp-job-description">
                    <p>{job.get('description', 'No description available')[:200]}...</p>
                  </div>
                  <div class="hp-job-footer">
                    <a href="#careers" class="hp-btn hp-btn-primary hp-btn-sm" onclick="window.location.href='#careers'">View Job</a>
                  </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
    else:
        st.markdown(
            """
            <div class="hp-no-jobs">
              <p>No featured jobs available at the moment. Please check back later!</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown(
        """
              </div>
              <div class="hp-jobs-cta">
                <a href="#careers" class="hp-btn hp-btn-secondary hp-btn-lg">View All Open Positions</a>
              </div>
            </div>
          </div>
        </section>
        """,
        unsafe_allow_html=True,
    )


def _render_for_candidates():
    st.markdown(
        """
        <section class="hp-section hp-section-alt" id="careers">
          <div class="hp-container">
            <div class="hp-split">
              <div class="hp-split-visual">
                <svg width="120" height="120" viewBox="0 0 120 120" fill="none" xmlns="http://www.w3.org/2000/svg">
                  <rect x="20" y="25" width="80" height="70" rx="8" stroke="#1E40AF" stroke-width="4"/>
                  <circle cx="45" cy="50" r="8" fill="#1E40AF" opacity="0.3"/>
                  <path d="M30 70 Q45 55 60 70 Q75 55 90 70" stroke="#1E40AF" stroke-width="4" fill="none"/>
                  <rect x="35" y="85" width="50" height="6" rx="3" fill="#1E40AF" opacity="0.3"/>
                </svg>
              </div>
              <div class="hp-split-content">
                <div class="hp-section-tag">For Candidates</div>
                <h2>Find Your Next Opportunity</h2>
                <p>Explore available opportunities, discover roles that match your skills, and apply through a simple and organized application process.</p>
                <ul class="hp-split-list">
                  <li>AI-powered resume analysis and skill matching</li>
                  <li>Personalized job recommendations based on your profile</li>
                  <li>Transparent application tracking and status updates</li>
                  <li>Interview preparation insights and feedback</li>
                </ul>
                <a href="#careers" class="hp-btn hp-btn-primary">Browse Open Positions</a>
              </div>
            </div>
          </div>
        </section>
        """,
        unsafe_allow_html=True,
    )


def _render_for_companies():
    st.markdown(
        """
        <section class="hp-section" id="companies">
          <div class="hp-container">
            <div class="hp-split">
              <div class="hp-split-content">
                <div class="hp-section-tag">For Companies</div>
                <h2>Build Better Teams with HirePilot</h2>
                <p>Manage jobs, candidates, interviews, communication, onboarding, employees, analytics, and AI-powered insights from one centralized platform.</p>
                <ul class="hp-split-list">
                  <li>Reduce time-to-hire with AI-driven candidate ranking</li>
                  <li>Centralized interview and offer management</li>
                  <li>Seamless onboarding and employee lifecycle tracking</li>
                  <li>AI-powered recruitment analytics and insights</li>
                </ul>
                <a href="?public_page=hr_login" class="hp-btn hp-btn-primary">Access Recruiter Portal</a>
              </div>
              <div class="hp-split-visual">
                <svg width="120" height="120" viewBox="0 0 120 120" fill="none" xmlns="http://www.w3.org/2000/svg">
                  <rect x="15" y="30" width="90" height="60" rx="8" stroke="#1E40AF" stroke-width="4"/>
                  <rect x="25" y="40" width="25" height="18" rx="4" fill="#1E40AF" opacity="0.2"/>
                  <rect x="55" y="40" width="25" height="18" rx="4" fill="#1E40AF" opacity="0.2"/>
                  <rect x="25" y="65" width="55" height="6" rx="3" fill="#1E40AF" opacity="0.3"/>
                  <rect x="25" y="78" width="40" height="6" rx="3" fill="#1E40AF" opacity="0.2"/>
                </svg>
              </div>
            </div>
          </div>
        </section>
        """,
        unsafe_allow_html=True,
    )


def _render_contact():
    st.markdown(
        """
        <section class="hp-section hp-section-alt" id="contact">
          <div class="hp-container">
            <div class="hp-section-header">
              <div class="hp-section-tag">Contact</div>
              <h2>Get in Touch</h2>
              <p>Learn how HirePilot can help your organization improve recruitment workflows and make informed hiring decisions.</p>
            </div>
            <div class="hp-contact-grid">
              <div class="hp-contact-info">
                <h2>Let's Start a Conversation</h2>
                <p>Fill out the form and we'll schedule a personalized demo tailored to your hiring needs.</p>
                <div class="hp-contact-detail">
                  <div class="icon">📍</div>
                  <span>123 Innovation Drive, Tech Park, Bangalore, India</span>
                </div>
                <div class="hp-contact-detail">
                  <div class="icon">📧</div>
                  <span>hello@hirepilot.ai</span>
                </div>
                <div class="hp-contact-detail">
                  <div class="icon">📞</div>
                  <span>+91 98765 43210</span>
                </div>
              </div>
              <div class="hp-contact-form">
        """,
        unsafe_allow_html=True,
    )

    with st.form("contact_form"):
        name = st.text_input("Full Name", placeholder="Your full name")
        email = st.text_input("Email Address", placeholder="you@company.com")
        company = st.text_input("Company", placeholder="Your company name")
        message = st.text_area("Message", placeholder="Tell us about your hiring needs...")
        submitted = st.form_submit_button("Send Message", width="stretch", type="primary")
        if submitted:
            st.success("Thank you for reaching out! We will get back to you soon.")

    st.markdown("</div></div></section>", unsafe_allow_html=True)


def _render_footer():
    st.markdown(
        """
        <footer class="hp-footer">
          <div class="hp-container">
            <div class="hp-footer-grid">
              <div class="hp-footer-brand">
                <h3>HIREPILOT</h3>
                <p>AI Recruitment and Talent Management Platform</p>
              </div>
              <div class="hp-footer-col">
                <h4>Navigation</h4>
                <ul>
                  <li><a href="#home">Home</a></li>
                  <li><a href="#about">About Us</a></li>
                  <li><a href="#careers">Careers</a></li>
                  <li><a href="#how-it-works">How It Works</a></li>
                  <li><a href="#contact">Contact</a></li>
                </ul>
              </div>
              <div class="hp-footer-col">
                <h4>For Candidates</h4>
                <ul>
                  <li><a href="#careers">Browse Jobs</a></li>
                  <li><a href="#features">Platform Features</a></li>
                  <li><a href="#contact">Support</a></li>
                </ul>
              </div>
              <div class="hp-footer-col">
                <h4>For Companies</h4>
                <ul>
                  <li><a href="?page=login">Recruiter Portal</a></li>
                  <li><a href="#how-it-works">How It Works</a></li>
                  <li><a href="?page=login">Request Demo</a></li>
                </ul>
              </div>
            </div>
            <div class="hp-footer-bottom">
              <span>&copy; 2026 HIREPILOT. All rights reserved.</span>
              <div class="hp-footer-bottom-links">
                <a href="?page=login">Sign In</a>
              </div>
            </div>
          </div>
        </footer>
        """,
        unsafe_allow_html=True,
    )
