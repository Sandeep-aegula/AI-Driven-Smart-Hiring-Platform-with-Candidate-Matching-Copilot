import streamlit as st
import os
import sys
import datetime

# Setup path to import api_client
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
project_root = os.path.dirname(parent_dir)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from frontend.components import api_client
from frontend.services.cache import get_jobs_cached
from frontend.services.app_state import AppState
from frontend.components.page_utils import setup_page, render_sidebar_footer

# Page Config
st.set_page_config(
    page_title="Job Management - HirePilot",
    page_icon="💼",
    layout="wide",
    initial_sidebar_state="expanded"
)

setup_page("Job Openings", "Manage and view your job openings", page_key=__file__)

# State initialization
if "job_action" not in st.session_state:
    st.session_state.job_action = "list"
if "selected_job_id" not in st.session_state:
    st.session_state.selected_job_id = None
if "generated_jd_data" not in st.session_state:
    st.session_state.generated_jd_data = None

# Back to List Helper
def go_to_list():
    st.session_state.job_action = "list"
    st.session_state.selected_job_id = None
    st.session_state.generated_jd_data = None
    st.session_state.pop("job_form_key", None)
    st.rerun()


def _seed_job_form(job_data, generated=None):
    src = {**job_data, **(generated or {})}
    dl = job_data.get("deadline")
    st.session_state.update({
        "jf_title": src.get("title", ""),
        "jf_department": src.get("department", ""),
        "jf_location": src.get("location", "Remote"),
        "jf_hiring_manager": src.get("hiring_manager", ""),
        "jf_employment_type": src.get("employment_type", "Full-time"),
        "jf_exp_min": int(src.get("experience_min", 0)),
        "jf_exp_max": int(src.get("experience_max", 0)),
        "jf_sal_min": int(src.get("salary_min", 0)),
        "jf_sal_max": int(src.get("salary_max", 0)),
        "jf_deadline": (
            datetime.datetime.strptime(dl, "%Y-%m-%d").date()
            if dl else datetime.date.today() + datetime.timedelta(days=30)
        ),
        "jf_required_skills": "\n".join(src.get("requirements", [])),
        "jf_description": src.get("description", ""),
        "jf_responsibilities": "\n".join(src.get("responsibilities", [])),
        "jf_preferred_skills": "\n".join(src.get("preferred_skills", [])),
        "jf_benefits": "\n".join(src.get("benefits", [])),
    })


def _build_job_payload(status="Active"):
    requirements = [l.strip() for l in st.session_state.get("jf_required_skills", "").split("\n") if l.strip()]
    return {
        "title": st.session_state.get("jf_title", "").strip(),
        "department": st.session_state.get("jf_department", "").strip(),
        "location": st.session_state.get("jf_location", "Remote").strip(),
        "experience_min": int(st.session_state.get("jf_exp_min", 0)),
        "experience_max": int(st.session_state.get("jf_exp_max", 0)),
        "salary_min": int(st.session_state.get("jf_sal_min", 0)),
        "salary_max": int(st.session_state.get("jf_sal_max", 0)),
        "employment_type": st.session_state.get("jf_employment_type", "Full-time"),
        "hiring_manager": st.session_state.get("jf_hiring_manager", "").strip(),
        "deadline": st.session_state.get("jf_deadline", datetime.date.today()).isoformat(),
        "status": status,
        "description": st.session_state.get("jf_description", "").strip(),
        "responsibilities": [l.strip() for l in st.session_state.get("jf_responsibilities", "").split("\n") if l.strip()],
        "requirements": requirements,
        "preferred_skills": [l.strip() for l in st.session_state.get("jf_preferred_skills", "").split("\n") if l.strip()],
        "nice_to_have_skills": [],
        "benefits": [l.strip() for l in st.session_state.get("jf_benefits", "").split("\n") if l.strip()],
    }


def _apply_generated_jd(generated):
    st.session_state["jf_description"] = generated.get("description", "")
    st.session_state["jf_responsibilities"] = "\n".join(generated.get("responsibilities", []))
    if generated.get("requirements"):
        st.session_state["jf_required_skills"] = "\n".join(generated["requirements"])
    st.session_state["jf_preferred_skills"] = "\n".join(generated.get("preferred_skills", []))
    st.session_state["jf_benefits"] = "\n".join(generated.get("benefits", []))

