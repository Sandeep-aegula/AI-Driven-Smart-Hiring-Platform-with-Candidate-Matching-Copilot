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

ROOT = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(ROOT)

if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

import streamlit as st
import textwrap
from components.public_careers import render_careers_page
from components.public_job_details import _render_job_detail_page
from components.public_about import render_about_page
from components.public_contact import _render_contact_page
from public.components.public_navbar import _render_public_navbar



def _flatten_html(html: str) -> str:
    """Strip leading whitespace from every line so Streamlit's markdown
    parser never mistakes indented HTML for a fenced code block."""
    return "\n".join(line.lstrip() for line in html.strip().splitlines())


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
from frontend.services.cache import inject_css_once, inject_public_css_once

from frontend.components.api_client import (
    get_public_jobs,
    get_public_job_details,
    submit_public_application,
)
from frontend.components.file_uploader import file_uploader_simple


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

PUBLIC_CONTENT = {
    "company_name": "HirePilot",
    "tagline": "AI Recruitment & Talent Management Platform",
    "hero": {
        "badge_text": "AI-Powered Recruitment",
        "badge_icon": "✨",
        "headline_prefix": "Hire Smarter. ",
        "headline_highlight": "Onboard Faster.",
        "headline_suffix": "Grow Together.",
        "subhead": (
            "HirePilot is the complete AI copilot for recruitment and talent teams — "
            "from job publishing and intelligent resume screening to interviews, "
            "onboarding, and employee performance insights."
        ),
        "primary_cta": "Browse Open Roles",
        "secondary_cta": "How It Works",
        "stat_cards": [
            {"value": "12K+", "label": "Resumes Parsed"},
            {"value": "95%", "label": "ATS Match Accuracy"},
            {"value": "4x", "label": "Faster Time-to-Hire"},
            {"value": "340+", "label": "Employees Hired"},
        ],
    },
    "about": {
        "tag": "About Us",
        "title": "Modern talent acquisition powered by AI you can trust.",
        "paragraphs": [
            "HirePilot is an end-to-end AI recruitment and talent management platform "
            "designed for high-growth teams. We connect every step of the hiring lifecycle — "
            "job creation, candidate applications, resume parsing, screening, interviews, "
            "onboarding and employee development — into one seamless workspace.",
            "Our mission is to eliminate repetitive manual work from recruiting so teams can "
            "focus on what matters most: identifying and nurturing the people who will drive "
            "their business forward.",
        ],
        "points": [
            "Built-in AI resume parser with structured profile extraction",
            "Configurable ATS scoring per job with transparent skill gaps",
            "Recruiter copilot for Q&A and instant pipeline insights",
            "Full onboarding document verification and employee record creation",
        ],
        "visual_emoji": "🚀",
    },
    "features": {
        "tag": "Platform Features",
        "title": "Everything you need to run recruitment at scale.",
        "subtitle": "A complete lifecycle platform, not a point tool. One source of truth for HR, recruiters and hiring managers.",
        "items": [
            {"icon": "fa-solid fa-file-lines", "title": "AI Resume Parser",
             "desc": "Extract structured data — skills, experience, education, projects — from any PDF or DOCX resume."},
            {"icon": "fa-solid fa-chart-simple", "title": "Smart ATS Scoring",
             "desc": "Rank candidates per role with transparent match %, missing-skill gaps and AI recommendations."},
            {"icon": "fa-solid fa-calendar-check", "title": "Interview Workflow",
             "desc": "Schedule job-specific interview rounds, record decisions, and auto-promote to the next round."},
            {"icon": "fa-solid fa-robot", "title": "AI Copilot for HR",
             "desc": "Ask questions about your pipeline in plain English. Scope-guarded responses, grounded in live data."},
        ],
    },
    "workflow": {
        "tag": "How It Works",
        "title": "From job posting to productive employee in 5 clear steps.",
        "subtitle": "Every candidate moves through the same consistent, auditable and AI-assisted pipeline.",
        "steps": [
            {"n": "1", "title": "Apply Online",
             "desc": "Candidates discover jobs on the public careers page and submit a resume in seconds."},
            {"n": "2", "title": "AI Screening",
             "desc": "Resumes are auto-parsed, ATS-scored against the JD, and ranked for HR review."},
            {"n": "3", "title": "Interviews",
             "desc": "Shortlisted candidates move through configurable, job-specific interview rounds."},
            {"n": "4", "title": "Offer & Docs",
             "desc": "Selected candidates complete document verification and accept their offer."},
            {"n": "5", "title": "Onboard",
             "desc": "Employee profile is created, skills are tracked, and talent insights generate automatically."},
        ],
    },
    "benefits_candidates": {
        "tag": "For Job Seekers",
        "title": "The smartest way to find your next opportunity.",
        "paragraph": "Once you submit your resume to HirePilot, our AI reads it fairly and compares it against every requirement. No keyword-game, no black-box rejections.",
        "visual_emoji": "🎯",
        "points": [
            "Fair, transparent ATS evaluation with explainable scores",
            "One profile applies to multiple jobs without re-typing",
            "Automated interview scheduling and personalized email updates",
            "Track every stage of your application in real time",
        ],
        "cta": "See Open Roles →",
    },
    "benefits_recruiters": {
        "tag": "For Recruiters & HR Teams",
        "title": "Ship great hires without burning out your team.",
        "paragraph": "Replace the spreadsheet pipeline with a single structured system that actually saves time every single day.",
        "visual_emoji": "💼",
        "points": [
            "Stop reading every resume — let the AI surface the top 5% for you",
            "Generate interview emails and JD drafts in one click",
            "Reporting & analytics built in — no manual exports",
            "Copilot answers pipeline questions instantly in plain English",
        ],
        "cta": "Schedule a Demo →",
    },
   "featured_jobs": {
        "tag": "Careers",
        "title": "Featured Open Roles",
        "subtitle": "Live positions hiring right now on the HirePilot platform. Click any card to view the full description and apply.",
        "cta_all": "View All Open Roles →",
        "empty": "We don't have any open roles at the moment. Check back soon or reach out via our Contact page.",
    },
    "contact": {
        "tag": "Contact",
        "title": "Have questions? We'd love to hear from you.",
        "paragraph": "Whether you're a candidate looking for an update or a hiring leader evaluating HirePilot for your team, we're one message away.",
        "details": [
            {"icon": "fa-solid fa-envelope", "label": "careers@hirepilot.ai", "title": "Email"},
            {"icon": "fa-solid fa-phone", "label": "+1 (415) 555-0142", "title": "Phone"},
            {"icon": "fa-solid fa-location-dot", "label": "Hyderabad, India · Remote-first", "title": "Office"},
        ],
    },
    "footer": {
        "description": "HirePilot is an end-to-end AI recruitment and talent management platform for modern teams.",
        "cols": [
            {"title": "Platform",
             "links": [("Home", "home"), ("Careers", "careers"), ("About Us", "about"), ("Contact", "contact")]},
            {"title": "For HR",
             "links": [("Recruiter Portal", "hr_login"), ("Jobs", "careers"), ("Analytics", "hr_login"), ("Reports", "hr_login")]},
            {"title": "Legal",
             "links": [("Privacy Policy", "home"), ("Terms of Service", "home"), ("Cookie Policy", "home")]},
        ],
        "copyright": f"© {2026} HirePilot. All rights reserved.",
        "bottom_links": [("Privacy", "home"), ("Terms", "home"), ("Security", "home")],
    },
}


