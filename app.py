import streamlit as st
import sys
import os

# Ensure the project root is in the path for proper module imports
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

# Import layout utilities and seed database
from utils.styles import inject_css
from utils.dummy_data import initialize_session_state

# Import presentation subcomponents
from components.header import render_header
from components.dashboard_cards import render_kpis
from components.create_job import render_create_job
from components.upload_resume import render_upload_resume
from components.workflow import render_workflow
from components.resume_analysis import render_resume_analysis
from components.job_match import render_job_matching
from components.candidate_table import render_candidate_table
from components.analytics import render_analytics
from components.recommendation import render_recommendation
from components.timeline import render_timeline
from components.footer import render_footer

# ==========================================
# PAGE SETTINGS
# ==========================================
st.set_page_config(
    page_title="AI Recruitment & Talent Management Copilot",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ==========================================
# INITIALIZATION & STYLE INJECTION
# ==========================================
initialize_session_state()
inject_css()

# ==========================================
# RENDERING DASHBOARD PAGE LAYOUT
# ==========================================

# SECTION 1: HEADER
render_header()

# SECTION 2: DASHBOARD OVERVIEW (KPI CARDS)
render_kpis()

# SECTION 3 & 4: CREATE JOB REQUIREMENT & RESUME UPLOAD (SIDE-BY-SIDE)
row1_col1, row1_col2 = st.columns([5, 4])
with row1_col1:
    render_create_job()
with row1_col2:
    render_upload_resume()

st.markdown("<div style='height: 24px;'></div>", unsafe_allow_html=True)

# PROCESS FLOW PIPELINE (Full width status flow)
render_workflow()

# SECTION 5 & 6: AI RESUME ANALYSIS & JOB FIT MATCHING (SIDE-BY-SIDE)
row2_col1, row2_col2 = st.columns([5, 4])
with row2_col1:
    render_resume_analysis()
with row2_col2:
    render_job_matching()

st.markdown("<div style='height: 24px;'></div>", unsafe_allow_html=True)

# SECTION 7: CANDIDATE DATABASE BOARD (FULL WIDTH)
render_candidate_table()

# # SECTION 8: HIRING ANALYTICS & INSIGHTS (FULL WIDTH)
# render_analytics()

# SECTION 9 & 10: AI RECOMMENDATIONS & TIMELINE ACTIVITIES (SIDE-BY-SIDE)
row3_col1, row3_col2 = st.columns([5, 4])
with row3_col1:
    render_recommendation()
with row3_col2:
    render_timeline()

# SECTION 11: FOOTER (FULL WIDTH)
render_footer()