# ══════════════════════════════════════════════════════════════════════════════
# JOB CREATE / EDIT FORM VIEW
# ══════════════════════════════════════════════════════════════════════════════
if st.session_state.job_action in ("create", "edit"):
    is_edit = st.session_state.job_action == "edit"
    job_id = st.session_state.selected_job_id

    job_data = {}
    if is_edit and job_id:
        job_data = api_client.get_job(job_id) or {}

    # ── Back button ──────────────────────────────────────────────────────────
    if st.button("← Back to Job Openings", key="back_btn_top"):
        go_to_list()

    st.markdown("<div style='height:4px;'></div>", unsafe_allow_html=True)

    # ── Hero Header ──────────────────────────────────────────────────────────
    action_label = "Edit Job Details" if is_edit else "Create New Job Listing"
    action_icon  = "✏️" if is_edit else "➕"
    action_sub   = f"Editing: {job_data.get('title', '')}" if is_edit else "Fill in the details below to post a new job opening."
    
    st.subheader(f"{action_icon} {action_label}")
    st.write(action_sub)

    # ── Initialize form state ─────────────────────────────────────────────
    form_key = f"{'edit' if is_edit else 'create'}_{job_id or 'new'}"
    if st.session_state.get("job_form_key") != form_key:
        _seed_job_form(job_data, st.session_state.generated_jd_data)
        st.session_state["job_form_key"] = form_key

    # ── Step 1: Basic inputs ──────────────────────────────────────────────
    st.markdown("""
    <div style="display:flex; align-items:center; gap:12px; margin:4px 0 18px 0;">
        <div style="background:#EEF2FF; border-radius:8px; padding:6px 14px;
                    font-size:0.8rem; color:#4F46E5; font-weight:700; white-space:nowrap;">
            Step 1 — Job details
        </div>
        <div style="flex:1; height:1px; background:linear-gradient(to right, #E0E7FF, transparent);"></div>
    </div>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns(3)
    with col1:
        st.text_input("Job Title *", key="jf_title", placeholder="e.g. Senior Python Engineer")
        st.text_input("Department *", key="jf_department", placeholder="e.g. Engineering")
    with col2:
        st.text_input("Location", key="jf_location", placeholder="e.g. Remote / New York")
        st.text_input("Hiring Manager", key="jf_hiring_manager", placeholder="e.g. Jane Smith")
    with col3:
        st.selectbox("Employment Type", ["Full-time", "Part-time", "Contract", "Internship"], key="jf_employment_type")
        st.date_input("Application Deadline", key="jf_deadline")

    comp_c1, comp_c2, comp_c3, comp_c4 = st.columns(4)
    with comp_c1:
        st.number_input("Min Experience (Yrs)", min_value=0, key="jf_exp_min")
    with comp_c2:
        st.number_input("Max Experience (Yrs)", min_value=0, key="jf_exp_max")
    with comp_c3:
        st.number_input("Min Salary ($)", step=5000, key="jf_sal_min")
    with comp_c4:
        st.number_input("Max Salary ($)", step=5000, key="jf_sal_max")

    st.text_area(
        "Required Skills (one per line) *",
        key="jf_required_skills",
        height=100,
        placeholder="Python\nFastAPI\nPostgreSQL",
    )

    st.markdown("<div style='height:12px;'></div>", unsafe_allow_html=True)

    # ── Step 2: Generate from all inputs ──────────────────────────────────
    if st.button("⚡ Generate Job Description with AI", type="primary", use_container_width=True, key="jf_generate_btn"):
        title = st.session_state.get("jf_title", "").strip()
        dept = st.session_state.get("jf_department", "").strip()
        reqs = [l.strip() for l in st.session_state.get("jf_required_skills", "").split("\n") if l.strip()]
        if not title or not dept:
            st.error("⚠️ Job Title and Department are required before generating.")
        elif not reqs:
            st.error("⚠️ Add at least one required skill before generating.")
        else:
            with st.spinner("AI is generating the job description… This may take up to 20 seconds…"):
                payload = _build_job_payload(job_data.get("status", "Active"))
                payload["description"] = ""
                payload["responsibilities"] = []
                payload["preferred_skills"] = []
                payload["benefits"] = []
                res = api_client.generate_jd(payload)
                if res:
                    st.session_state.generated_jd_data = res
                    _apply_generated_jd(res)
                    st.success("✅ Job description generated! Review below, then save.")
                    st.rerun()
                else:
                    st.error("AI generation failed. Ensure the backend and Ollama are running.")

    if st.session_state.generated_jd_data:
        st.info("AI content generated — review and edit below before saving.")

    # ── Step 3: Generated / editable content ──────────────────────────────
    st.markdown("""
    <div style="display:flex; align-items:center; gap:12px; margin:4px 0 18px 0;">
        <div style="background:#FFF7ED; border-radius:8px; padding:6px 14px;
                    font-size:0.8rem; color:#C2410C; font-weight:700; white-space:nowrap;">
            Step 2 — Job description &amp; content
        </div>
        <div style="flex:1; height:1px; background:linear-gradient(to right, #FED7AA, transparent);"></div>
    </div>
    """, unsafe_allow_html=True)

    st.text_area("Job Description Summary", key="jf_description", height=120,
                 placeholder="Summarize the role, team, and what success looks like…")

    content_c1, content_c2 = st.columns(2)
    with content_c1:
        st.text_area("Responsibilities (one per line)", key="jf_responsibilities", height=160)
    with content_c2:
        st.text_area("Preferred / Optional Skills (one per line)", key="jf_preferred_skills", height=160)

    st.text_area("Benefits Package (one per line)", key="jf_benefits", height=120)

    st.markdown("<div style='height:20px;'></div>", unsafe_allow_html=True)

    # ── Save / Cancel ───────────────────────────────────────────────────────
    btn_c1, btn_c2, _ = st.columns([1.6, 1.2, 5])
    with btn_c1:
        if st.button(
            "💾 Save Job Opening" if is_edit else "🚀 Create Job Opening",
            type="primary", use_container_width=True, key="jf_save_btn"
        ):
            payload = _build_job_payload(job_data.get("status", "Active"))
            if not payload["title"] or not payload["department"]:
                st.error("⚠️ Job Title and Department are required fields.")
            elif not payload["description"]:
                st.error("⚠️ Generate or enter a job description before saving.")
            else:
                if is_edit:
                    res = api_client.update_job(job_id, payload)
                    if res:
                        st.toast("Job opening updated!", icon="✅")
                        go_to_list()
                    else:
                        st.error("Failed to update job details.")
                else:
                    res = api_client.create_job(payload)
                    if res:
                        st.toast("Job opening created successfully!", icon="🎉")
                        go_to_list()
                    else:
                        st.error("Failed to create job.")
    with btn_c2:
        if st.button("✕ Cancel", use_container_width=True, key="jf_cancel_btn"):
            go_to_list()

# ══════════════════════════════════════════════════════════════════════════════
# JOB DETAILS PANEL VIEW
# ══════════════════════════════════════════════════════════════════════════════
elif st.session_state.job_action == "view" and st.session_state.selected_job_id:
    job = api_client.get_job(st.session_state.selected_job_id)
    if not job:
        st.error("Job details could not be found.")
        if st.button("Back to List"):
            go_to_list()
    else:
        st.markdown(f"""
        <div style="background-color: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 16px; padding: 24px; margin-bottom: 24px;">
            <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 12px;">
                <div>
                    <span class="badge-blue" style="margin-bottom: 8px;">{job.get('department')}</span>
                    <h2 style="font-size: 1.8rem; font-weight: 800; color: #0F172A; margin: 0;">{job.get('title')}</h2>
                    <p style="font-size: 0.9rem; color: #64748B; margin: 4px 0 0 0;"><i class="fa-solid fa-location-dot"></i> {job.get('location')} &bull; {job.get('employment_type')}</p>
                </div>
                <span class="badge-strong">{job.get('status')}</span>
            </div>
            <hr style="border-color: #E2E8F0; margin: 16px 0;">
            <div style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px;">
                <div>
                    <div style="font-size: 0.75rem; color: #94A3B8; text-transform: uppercase; font-weight: 700;">Hiring Manager</div>
                    <div style="font-weight: 600; color: #334155; font-size: 0.9rem; margin-top: 2px;">{job.get('hiring_manager') or 'N/A'}</div>
                </div>
                <div>
                    <div style="font-size: 0.75rem; color: #94A3B8; text-transform: uppercase; font-weight: 700;">Experience Required</div>
                    <div style="font-weight: 600; color: #334155; font-size: 0.9rem; margin-top: 2px;">{job.get('experience_min')} - {job.get('experience_max')} Yrs</div>
                </div>
                <div>
                    <div style="font-size: 0.75rem; color: #94A3B8; text-transform: uppercase; font-weight: 700;">Salary Package</div>
                    <div style="font-weight: 600; color: #334155; font-size: 0.9rem; margin-top: 2px;">${job.get('salary_min'):,} - ${job.get('salary_max'):,}</div>
                </div>
                <div>
                    <div style="font-size: 0.75rem; color: #94A3B8; text-transform: uppercase; font-weight: 700;">Deadline</div>
                    <div style="font-weight: 600; color: #334155; font-size: 0.9rem; margin-top: 2px;">{job.get('deadline') or 'No limit'}</div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        col_v1, col_v2 = st.columns(2)
        with col_v1:
            with st.container(border=True):
                st.markdown("#### <i class='fa-solid fa-file-lines' style='color:#6366F1; margin-right:8px;'></i> Description", unsafe_allow_html=True)
                st.write(job.get("description") or "No description summary provided.")

            st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)
            with st.container(border=True):
                st.markdown("#### <i class='fa-solid fa-list-check' style='color:#6366F1; margin-right:8px;'></i> Responsibilities", unsafe_allow_html=True)
                if job.get("responsibilities"):
                    for item in job["responsibilities"]:
                        st.markdown(f"- {item}")
                else:
                    st.write("No responsibilities provided.")

        with col_v2:
            with st.container(border=True):
                st.markdown("#### <i class='fa-solid fa-square-check' style='color:#6366F1; margin-right:8px;'></i> Required &amp; Optional Skills", unsafe_allow_html=True)
                reqs = job.get("requirements", [])
                opts = job.get("preferred_skills", [])
                if reqs:
                    st.markdown("**Required Skills:**")
                    for item in reqs:
                        st.markdown(f"- **{item}**")
                if opts:
                    st.markdown("<div style='height: 8px;'></div>", unsafe_allow_html=True)
                    st.markdown("**Optional Skills:**")
                    for item in opts:
                        st.markdown(f"- *{item}*")
                if not reqs and not opts:
                    st.write("No skills specified.")

            st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)
            with st.container(border=True):
                st.markdown("#### <i class='fa-solid fa-gift' style='color:#6366F1; margin-right:8px;'></i> Benefits Package", unsafe_allow_html=True)
                bens = job.get("benefits", [])
                if bens:
                    for item in bens:
                        st.markdown(f"- {item}")
                else:
                    st.write("No benefits package details logged.")

        st.markdown("<div style='height: 20px;'></div>", unsafe_allow_html=True)
        if st.button("← Back to Job Openings List", type="primary"):
            go_to_list()