# def _render_public_navbar(active_page: str) -> None:
#     st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)
#     # Use a single row with proper column ratios: logo (wide), spacer, nav buttons, HR Sign In
#     col_logo, col_nav, col_hr = st.columns([4, 3, 1], vertical_alignment="center")
    
#     with col_logo:
#         st.markdown(
#             """
#             <div class="hp-navbar-logo" style="display: flex; align-items: center; gap: 8px; padding: 8px 0;">
#                 <div style="background: #1E40AF; width: 36px; height: 36px; border-radius: 8px; display: flex; align-items: center; justify-content: center; color: white; font-weight: 800; font-size: 1rem;">HP</div>
#                 <div>
#                     <div style="font-size: 1.3rem; font-weight: 800; color: #1E40AF; line-height: 1.2;">HIREPILOT</div>
#                     <div style="font-size: 0.75rem; font-weight: 500; color: #64748B; margin-top: 2px;">AI Recruitment Platform</div>
#                 </div>
#             </div>
#             """,
#             unsafe_allow_html=True,
#         )
    
#     with col_nav:
#         # Navigation buttons in a horizontal row
#         nav_cols = st.columns([1, 1, 1], vertical_alignment="center")
#         with nav_cols[0]:
#             if st.button("Home", key="nv_home", use_container_width=True,
#                          type="primary" if active_page == "home" else "secondary"):
#                 st.session_state.public_page = "Home"
#                 st.rerun()
#         with nav_cols[1]:
#             if st.button("About Us", key="nv_about", use_container_width=True,
#                          type="primary" if active_page == "about" else "secondary"):
#                 st.session_state.public_page = "About Us"
#                 st.rerun()
#         with nav_cols[2]:
#             if st.button("Careers", key="nv_car", use_container_width=True,
#                          type="primary" if active_page == "careers" else "secondary"):
#                 st.session_state.public_page = "Careers"
#                 st.rerun()
    
