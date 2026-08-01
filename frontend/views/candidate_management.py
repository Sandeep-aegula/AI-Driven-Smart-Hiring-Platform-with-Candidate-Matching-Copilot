import streamlit as st
import os
import sys
import datetime
from typing import Optional

# Setup path to import api_client
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
project_root = os.path.dirname(parent_dir)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from frontend.components import api_client
from frontend.components.page_utils import setup_page

# Page Config
st.set_page_config(
    page_title="Candidate Management - HirePilot",
    page_icon="👥",
    layout="wide",
    initial_sidebar_state="expanded"
)

setup_page("Candidate Management", "Review, compare, and shortlist candidates using AI", page_key=__file__)

# ══════════════════════════════════════════════════════════════════════════════
# STATE INITIALIZATION
# ══════════════════════════════════════════════════════════════════════════════

if "selected_job_id" not in st.session_state:
    st.session_state.selected_job_id = None
if "selected_candidate_id" not in st.session_state:
    st.session_state.selected_candidate_id = None
if "selected_application_ids" not in st.session_state:
    st.session_state.selected_application_ids = []
if "search_query" not in st.session_state:
    st.session_state.search_query = ""
if "status_filter" not in st.session_state:
    st.session_state.status_filter = "All"
if "min_ats_score" not in st.session_state:
    st.session_state.min_ats_score = 0


# ══════════════════════════════════════════════════════════════════════════════
# HELPER FUNCTIONS
# ══════════════════════════════════════════════════════════════════════════════

def fetch_candidates(job_id: Optional[int] = None, search: str = "", status: str = "All", min_score: int = 0):
    """Fetch candidates from the API with filters via the shared API client."""
    try:
        return api_client.get_candidates(
            search=search,
            status=status if status != "All" else "All",
            skill="All",
            job_id=job_id,
            min_match_score=min_score,
            limit=100,
            offset=0,
        )
    except Exception as e:
        st.error(f"Error fetching candidates: {e}")
        return None

def fetch_jobs():
    """Fetch all jobs."""
    try:
        jobs = api_client.get_jobs()
        return jobs or []
    except Exception as e:
        st.error(f"Error fetching jobs: {e}")
        return []

def shortlist_candidate(application_id: int):
    """Shortlist a single candidate via the shared API client."""
    try:
        result = api_client.shortlist_candidate(application_id)
        if result:
            return result
        st.error("Failed to shortlist candidate.")
        return None
    except Exception as e:
        st.error(f"Error shortlisting candidate: {e}")
        return None

def shortlist_bulk(application_ids: list[int]):
    """Bulk shortlist multiple candidates via the shared API client."""
    try:
        result = api_client.shortlist_bulk(application_ids)
        if result:
            return result
        st.error("Failed to bulk shortlist.")
        return None
    except Exception as e:
        st.error(f"Error bulk shortlisting: {e}")
        return None

def get_application_details(application_id: int):
    """Get detailed application information via the shared API client."""
    try:
        # Use get_candidate with application context; the API client
        # does not expose a dedicated application-details helper, so we
        # call the REST endpoint directly with the shared base URL.
        import httpx as _httpx
        resp = _httpx.get(
            f"{api_client.BASE_URL}/candidates/applications/{application_id}",
            timeout=30.0,
        )
        return resp.json() if resp.status_code == 200 else None
    except Exception as e:
        st.error(f"Error fetching application: {e}")
        return None


# ══════════════════════════════════════════════════════════════════════════════
# HEADER
# ══════════════════════════════════════════════════════════════════════════════

col_header_1, col_header_2 = st.columns([4, 1])

with col_header_1:
    st.markdown("### Candidate Management")
    st.caption("Review, compare, and shortlist candidates using AI")

with col_header_2:
    if st.button("🔄 Refresh", width="stretch"):
        st.rerun()