# ══════════════════════════════════════════════════════════════════════════════
# JOBS LIST VIEW (DEFAULT)
# ══════════════════════════════════════════════════════════════════════════════
else:
    # 5-Column filter + Create button layout
    col_search, col_dept, col_loc, col_status, col_exp, col_btn = st.columns([2.5, 1.8, 1.8, 1.8, 1.8, 1.5])

    with col_search:
        search = st.text_input("Search Job openings", value="", placeholder="Search by title...", label_visibility="collapsed")
    with col_dept:
        department = st.selectbox("Department", ["All", "Engineering", "Sales", "Marketing", "HR", "Finance", "Analytics"], index=0, label_visibility="collapsed")
    with col_loc:
        location = st.selectbox("Location", ["All", "Remote", "On-site", "Hybrid"], index=0, label_visibility="collapsed")
    with col_status:
        status = st.selectbox("Status", ["All", "Active", "Paused", "Archived"], index=0, label_visibility="collapsed")
    with col_exp:
        exp_filter = st.selectbox("Experience Filter", ["All", "Junior (0-2 Yrs)", "Mid-level (3-5 Yrs)", "Senior (6+ Yrs)"], index=0, label_visibility="collapsed")
    with col_btn:
        if st.button("➕ Create Job", type="primary", use_container_width=True):
            st.session_state.job_action = "create"
            st.session_state.selected_job_id = None
            st.rerun()

    # Load list from backend
    all_jobs = api_client.get_jobs(search=search, department=department, status=status)

    # Filter Location locally
    if location != "All":
        all_jobs = [j for j in all_jobs if location.lower() in j.get("location", "").lower()]

    # Filter Experience locally
    if exp_filter != "All":
        if "Junior" in exp_filter:
            all_jobs = [j for j in all_jobs if j.get("experience_min", 0) <= 2]
        elif "Mid-level" in exp_filter:
            all_jobs = [j for j in all_jobs if 3 <= j.get("experience_min", 0) <= 5]
        elif "Senior" in exp_filter:
            all_jobs = [j for j in all_jobs if j.get("experience_min", 0) >= 6]

    if not all_jobs:
        st.markdown("<p style='text-align: center; color: #64748B; font-weight: 500; padding: 40px 0;'>No job openings found matching the criteria.</p>", unsafe_allow_html=True)
    else:
        for idx, job in enumerate(all_jobs):
            req_skills = job.get("requirements", [])
            skills_html = "".join([f'<span class="tag" style="background-color:#EEF2FF; color:#4F46E5; border:1px solid #E0E7FF;">{s}</span>' for s in req_skills[:4]])
            if len(req_skills) > 4:
                skills_html += f'<span class="tag" style="background-color: #EEF2FF; color: #4F46E5;">+{len(req_skills) - 4} more</span>'

            status_color = "#10B981" if job.get("status") == "Active" else ("#F59E0B" if job.get("status") == "Paused" else "#64748B")

            with st.container(border=True):
                col_c1, col_c2 = st.columns([3.2, 0.8])
                with col_c1:
                    st.markdown(f"""
                    <div>
                        <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 6px;">
                            <span style="font-weight: 800; font-size: 1.15rem; color: #0F172A;">{job.get('title')}</span>
                            <span class="badge-blue" style="background-color: {status_color}15; color: {status_color}; font-size: 0.72rem; padding: 2px 10px; border-radius:9999px;">{job.get('status')}</span>
                        </div>
                        <p style="font-size: 0.82rem; color: #64748B; margin: 0 0 10px 0;">
                            <strong>Dept:</strong> {job.get('department')} &bull; <strong>Location:</strong> {job.get('location')} &bull; <strong>Type:</strong> {job.get('employment_type')}
                        </p>
                        <div style="display: flex; gap: 18px; font-size: 0.8rem; color: #475569; margin-bottom: 10px;">
                            <span>Experience: {job.get('experience_min')} - {job.get('experience_max')} Yrs</span>
                            <span>Salary: ${job.get('salary_min'):,} - ${job.get('salary_max'):,}</span>
                            <span>Applications: {job.get('applications_count', 0)}</span>
                        </div>
                        <div style="margin-top: 8px;">{skills_html}</div>
                    </div>
                    """, unsafe_allow_html=True)

                with col_c2:
                    st.markdown("<div style='height: 4px;'></div>", unsafe_allow_html=True)
                    btn_row1 = st.columns(2)
                    with btn_row1[0]:
                        if st.button("View", key=f"v_btn_{job.get('id')}", use_container_width=True):
                            st.session_state.job_action = "view"
                            st.session_state.selected_job_id = job.get('id')
                            st.rerun()
                    with btn_row1[1]:
                        if st.button("Edit", key=f"e_btn_{job.get('id')}", use_container_width=True):
                            st.session_state.job_action = "edit"
                            st.session_state.selected_job_id = job.get('id')
                            st.rerun()

                    btn_row2 = st.columns(2)
                    with btn_row2[0]:
                        is_archived = job.get("status") == "Archived"
                        if st.button("Archive", key=f"a_btn_{job.get('id')}", use_container_width=True, disabled=is_archived):
                            res = api_client.archive_job(job.get('id'))
                            if res:
                                st.toast("Job opening archived.", icon="📥")
                                st.rerun()
                    with btn_row2[1]:
                        if st.button("Delete", key=f"d_btn_{job.get('id')}", use_container_width=True):
                            res = api_client.delete_job(job.get('id'))
                            if res:
                                st.toast("Job opening deleted.", icon="🗑️")
                                st.rerun()

                    if st.button("🪄 AI Generate JD", key=f"ai_jd_btn_{job.get('id')}", use_container_width=True, type="secondary"):
                        with st.spinner("AI is generating Job description details..."):
                            payload = {
                                "title": job.get("title"), "department": job.get("department"),
                                "location": job.get("location", "Remote"),
                                "experience_min": job.get("experience_min", 3),
                                "experience_max": job.get("experience_max", 8),
                                "salary_min": job.get("salary_min", 100000),
                                "salary_max": job.get("salary_max", 150000),
                                "employment_type": job.get("employment_type", "Full-time"),
                                "hiring_manager": job.get("hiring_manager", ""),
                                "deadline": job.get("deadline", ""),
                                "status": job.get("status", "Active"),
                                "description": job.get("description", ""),
                                "responsibilities": job.get("responsibilities", []),
                                "requirements": job.get("requirements", []),
                                "preferred_skills": job.get("preferred_skills", []),
                                "nice_to_have_skills": [],
                                "benefits": job.get("benefits", [])
                            }
                            res = api_client.generate_jd(payload)
                            if res:
                                payload.update(res)
                                api_client.update_job(job.get('id'), payload)
                                st.toast("Job description successfully updated via Ollama AI!", icon="🪄")
                                st.rerun()
                            else:
                                st.error("AI Generation failed. Check Ollama server.")
            st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)