#     with col_hr:
#         if st.button("HR Sign In", key="nv_hr", use_container_width=True, type="primary"):
#             open_hr_login()
#     st.markdown("<div style='height: 8px;'></div>", unsafe_allow_html=True)

# def _render_public_footer() -> None:
#     F = PUBLIC_CONTENT["footer"]
#     cols_html = "".join(
#         f'''
#         <div class="hp-footer-col">
#           <h4>{c["title"]}</h4>
#           <ul>
#             {''.join(
#               f'<li><a href="?public_page={target}">{label}</a></li>'
#               for label, target in c["links"]
#             )}
#           </ul>
#         </div>
#         '''
#         for c in F["cols"]
#     )
#     bottom_links = "".join(
#         f'<a href="?public_page={t}">{l}</a>'
#         for l, t in F["bottom_links"]
#     )
#     st.markdown(
#         _flatten_html(f"""
#         <footer class="hp-footer">
#           ...
#         </footer>
#         """),
#         unsafe_allow_html=True,
#     )

def _render_public_footer() -> None:
    F = PUBLIC_CONTENT["footer"]
    cols_html = "".join(
        f'''
        <div class="hp-footer-col">
          <h4>{c["title"]}</h4>
          <ul>
            {''.join(
              f'<li><a href="?public_page={target}">{label}</a></li>'
              for label, target in c["links"]
            )}
          </ul>
        </div>
        '''
        for c in F["cols"]
    )
    bottom_links = "".join(
        f'<a href="?public_page={t}">{l}</a>'
        for l, t in F["bottom_links"]
    )
    st.markdown(
        _flatten_html(f"""
        <footer class="hp-footer">
          <div class="hp-container">
            <div class="hp-footer-grid">
              <div class="hp-footer-brand">
                <h3 style="font-size:1.25rem; font-weight:800; letter-spacing:-0.01em;">HIREPILOT</h3>
                <p>{F["description"]}</p>
              </div>
              {cols_html}
            </div>
            <div class="hp-footer-bottom">
              <div>{F["copyright"]}</div>
              <div class="hp-footer-bottom-links">{bottom_links}</div>
            </div>
          </div>
        </footer>
        """),
        unsafe_allow_html=True,
    )