st.markdown("<div style='height:12px;'></div>", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# FILTERS
# ══════════════════════════════════════════════════════════════════════════════

all_jobs = fetch_jobs()
job_options = {"All Jobs": None}
for job in all_jobs:
    job_options[f"{job.get('title')} - {job.get('department')}"] = job.get("id")

col_f1, col_f2, col_f3, col_f4, col_f5 = st.columns([2.5, 1.5, 1.5, 2, 1])

with col_f1:
    selected_job_label = st.selectbox(
        "Job Role",
        list(job_options.keys()),
        key="job_filter_select"
    )
    st.session_state.selected_job_id = job_options[selected_job_label]

with col_f2:
    status_filter = st.selectbox(
        "Status",
        ["All", "submitted", "under_review", "shortlisted", "interview", "rejected"],
        key="status_filter_select"
    )
    st.session_state.status_filter = status_filter

with col_f3:
    min_ats = st.slider(
        "Min ATS Score",
        min_value=0,
        max_value=100,
        value=0,
        step=5,
        key="ats_slider"
    )
    st.session_state.min_ats_score = min_ats

with col_f4:
    search_input = st.text_input(
        "Search",
        placeholder="Name, email, or skills...",
        key="search_input",
        label_visibility="collapsed"
    )
    st.session_state.search_query = search_input

with col_f5:
    if st.button("Clear Filters", width="stretch"):
        st.session_state.selected_job_id = None
        st.session_state.status_filter = "All"
        st.session_state.min_ats_score = 0
        st.session_state.search_query = ""
        st.rerun()

st.markdown("<div style='height:16px;'></div>", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# FETCH DATA
# ══════════════════════════════════════════════════════════════════════════════

candidates_data = fetch_candidates(
    job_id=st.session_state.selected_job_id,
    search=st.session_state.search_query,
    status=st.session_state.status_filter,
    min_score=st.session_state.min_ats_score
)

if not candidates_data:
    st.error("Failed to load candidates data")
    st.stop()

candidates = candidates_data.get("items", [])
total_candidates = candidates_data.get("total", 0)
status_counts = candidates_data.get("status_counts", {})
avg_ats_score = candidates_data.get("average_ats_score", 0.0)
selected_job_title = candidates_data.get("selected_job_title", "All Jobs")
role_candidate_count = candidates_data.get("role_candidate_count", 0)


# ══════════════════════════════════════════════════════════════════════════════
# SUMMARY CARDS
# ══════════════════════════════════════════════════════════════════════════════

col_s1, col_s2, col_s3, col_s4 = st.columns(4)

with col_s1:
    st.markdown(f"""
    <div style="background:#FFFFFF; border:1px solid #E2E8F0; border-radius:12px; padding:16px; text-align:center;">
        <div style="font-size:2rem; font-weight:800; color:#6366F1;">{total_candidates}</div>
        <div style="font-size:0.85rem; color:#64748B; font-weight:600;">Total Candidates</div>
        <div style="font-size:0.7rem; color:#94A3B8; margin-top:4px;">{selected_job_title}</div>
    </div>
    """, unsafe_allow_html=True)

with col_s2:
    st.markdown(f"""
    <div style="background:#FFFFFF; border:1px solid #E2E8F0; border-radius:12px; padding:16px; text-align:center;">
        <div style="font-size:2rem; font-weight:800; color:#10B981;">{avg_ats_score}%</div>
        <div style="font-size:0.85rem; color:#64748B; font-weight:600;">Avg ATS Score</div>
        <div style="font-size:0.7rem; color:#94A3B8; margin-top:4px;">For selected role</div>
    </div>
    """, unsafe_allow_html=True)

with col_s3:
    shortlisted_count = status_counts.get("shortlisted", 0)
    st.markdown(f"""
    <div style="background:#FFFFFF; border:1px solid #E2E8F0; border-radius:12px; padding:16px; text-align:center;">
        <div style="font-size:2rem; font-weight:800; color:#F59E0B;">{shortlisted_count}</div>
        <div style="font-size:0.85rem; color:#64748B; font-weight:600;">Shortlisted</div>
        <div style="font-size:0.7rem; color:#94A3B8; margin-top:4px;">Ready for interview</div>
    </div>
    """, unsafe_allow_html=True)

with col_s4:
    under_review_count = status_counts.get("under_review", 0)
    st.markdown(f"""
    <div style="background:#FFFFFF; border:1px solid #E2E8F0; border-radius:12px; padding:16px; text-align:center;">
        <div style="font-size:2rem; font-weight:800; color:#8B5CF6;">{under_review_count}</div>
        <div style="font-size:0.85rem; color:#64748B; font-weight:600;">Under Review</div>
        <div style="font-size:0.7rem; color:#94A3B8; margin-top:4px;">Pending decision</div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<div style='height:20px;'></div>", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# STATUS BREAKDOWN
# ══════════════════════════════════════════════════════════════════════════════

with st.expander(f"Status Breakdown - {selected_job_title}", expanded=False):
    if status_counts:
        status_cols = st.columns(len(status_counts))
        for idx, (status, count) in enumerate(status_counts.items()):
            with status_cols[idx]:
                st.metric(label=status.title(), value=count)
    else:
        st.info("No candidates match the current filters")

st.markdown("<div style='height:16px;'></div>", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# BULK ACTIONS
# ══════════════════════════════════════════════════════════════════════════════

if len(st.session_state.selected_application_ids) > 0:
    st.markdown(f"""
    <div style="background:#EEF2FF; border:1px solid #C7D2FE; border-radius:8px; padding:12px 16px; margin-bottom:12px;">
        <span style="font-weight:600; color:#4F46E5;">{len(st.session_state.selected_application_ids)} candidates selected</span>
    </div>
    """, unsafe_allow_html=True)

    col_ba1, col_ba2, col_ba3 = st.columns([1, 1, 4])

    with col_ba1:
        if st.button(f"Shortlist Selected ({len(st.session_state.selected_application_ids)})", type="primary", width="stretch"):
            with st.spinner("Shortlisting candidates..."):
                result = shortlist_bulk(st.session_state.selected_application_ids)
                if result and result.get("success"):
                    st.success(f"✅ {result.get('message')}")
                    st.session_state.selected_application_ids = []
                    st.rerun()

    with col_ba2:
        if st.button("Clear Selection", width="stretch"):
            st.session_state.selected_application_ids = []
            st.rerun()

st.markdown("<div style='height:8px;'></div>", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# CANDIDATE TABLE
# ══════════════════════════════════════════════════════════════════════════════

st.markdown(f"#### Candidates for {selected_job_title} ({role_candidate_count})")
st.caption(f"Showing {len(candidates)} candidates")

if not candidates:
    st.info("No candidates match the current filters")
else:
    # Table header
    st.markdown("""
    <div style="background:#F8FAFC; border:1px solid #E2E8F0; border-radius:8px 8px 0 0; padding:12px 16px; display:flex; align-items:center; font-weight:600; font-size:0.85rem; color:#475569;">
        <div style="width:40px;"></div>
        <div style="flex:0.8;">ID</div>
        <div style="flex:2.5;">Candidate</div>
        <div style="flex:1.2;">ATS Score</div>
        <div style="flex:1.2;">Status</div>
        <div style="flex:1;">Experience</div>
        <div style="flex:1.5;">Applied On</div>
        <div style="flex:2;">Actions</div>
    </div>
    """, unsafe_allow_html=True)

    # Table rows
    for idx, candidate in enumerate(candidates):
        cand_id = candidate.get("id")
        app_id = candidate.get("application_id")
        name = candidate.get("name", "Unknown")
        email = candidate.get("email", "")
        ats_score = candidate.get("ats_score", 0)
        status = candidate.get("status", "Applied")
        experience = candidate.get("years_experience", 0)
        applied_date = candidate.get("created_at", "")

        try:
            applied_formatted = datetime.datetime.fromisoformat(applied_date).strftime("%b %d, %Y") if applied_date else "N/A"
        except:
            applied_formatted = "N/A"

        # Status color
        status_color = "#10B981" if status == "shortlisted" else ("#F59E0B" if status == "under_review" else "#6366F1")

        # ATS score color
        ats_color = "#10B981" if ats_score >= 75 else ("#F59E0B" if ats_score >= 50 else "#EF4444")

        # Row container
        with st.container():
            st.markdown(f"""
            <div style="background:#FFFFFF; border:1px solid #E2E8F0; border-top:none; padding:12px 16px; display:flex; align-items:center; font-size:0.85rem;">
                <div style="width:40px;">
                    <input type="checkbox" id="chk_{app_id}" style="width:16px; height:16px; cursor:pointer;">
                </div>
                <div style="flex:0.8; color:#64748B;">#{cand_id}</div>
                <div style="flex:2.5;">
                    <div style="font-weight:600; color:#0F172A;">{name}</div>
                    <div style="font-size:0.75rem; color:#64748B;">{email}</div>
                </div>
                <div style="flex:1.2;">
                    <span style="background:{ats_color}15; color:{ats_color}; padding:4px 12px; border-radius:6px; font-weight:700; font-size:0.9rem;">
                        {ats_score}%
                    </span>
                </div>
                <div style="flex:1.2;">
                    <span style="background:{status_color}15; color:{status_color}; padding:4px 10px; border-radius:6px; font-weight:600; font-size:0.75rem;">
                        {status}
                    </span>
                </div>
                <div style="flex:1; color:#475569;">{experience} Yrs</div>
                <div style="flex:1.5; color:#64748B; font-size:0.8rem;">{applied_formatted}</div>
                <div style="flex:2;">
                    <!-- Actions will be Streamlit buttons below -->
                </div>
            </div>
            """, unsafe_allow_html=True)

            # Action buttons
            col_a1, col_a2, col_a3, col_a4 = st.columns([1, 1, 1, 1])

            with col_a1:
                if st.button("📄 Resume", key=f"resume_{app_id}", width="stretch"):
                    st.session_state.selected_application_id = app_id
                    st.session_state.show_resume_panel = True
                    st.rerun()

            with col_a2:
                is_selected = app_id in st.session_state.selected_application_ids
                if st.button("☑️" if is_selected else "☐", key=f"select_{app_id}", width="stretch"):
                    if is_selected:
                        st.session_state.selected_application_ids.remove(app_id)
                    else:
                        st.session_state.selected_application_ids.append(app_id)
                    st.rerun()

            with col_a3:
                if status != "shortlisted":
                    if st.button("⭐ Shortlist", key=f"shortlist_{app_id}", type="primary", width="stretch"):
                        with st.spinner("Shortlisting..."):
                            result = shortlist_candidate(app_id)
                            if result and result.get("success"):
                                st.success(f"✅ {name} shortlisted!")
                                st.rerun()
                else:
                    st.markdown("<span style='color:#10B981; font-size:0.75rem; font-weight:600;'>✅ Shortlisted</span>", unsafe_allow_html=True)

            with col_a4:
                if st.button("👁️ View", key=f"view_{app_id}", width="stretch"):
                    st.session_state.selected_application_id = app_id
                    st.session_state.show_resume_panel = True
                    st.rerun()

st.markdown("<div style='height:24px;'></div>", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# RESUME PANEL (SIDE DRAWER)
# ══════════════════════════════════════════════════════════════════════════════

if st.session_state.get("show_resume_panel") and st.session_state.get("selected_application_id"):
    app_id = st.session_state.selected_application_id

    with st.sidebar:
        st.markdown("### Resume Details")

        with st.spinner("Loading application details..."):
            app_details = get_application_details(app_id)

        if app_details:
            candidate = app_details.get("candidate", {})
            job = app_details.get("job", {})
            resume = app_details.get("resume")
            ats_score_data = app_details.get("ats_score", {})

            # Close button
            if st.button("✕ Close", width="stretch"):
                st.session_state.show_resume_panel = False
                st.session_state.selected_application_id = None
                st.rerun()

            st.markdown("<div style='height:12px;'></div>", unsafe_allow_html=True)

            # Candidate info
            st.markdown(f"**{candidate.get('name')}**")
            st.caption(f"Applied for: {job.get('title') if job else 'Unknown'}")
            st.markdown(f"📧 {candidate.get('email')}")
            st.markdown(f"📱 {candidate.get('phone') or 'N/A'}")
            st.markdown(f"📍 {candidate.get('location') or 'Remote'}")
            st.markdown(f"💼 {candidate.get('years_experience', 0)} years experience")

            st.markdown("<div style='height:16px;'></div>", unsafe_allow_html=True)

            # ATS Score
            if ats_score_data:
                ats = ats_score_data.get("ats_score", 0)
                ats_color = "#10B981" if ats >= 75 else ("#F59E0B" if ats >= 50 else "#EF4444")

                st.markdown(f"""
                <div style="background:{ats_color}15; border:1px solid {ats_color}40; border-radius:12px; padding:16px; text-align:center;">
                    <div style="font-size:2.5rem; font-weight:900; color:{ats_color};">{ats}%</div>
                    <div style="font-size:0.85rem; color:#64748B; font-weight:600;">ATS Score</div>
                </div>
                """, unsafe_allow_html=True)

                st.markdown("<div style='height:12px;'></div>", unsafe_allow_html=True)

                with st.expander("Score Breakdown", expanded=False):
                    st.markdown(f"**Skills:** {ats_score_data.get('skills_score', 0)}%")
                    st.markdown(f"**Experience:** {ats_score_data.get('experience_score', 0)}%")
                    st.markdown(f"**Education:** {ats_score_data.get('education_score', 0)}%")
                    st.markdown(f"**Keywords:** {ats_score_data.get('keyword_score', 0)}%")

                    strengths = ats_score_data.get("strengths", [])
                    if strengths:
                        st.markdown("**Strengths:**")
                        for strength in strengths:
                            st.markdown(f"- {strength}")

                    gaps = ats_score_data.get("gaps", [])
                    if gaps:
                        st.markdown("**Gaps:**")
                        for gap in gaps:
                            st.markdown(f"- {gap}")

            st.markdown("<div style='height:16px;'></div>", unsafe_allow_html=True)

            # Resume file info
            if resume:
                st.markdown("**Resume File:**")
                st.markdown(f"📄 {resume.get('original_filename')}")
                st.caption(f"Uploaded: {resume.get('uploaded_at', 'N/A')[:10]}")

                if st.button("📥 Download Resume", width="stretch"):
                    st.info("Resume download feature coming soon")

            st.markdown("<div style='height:16px;'></div>", unsafe_allow_html=True)

            # Shortlist action
            if app_details.get("status") != "shortlisted":
                if st.button("⭐ Shortlist Candidate", type="primary", width="stretch"):
                    with st.spinner("Shortlisting..."):
                        result = shortlist_candidate(app_id)
                        if result and result.get("success"):
                            st.success(f"✅ Candidate shortlisted!")
                            st.rerun()
            else:
                st.success("✅ Already Shortlisted")
        else:
            st.error("Failed to load application details")