def _render_featured_jobs_section() -> None:
    J = PUBLIC_CONTENT["featured_jobs"]
    st.markdown(
        f"""
        <section class="hp-section">
          <div class="hp-container">
            <div class="hp-section-header">
              <div class="hp-section-tag">{J["tag"]}</div>
              <h2>{J["title"]}</h2>
              <p>{J["subtitle"]}</p>
            </div>
          </div>
        </section>
        """,
        unsafe_allow_html=True,
    )
    jobs_holder = st.container()
    all_jobs = []
    try:
        with jobs_holder:
            with st.spinner("Loading featured roles..."):
                all_jobs = get_public_jobs(search="", department="All", location="All", employment_type="All") or []
    except Exception:
        all_jobs = []

    if not all_jobs:
        st.markdown(
            f'<div class="hp-container"><div class="hp-no-jobs"><p>{J["empty"]}</p></div></div>',
            unsafe_allow_html=True,
        )
        return

    featured = all_jobs[:4]
    for i, job in enumerate(featured):
        title = job.get("title") or "Role"
        dept = job.get("department") or ""
        loc = job.get("location") or ""
        etype = job.get("employment_type") or ""
        desc = job.get("short_description") or job.get("description") or ""
        desc = (desc[:140] + "…") if len(desc) > 140 else desc
        with st.container(border=True):
            st.markdown(f"**{title}**")
            st.markdown(f"<small><i>{dept} · {loc}</i></small>", unsafe_allow_html=True)
            st.caption(desc)
            if st.button("View Job", key=f"ft_job_{job.get('id')}_{i}", type="primary"):
                st.session_state.selected_public_job = job.get("id")
                st.session_state.public_page = "JobDetail"
                st.rerun()
    st.markdown('<div class="hp-container"><div class="hp-jobs-cta">', unsafe_allow_html=True)
    if st.button(J["cta_all"], use_container_width=False, type="secondary"):
        st.session_state.public_page = "Careers"
        st.rerun()
    st.markdown("</div></div>", unsafe_allow_html=True)


def _render_home_page() -> None:
    C = PUBLIC_CONTENT
    H = C["hero"]
    st.markdown(
        f"""
        <section class="hp-hero">
          <div class="hp-container">
            <div class="hp-hero-grid">
              <div class="hp-hero-content">
                <div class="hp-hero-badge"><span>{H["badge_icon"]}</span>{H["badge_text"]}</div>
                <h1>{H["headline_prefix"]}<span class="highlight">{H["headline_highlight"]}</span><br>{H["headline_suffix"]}</h1>
                <p>{H["subhead"]}</p>
              </div>
              <div class="hp-hero-visual">
                <div class="hp-hero-card">
                  <div style="padding: 1rem; border-radius: 12px; background: linear-gradient(135deg, rgba(30,64,175,0.06), rgba(59,130,246,0.1)); border: 1px solid #DBEAFE;">
                    <div style="font-size: 0.8rem; font-weight: 700; color: #1E40AF; text-transform: uppercase; letter-spacing: 0.08em; margin-bottom: 0.5rem;">Live Pipeline Snapshot</div>
                    <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 0.5rem;">
                      <span style="font-size: 0.9rem; color: #475569;">AI/ML Engineer</span>
                      <span style="font-weight: 700; color: #059669;">94% · Strong Shortlist</span>
                    </div>
                    <div style="background: #E2E8F0; height: 8px; border-radius: 999px; overflow: hidden;">
                      <div style="width: 94%; height: 100%; background: linear-gradient(90deg, #1E40AF, #3B82F6);"></div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </section>
        """,
        unsafe_allow_html=True,
    )

    # colp, colc = st.columns([3, 1])
    # with colp:
    #     st.text_input("Search open roles", placeholder="Search jobs, skills, or keywords...",
    #                   label_visibility="collapsed", key="hero_job_search")
    # with colc:
    #     if st.button("Browse Roles", type="primary", use_container_width=True, key="hero_cta"):
    #         st.session_state.public_page = "Careers"
    #         st.rerun()

    stats = H["stat_cards"]
    st.markdown(
        f"""
        <section class="hp-stats">
          <div class="hp-container">
            <div class="hp-stats-grid">
              {''.join(
                f'<div class="hp-stat-item"><div class="stat-number">{s["value"]}</div><div class="stat-label">{s["label"]}</div></div>'
                for s in stats
              )}
            </div>
          </div>
        </section>
        """,
        unsafe_allow_html=True,
    )

# =========================
# FEATURES SECTION
# =========================

    F = C["features"]

# Create all feature cards first
    feature_cards = ""

    for fi in F["items"]:
            feature_cards += f"""
    <div class="hp-feature-card">
        <div class="hp-feature-icon">
              <i class="{fi["icon"]}"></i>
        </div>

        <h4>{fi["title"]}</h4>

        <p>{fi["desc"]}</p>
    </div>
    """
 
# Put all cards inside one complete HTML section
    features_html = f"""
    <section class="hp-section hp-section-alt">

    <div class="hp-container">

        <div class="hp-section-header">

            <div class="hp-section-tag">
                {F["tag"]}
            </div>

            <h2>{F["title"]}</h2>

            <p>{F["subtitle"]}</p>

        </div>

        <div class="hp-features-grid">

            {feature_cards}

        </div>

    </div>

    </section>
    """

# Render the complete HTML
    st.markdown(
        _flatten_html(features_html),
        unsafe_allow_html=True,
    )

    # =========================
    # HOW IT WORKS SECTION
    # =========================

    W = C["workflow"]

# Create all workflow steps first
    workflow_cards = ""

    for s in W["steps"]:
        workflow_cards += f"""
    <div class="hp-workflow-step">

        <div class="hp-workflow-number">
            {s["n"]}
        </div>

        <h4>{s["title"]}</h4>

        <p>{s["desc"]}</p>

    </div>
    """

# Put all workflow cards inside one complete HTML section
    workflow_html = f"""
       <section class="hp-section">

       <div class="hp-container">

        <div class="hp-section-header">

            <div class="hp-section-tag">
                {W["tag"]}
            </div>

            <h2>{W["title"]}</h2>

            <p>{W["subtitle"]}</p>

        </div>

        <div class="hp-workflow">

            {workflow_cards}

        </div>

    </div>

    </section>
    """

# Render the complete HTML
    st.markdown(
        _flatten_html(workflow_html),
        unsafe_allow_html=True,
    )

    BC = C["benefits_candidates"]
    st.markdown(
        f"""
        <section class="hp-section hp-section-alt">
          <div class="hp-container">
            <div class="hp-split">
              <div class="hp-split-visual" style="background: linear-gradient(135deg, #EFF6FF 0%, #DBEAFE 100%);">
                <div style="font-size: 5rem;">{BC["visual_emoji"]}</div>
              </div>
              <div class="hp-split-content">
                <div class="hp-section-tag">{BC["tag"]}</div>
                <h2>{BC["title"]}</h2>
                <p>{BC["paragraph"]}</p>
                <ul class="hp-split-list">
                  {''.join(f'<li>{pt}</li>' for pt in BC["points"])}
                </ul>
                <button id="hp-benefits-candidates" class="hp-btn hp-btn-primary">{BC["cta"]}</button>
              </div>
            </div>
          </div>
        </section>
        """,
        unsafe_allow_html=True,
    )

    BR = C["benefits_recruiters"]
    st.markdown(
        f"""
        <section class="hp-section">
          <div class="hp-container">
            <div class="hp-split">
              <div class="hp-split-content">
                <div class="hp-section-tag">{BR["tag"]}</div>
                <h2>{BR["title"]}</h2>
                <p>{BR["paragraph"]}</p>
                <ul class="hp-split-list">
                  {''.join(f'<li>{pt}</li>' for pt in BR["points"])}
                </ul>
                <button id="hp-benefits-recruiters" class="hp-btn hp-btn-secondary">{BR["cta"]}</button>
              </div>
              <div class="hp-split-visual" style="background: linear-gradient(135deg, #FEF3C7 0%, #FDE68A 100%);">
                <div style="font-size: 5rem;">{BR["visual_emoji"]}</div>
              </div>
            </div>
          </div>
        </section>
        """,
        unsafe_allow_html=True,
    )

    # _render_featured_jobs_section()

    CK = C["contact"]
    st.markdown(
        f"""
        <section class="hp-section hp-section-alt">
          <div class="hp-container">
            <div class="hp-contact-grid">
              <div class="hp-contact-info">
                <div class="hp-section-tag">{CK["tag"]}</div>
                <h2>{CK["title"]}</h2>
                <p>{CK["paragraph"]}</p>
                {''.join(
                  f'<div class="hp-contact-detail"><div class="icon"><i class="{d["icon"]}"></i></div><div><div style="font-size:0.75rem;color:#64748B;text-transform:uppercase;letter-spacing:0.08em;font-weight:700;">{d["title"]}</div><div style="color:#0F172A;font-weight:500;">{d["label"]}</div></div></div>'
                  for d in CK["details"]
                )}
              </div>
              <div id="hp-contact-form-marker"></div>
            </div>
          </div>
        </section>
        """,
        unsafe_allow_html=True,
    )
    # with st.container():
    #     st.markdown(
    #         '<div class="hp-container" style="margin-top:-2rem;"><div class="hp-contact-form">',
    #         unsafe_allow_html=True,
    #     )
    #     with st.form("public_contact_form", clear_on_submit=True):
    #         cc1, cc2 = st.columns(2)
    #         with cc1:
    #             c_name = st.text_input("Full Name", key="contact_name")
    #         with cc2:
    #             c_email = st.text_input("Email Address", key="contact_email")
    #         c_msg = st.text_area("Message", height=130, key="contact_message")
    #         sent = st.form_submit_button("Send Message", type="primary", use_container_width=True)
    #         if sent:
    #             if c_name and c_email and c_msg:
    #                 st.success("Thanks! Your message has been queued — we'll get back to you shortly.")
    #             else:
    #                 st.warning("Please enter your name, email and a message before sending.")
    #     st.markdown("</div></div>", unsafe_allow_html=True)
    _, form_col, _ = st.columns([1, 6, 1])
    with form_col:
        with st.form("public_contact_form", clear_on_submit=True):
            cc1, cc2 = st.columns(2)
            with cc1:
                c_name = st.text_input("Full Name", key="contact_name")
            with cc2:
                c_email = st.text_input("Email Address", key="contact_email")
            c_msg = st.text_area("Message", height=130, key="contact_message")
            sent = st.form_submit_button("Send Message", type="primary", use_container_width=True)
            if sent:
                if c_name and c_email and c_msg:
                    st.success("Thanks! Your message has been queued — we'll get back to you shortly.")
                else:
                    st.warning("Please enter your name, email and a message before sending.")
    # _render_public_footer()


# def _render_careers_page() -> None:
#     st.markdown(
#         f"""
#         <section class="hp-hero" style="padding: 6rem 0 2rem;">
#           <div class="hp-container">
#             <div class="hp-section-header" style="margin-bottom: 2rem;">
#               <div class="hp-section-tag">Open Roles</div>
#               <h2>Explore Career Opportunities</h2>
#               <p>Find a role that matches your skills, experience and career goals. We update this page daily as new positions open up.</p>
#             </div>
#           </div>
#         </section>
#         """,
#         unsafe_allow_html=True,
#     )
#     f1, f2, f3 = st.columns(3)
#     with f1:
#         department = st.selectbox("Department",
#             ["All Departments", "Engineering", "Technology", "Human Resources", "Operations", "Product", "Data"],
#             key="career_department")
#     with f2:
#         location = st.selectbox("Location",
#             ["All Locations", "Hyderabad", "Bengaluru", "Chennai", "Mumbai", "Remote"],
#             key="career_location")
#     with f3:
#         employment_type = st.selectbox("Employment Type",
#             ["All Types", "Full-Time", "Part-Time", "Internship", "Contract"],
#             key="career_employment_type")
#     dept_api = "All" if department == "All Departments" else department
#     loc_api = "All" if location == "All Locations" else location
#     etype_api = "All" if employment_type == "All Types" else employment_type

#     with st.spinner("Loading job listings..."):
#         jobs = get_public_jobs(search="", department=dept_api, location=loc_api, employment_type=etype_api) or []

#     if not jobs:
#         st.markdown(
#             '<div class="hp-container"><div class="hp-no-jobs"><p>No job openings match your filters right now. Try broadening your search, or check back again soon.</p></div></div>',
#             unsafe_allow_html=True,
#         )
#         _render_public_footer()
#         return

#     parts = []
#     for j in jobs:
#         title = j.get("title") or "Role"
#         dept = j.get("department") or ""
#         loc = j.get("location") or ""
#         etype = j.get("employment_type") or ""
#         exp = j.get("experience_required") or ""
#         desc = j.get("short_description") or j.get("description") or ""
#         desc = (desc[:160] + "…") if len(desc) > 160 else desc
#         parts.append(f'''
#           <div class="hp-job-card">
#             <div class="hp-job-header"><h3 style="margin:0;">{title}</h3><span class="hp-job-badge">{etype or "Full-Time"}</span></div>
#             <div class="hp-job-meta">
#               <div class="hp-job-meta-item"><span class="hp-job-meta-icon">🏢</span>{dept}</div>
#               <div class="hp-job-meta-item"><span class="hp-job-meta-icon">📍</span>{loc}</div>
#               {f'<div class="hp-job-meta-item"><span class="hp-job-meta-icon">⏱️</span>{exp}</div>' if exp else ''}
#             </div>
#             <div class="hp-job-description"><p>{desc}</p></div>
#           </div>
#         ''')
#     st.markdown(f'<div class="hp-container"><div class="hp-jobs-grid">{"".join(parts)}</div></div>', unsafe_allow_html=True)

#     per_row = 3
#     for row_start in range(0, len(jobs), per_row):
#         row = jobs[row_start:row_start + per_row]
#         cols = st.columns(len(row))
#         for j, col in zip(row, cols):
#             with col:
#                 if st.button(f"View Job", key=f"cv_{j.get('id')}_{row_start}", type="primary", use_container_width=True):
#                     st.session_state.selected_public_job = j.get("id")
#                     st.session_state.public_page = "JobDetail"
#                     st.rerun()
#     _render_public_footer()




# def _render_about_page() -> None:
#     A = PUBLIC_CONTENT["about"]
#     st.markdown(
#         f"""
#         <section class="hp-hero" style="padding: 5rem 0 2rem;">
#           <div class="hp-container">
#             <div class="hp-section-header" style="margin-bottom:2rem;">
#               <div class="hp-section-tag">{A["tag"]}</div>
#               <h2>About HirePilot</h2>
#               <p>We're building the operating system for modern talent teams.</p>
#             </div>
#             <div class="hp-about-grid">
#               <div class="hp-about-content">
#                 <h2>{A["title"]}</h2>
#                 {''.join(f'<p>{p}</p>' for p in A["paragraphs"])}
#               </div>
#               <div class="hp-about-image" style="background: linear-gradient(135deg,#EFF6FF,#DBEAFE);">
#                 <div style="font-size:5rem;">{A["visual_emoji"]}</div>
#               </div>
#             </div>
#             <div style="margin-top:3rem;">
#               <ul class="hp-split-list" style="max-width: 720px; margin: 0 auto;">
#                 {''.join(f'<li style="font-size:1rem;">{pt}</li>' for pt in A["points"])}
#               </ul>
#             </div>
#           </div>
#         </section>
#         """,
#         unsafe_allow_html=True,
#     )
#     _render_public_footer()


# def _render_contact_page() -> None:
#     CK = PUBLIC_CONTENT["contact"]
#     st.markdown(
#         f"""
#         <section class="hp-hero" style="padding: 5rem 0 2rem;">
#           <div class="hp-container">
#             <div class="hp-contact-grid">
#               <div class="hp-contact-info">
#                 <div class="hp-section-tag">{CK["tag"]}</div>
#                 <h2>{CK["title"]}</h2>
#                 <p>{CK["paragraph"]}</p>
#                 {''.join(
#                   f'<div class="hp-contact-detail"><div class="icon"><i class="{d["icon"]}"></i></div><div><div style="font-size:0.75rem;color:#64748B;text-transform:uppercase;letter-spacing:0.08em;font-weight:700;">{d["title"]}</div><div style="color:#0F172A;font-weight:500;">{d["label"]}</div></div></div>'
#                   for d in CK["details"]
#                 )}
#               </div>
#             </div>
#           </div>
#         </section>
#         """,
#         unsafe_allow_html=True,
#     )
#     st.markdown('<div class="hp-container" style="margin-top:-2rem;">', unsafe_allow_html=True)
#     st.markdown('<div class="hp-contact-form">', unsafe_allow_html=True)
#     with st.form("public_contact_full_form", clear_on_submit=True):
#         cc1, cc2 = st.columns(2)
#         with cc1:
#             c_name = st.text_input("Full Name", key="contact_full_name")
#         with cc2:
#             c_email = st.text_input("Email Address", key="contact_full_email")
#         st.text_input("Subject", key="contact_full_subject")
#         c_msg = st.text_area("Message", height=150, key="contact_full_message")
#         sent = st.form_submit_button("Send Message", type="primary", use_container_width=True)
#         if sent:
#             if c_name and c_email and c_msg:
#                 st.success("Thank you! Your message has been sent to the HirePilot team.")
#             else:
#                 st.warning("Please fill in your name, email and message.")
#     st.markdown('</div></div>', unsafe_allow_html=True)
#     _render_public_footer()


def render_company_website():
    """
    Render the public HirePilot website.

    Only one public page is rendered during each Streamlit rerun.
    The navbar and footer are shared and rendered exactly once.
    """
    st.markdown(
        """
        <style>
        /* ── Public site: horizontal centering & container width only ── */
        /* 1. Undo the HR-portal block-container sidebar offset and asymmetric padding
              so the root streamlit wrapper doesn't push everything toward the right. */
        [data-testid="stMainBlockContainer"] {
            max-width: none !important;
            padding-top: 0 !important;
            padding-bottom: 0 !important;
            padding-left: 0 !important;
            padding-right: 0 !important;
            margin-left: auto !important;
            margin-right: auto !important;
        }
        .main .block-container {
            max-width: none !important;
            padding-top: 0 !important;
            padding-bottom: 0 !important;
            padding-left: 0 !important;
            padding-right: 0 !important;
            margin-left: auto !important;
            margin-right: auto !important;
        }
        /* 2. Section wrappers span the full viewport width so backgrounds
              (hero gradient, alt section colors, footer) bleed edge-to-edge. */
        .hp-section,
        .hp-hero,
        .hp-stats,
        .hp-footer {
            width: 100%;
            box-sizing: border-box;
        }
        /* 3. The content container: centered, max-width, symmetric side gutter —
              the core rule that fixes the "lopsided left margin" symptom. */
        .hp-container {
            width: min(1240px, calc(100% - 4rem));
            max-width: 1240px;
            margin-left: auto !important;
            margin-right: auto !important;
            padding-left: 0;
            padding-right: 0;
            box-sizing: border-box;
        }
        /* 4. Tighter gutter on tablet/phone so content isn't cramped. */
        @media (max-width: 768px) {
            .hp-container {
                width: min(1240px, calc(100% - 2.5rem));
            }
        }
         @media (max-width: 480px) {
            .hp-container {
                width: calc(100% - 1.5rem);
            }
        }
        /* 5. Push the first section down below the now-fixed navbar. */
        .hp-hero {
            padding-top: 7rem !important;
        }
        
        </style>
        """,
        unsafe_allow_html=True,
    )
    public_page = st.session_state.get("public_page", "Home")
    active_map = {
        "Home": "home",
        "Careers": "careers",
        "JobDetail": "careers",
        "About Us": "about",
        "Contact": "contact",
    }
    active = active_map.get(public_page, "home")
    _render_public_navbar(active, on_hr_sign_in=open_hr_login)
    if public_page == "Home":
        _render_home_page()
    elif public_page == "About Us":
        render_about_page(PUBLIC_CONTENT)
    elif public_page == "Careers":
        render_careers_page(PUBLIC_CONTENT)
    elif public_page == "JobDetail":
        _render_job_detail_page()
    elif public_page == "Contact":
        _render_contact_page()
    else:
        _render_home_page()
    _render_public_footer()


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
    .main .block-container {
        padding-left: 2rem !important;
        padding-right: 2rem !important;
    }
    div[class*="st-key-hr_login_back_btn_wrap"] {
        padding-left: 17rem;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

    top_left, top_center, top_right = st.columns(
    [1, 2, 1], vertical_alignment="center"
    )
    
    with top_left:
        with st.container(key="hr_login_back_btn_wrap"):
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

    # elif page == "AI Screening":

    #     from frontend.components.ai_screening import (
    #         render_ai_screening
    #     )

    #     render_ai_screening()

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

    AppState.init()
    initialize_application_state()

    app_mode = st.session_state.get("app_mode", "public")

    if app_mode in ("public", "hr_login"):
        inject_public_css_once()
    else:
        inject_css_once()

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