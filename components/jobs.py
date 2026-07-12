"""
components/jobs.py — HirePilot Job Management Page
====================================================
Renders the full Jobs page: list view, create/edit form, detail view.
Called from app.py when current_page == "Jobs".
"""

import datetime
import streamlit as st
from frontend.components import api_client


def render_jobs() -> None:
    """Entry point — dispatches to sub-view based on session state."""

    # ── State initialisation ──────────────────────────────────────────────
    for key, default in [
        ("job_action", "list"),
        ("selected_job_id", None),
        ("generated_jd_data", None),
    ]:
        if key not in st.session_state:
            st.session_state[key] = default

    # ── Page-level header ─────────────────────────────────────────────────
    st.markdown("""
    <h1 style="font-size:1.6rem;font-weight:800;color:#0F172A;margin:0 0 4px 0;">
        💼 Job Management
    </h1>
    <p style="font-size:0.85rem;color:#64748B;margin:0 0 20px 0;font-weight:500;">
        Manage and view your job openings
    </p>
    <hr style="margin:0 0 20px 0;border:none;border-top:1px solid #F1F5F9;">
    """, unsafe_allow_html=True)

    action = st.session_state.get("job_action", "list")

    if action in ("create", "edit"):
        _render_job_form()
    elif action == "view" and st.session_state.get("selected_job_id"):
        _render_job_detail()
    else:
        _render_job_list()


# ── Sub-views ────────────────────────────────────────────────────────────────

def _go_to_list():
    st.session_state["job_action"] = "list"
    st.session_state["selected_job_id"] = None
    st.session_state["generated_jd_data"] = None
    st.session_state.pop("job_form_key", None)
    st.rerun()


def _seed_job_form(job_data: dict, generated: dict | None = None) -> None:
    """Initialize keyed form widgets from existing job data and optional AI output."""
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


def _build_job_payload() -> dict:
    """Collect all form widget values into an API-ready payload."""
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
        "status": st.session_state.get("jf_status", "Active"),
        "description": st.session_state.get("jf_description", "").strip(),
        "responsibilities": [l.strip() for l in st.session_state.get("jf_responsibilities", "").split("\n") if l.strip()],
        "requirements": requirements,
        "preferred_skills": [l.strip() for l in st.session_state.get("jf_preferred_skills", "").split("\n") if l.strip()],
        "nice_to_have_skills": [],
        "benefits": [l.strip() for l in st.session_state.get("jf_benefits", "").split("\n") if l.strip()],
    }


def _apply_generated_jd(generated: dict) -> None:
    """Merge AI-generated content into the form widgets."""
    st.session_state["jf_description"] = generated.get("description", "")
    st.session_state["jf_responsibilities"] = "\n".join(generated.get("responsibilities", []))
    if generated.get("requirements"):
        st.session_state["jf_required_skills"] = "\n".join(generated["requirements"])
    st.session_state["jf_preferred_skills"] = "\n".join(generated.get("preferred_skills", []))
    st.session_state["jf_benefits"] = "\n".join(generated.get("benefits", []))


def _render_job_form():
    is_edit = st.session_state["job_action"] == "edit"
    job_id  = st.session_state.get("selected_job_id")
    job_data = {}
    if is_edit and job_id:
        job_data = api_client.get_job(job_id) or {}

    form_key = f"{'edit' if is_edit else 'create'}_{job_id or 'new'}"
    if st.session_state.get("job_form_key") != form_key:
        generated = st.session_state.get("generated_jd_data")
        _seed_job_form(job_data, generated)
        st.session_state["jf_status"] = job_data.get("status", "Active")
        st.session_state["job_form_key"] = form_key

    if st.button("← Back to Job Openings", key="job_form_back"):
        _go_to_list()

    st.markdown(f"### {'Edit Job Details' if is_edit else 'Create New Job Listing'}")
    st.markdown(
        "<p style='font-size:0.85rem;color:#64748B;margin:0 0 16px 0;'>"
        "Fill in all job details below, generate the description with AI, then save.</p>",
        unsafe_allow_html=True,
    )

    # ── Step 1: Basic inputs ──────────────────────────────────────────────
    st.markdown("**Step 1 — Job details**")
    c1, c2 = st.columns(2)
    with c1:
        st.text_input("Job Title *", key="jf_title", placeholder="e.g. Senior Python Engineer")
        st.text_input("Department *", key="jf_department", placeholder="e.g. Engineering")
        st.text_input("Location", key="jf_location", placeholder="e.g. Remote / New York")
        st.selectbox("Employment Type", ["Full-time", "Part-time", "Contract", "Internship"], key="jf_employment_type")
    with c2:
        st.text_input("Hiring Manager", key="jf_hiring_manager", placeholder="e.g. Jane Smith")
        st.date_input("Application Deadline", key="jf_deadline")
        st.number_input("Min Experience (Yrs)", min_value=0, key="jf_exp_min")
        st.number_input("Max Experience (Yrs)", min_value=0, key="jf_exp_max")

    sal1, sal2 = st.columns(2)
    with sal1:
        st.number_input("Min Salary ($)", step=5000, key="jf_sal_min")
    with sal2:
        st.number_input("Max Salary ($)", step=5000, key="jf_sal_max")

    st.text_area(
        "Required Skills (one per line) *",
        key="jf_required_skills",
        height=100,
        placeholder="Python\nFastAPI\nPostgreSQL",
    )

    st.markdown("<div style='height:8px;'></div>", unsafe_allow_html=True)

    # ── Step 2: Generate description from all inputs ───────────────────────
    if st.button("🪄 Generate Job Description with AI", type="primary", use_container_width=True, key="jf_generate_btn"):
        title = st.session_state.get("jf_title", "").strip()
        dept = st.session_state.get("jf_department", "").strip()
        reqs = [l.strip() for l in st.session_state.get("jf_required_skills", "").split("\n") if l.strip()]
        if not title or not dept:
            st.error("Job Title and Department are required before generating.")
        elif not reqs:
            st.error("Add at least one required skill before generating.")
        else:
            with st.spinner("AI is generating the job description… This may take up to 20 seconds…"):
                payload = _build_job_payload()
                payload["description"] = ""
                payload["responsibilities"] = []
                payload["preferred_skills"] = []
                payload["benefits"] = []
                res = api_client.generate_jd(payload)
                if res:
                    st.session_state["generated_jd_data"] = res
                    _apply_generated_jd(res)
                    st.success("Job description generated! Review the content below, then save.")
                    st.rerun()
                else:
                    st.error("AI generation failed. Ensure the backend and Ollama are running.")

    if st.session_state.get("generated_jd_data"):
        st.info("AI content generated — review and edit below before saving.")

    # ── Step 3: Generated / editable content ───────────────────────────────
    st.markdown("**Step 2 — Job description & content**")
    st.text_area("Job Description Summary", key="jf_description", height=120)
    cc1, cc2 = st.columns(2)
    with cc1:
        st.text_area("Responsibilities (one per line)", key="jf_responsibilities", height=140)
    with cc2:
        st.text_area("Preferred Skills (one per line)", key="jf_preferred_skills", height=140)
    st.text_area("Benefits Package (one per line)", key="jf_benefits", height=100)

    st.markdown("<div style='height:12px;'></div>", unsafe_allow_html=True)

    # ── Step 4: Save ───────────────────────────────────────────────────────
    sc1, sc2, _ = st.columns([1.5, 1.2, 6])
    with sc1:
        if st.button("💾 Save Job Opening", type="primary", use_container_width=True, key="jf_save_btn"):
            payload = _build_job_payload()
            if not payload["title"] or not payload["department"]:
                st.error("Title and Department are required.")
            elif not payload["description"]:
                st.error("Generate or enter a job description before saving.")
            else:
                if is_edit:
                    res = api_client.update_job(job_id, payload)
                    if res:
                        st.toast("Job opening updated!", icon="✅")
                        _go_to_list()
                    else:
                        st.error("Failed to update job.")
                else:
                    res = api_client.create_job(payload)
                    if res:
                        st.toast("Job opening created!", icon="🎉")
                        _go_to_list()
                    else:
                        st.error("Failed to create job.")
    with sc2:
        if st.button("Cancel", use_container_width=True, key="jf_cancel_btn"):
            _go_to_list()


def _render_job_detail():
    job = api_client.get_job(st.session_state["selected_job_id"])
    if not job:
        st.error("Job not found.")
        if st.button("Back to List"): _go_to_list()
        return

    st.markdown(f"""
    <div style="background:#F8FAFC;border:1px solid #E2E8F0;border-radius:16px;padding:24px;margin-bottom:24px;">
        <div style="display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:12px;">
            <div>
                <span class="badge-blue" style="margin-bottom:8px;">{job.get('department')}</span>
                <h2 style="font-size:1.8rem;font-weight:800;color:#0F172A;margin:0;">{job.get('title')}</h2>
                <p style="font-size:0.9rem;color:#64748B;margin:4px 0 0 0;">
                    <i class="fa-solid fa-location-dot"></i> {job.get('location')} • {job.get('employment_type')}
                </p>
            </div>
            <span class="badge-strong">{job.get('status')}</span>
        </div>
        <hr style="border-color:#E2E8F0;margin:16px 0;">
        <div style="display:grid;grid-template-columns:repeat(4,1fr);gap:16px;">
            <div>
                <div style="font-size:0.72rem;color:#94A3B8;text-transform:uppercase;font-weight:700;">Hiring Manager</div>
                <div style="font-weight:600;color:#334155;font-size:0.9rem;margin-top:2px;">{job.get('hiring_manager') or 'N/A'}</div>
            </div>
            <div>
                <div style="font-size:0.72rem;color:#94A3B8;text-transform:uppercase;font-weight:700;">Experience</div>
                <div style="font-weight:600;color:#334155;font-size:0.9rem;margin-top:2px;">{job.get('experience_min')} – {job.get('experience_max')} Yrs</div>
            </div>
            <div>
                <div style="font-size:0.72rem;color:#94A3B8;text-transform:uppercase;font-weight:700;">Salary</div>
                <div style="font-weight:600;color:#334155;font-size:0.9rem;margin-top:2px;">${job.get('salary_min'):,} – ${job.get('salary_max'):,}</div>
            </div>
            <div>
                <div style="font-size:0.72rem;color:#94A3B8;text-transform:uppercase;font-weight:700;">Deadline</div>
                <div style="font-weight:600;color:#334155;font-size:0.9rem;margin-top:2px;">{job.get('deadline') or 'No limit'}</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    cv1, cv2 = st.columns(2)
    with cv1:
        with st.container(border=True):
            st.markdown("#### <i class='fa-solid fa-file-lines' style='color:#6366F1;'></i> Description",
                        unsafe_allow_html=True)
            st.write(job.get("description") or "No description provided.")
        st.markdown("<div style='height:10px;'></div>", unsafe_allow_html=True)
        with st.container(border=True):
            st.markdown("#### <i class='fa-solid fa-list-check' style='color:#6366F1;'></i> Responsibilities",
                        unsafe_allow_html=True)
            for item in job.get("responsibilities", []):
                st.markdown(f"- {item}")

    with cv2:
        with st.container(border=True):
            st.markdown("#### <i class='fa-solid fa-square-check' style='color:#6366F1;'></i> Required & Optional Skills",
                        unsafe_allow_html=True)
            for item in job.get("requirements", []):
                st.markdown(f"- <span style='color:#312E81;font-weight:600;'>{item}</span>", unsafe_allow_html=True)
            for item in job.get("preferred_skills", []):
                st.markdown(f"- *{item}*")
        st.markdown("<div style='height:10px;'></div>", unsafe_allow_html=True)
        with st.container(border=True):
            st.markdown("#### <i class='fa-solid fa-gift' style='color:#6366F1;'></i> Benefits Package",
                        unsafe_allow_html=True)
            for item in job.get("benefits", []): st.markdown(f"- {item}")

    st.markdown("<div style='height:20px;'></div>", unsafe_allow_html=True)
    if st.button("← Back to Job Openings List", type="primary"):
        _go_to_list()


def _render_job_list():
    # ── Filters ───────────────────────────────────────────────────────────
    cs, cd, cl, cst, ce, cb = st.columns([2.5, 1.8, 1.8, 1.8, 1.8, 1.5])
    with cs:  search     = st.text_input("Search", value="", placeholder="Search by title…", label_visibility="collapsed")
    with cd:  department = st.selectbox("Dept",    ["All Departments","Engineering","Sales","Marketing","HR","Finance","Analytics"], label_visibility="collapsed")
    with cl:  location   = st.selectbox("Location",["All Locations","Remote","On-site","Hybrid"],                                  label_visibility="collapsed")
    with cst: status     = st.selectbox("Status",  ["All Statuses","Active","Paused","Archived"],                                  label_visibility="collapsed")
    with ce:  exp_f      = st.selectbox("Exp",     ["All Experience Levels","Junior (0-2 Yrs)","Mid-level (3-5 Yrs)","Senior (6+ Yrs)"],   label_visibility="collapsed")
    with cb:
        if st.button("➕ Create Job", type="primary", use_container_width=True):
            st.session_state["job_action"] = "create"
            st.session_state["selected_job_id"] = None
            st.rerun()

    # Map friendly filter labels back to API-compatible "All"
    dept_api = "All" if department == "All Departments" else department
    status_api = "All" if status == "All Statuses" else status

    all_jobs = api_client.get_jobs(search=search, department=dept_api, status=status_api)
    if location != "All Locations":
        all_jobs = [j for j in all_jobs if location.lower() in j.get("location","").lower()]
    if "Junior" in exp_f:
        all_jobs = [j for j in all_jobs if j.get("experience_min",0) <= 2]
    elif "Mid" in exp_f:
        all_jobs = [j for j in all_jobs if 3 <= j.get("experience_min",0) <= 5]
    elif "Senior" in exp_f:
        all_jobs = [j for j in all_jobs if j.get("experience_min",0) >= 6]

    if not all_jobs:
        st.markdown("<p style='text-align:center;color:#64748B;padding:40px 0;'>No job openings found.</p>",
                    unsafe_allow_html=True)
        return

    for job in all_jobs:
        req  = job.get("requirements", [])
        tags = "".join(f'<span class="tag">{s}</span>' for s in req[:4])
        if len(req) > 4: tags += f'<span class="tag">+{len(req)-4} more</span>'
        sc = {"Active": "#10B981", "Paused": "#F59E0B"}.get(job.get("status",""), "#64748B")

        with st.container(border=True):
            cc1, cc2 = st.columns([3.2, 0.8])
            with cc1:
                st.markdown(f"""
                <div>
                    <div style="display:flex;align-items:center;gap:10px;margin-bottom:6px;">
                        <span style="font-weight:800;font-size:1.1rem;color:#0F172A;">{job.get('title')}</span>
                        <span style="background:{sc}15;color:{sc};font-size:0.72rem;padding:2px 10px;
                                     border-radius:9999px;font-weight:600;">{job.get('status')}</span>
                    </div>
                    <p style="font-size:0.82rem;color:#64748B;margin:0 0 10px 0;">
                        <strong>Dept:</strong> {job.get('department')} •
                        <strong>Location:</strong> {job.get('location')} •
                        <strong>Type:</strong> {job.get('employment_type')}
                    </p>
                    <div style="display:flex;gap:18px;font-size:0.8rem;color:#475569;margin-bottom:10px;">
                        <span><i class="fa-solid fa-briefcase"></i> {job.get('experience_min')}–{job.get('experience_max')} Yrs</span>
                        <span><i class="fa-solid fa-money-bill-wave"></i> ${job.get('salary_min'):,}–${job.get('salary_max'):,}</span>
                        <span><i class="fa-solid fa-user-group"></i> {job.get('applications_count',0)} Applications</span>
                    </div>
                    <div style="margin-top:8px;">{tags}</div>
                </div>
                """, unsafe_allow_html=True)

            with cc2:
                st.markdown("<div style='height:4px;'></div>", unsafe_allow_html=True)
                r1 = st.columns(2)
                with r1[0]:
                    if st.button("View", key=f"v_{job['id']}", use_container_width=True):
                        st.session_state["job_action"] = "view"
                        st.session_state["selected_job_id"] = job["id"]
                        st.rerun()
                with r1[1]:
                    if st.button("Edit", key=f"e_{job['id']}", use_container_width=True):
                        st.session_state["job_action"] = "edit"
                        st.session_state["selected_job_id"] = job["id"]
                        st.rerun()
                r2 = st.columns(2)
                with r2[0]:
                    archived = job.get("status") == "Archived"
                    if st.button("Archive", key=f"a_{job['id']}", use_container_width=True, disabled=archived):
                        if api_client.archive_job(job["id"]): st.toast("Archived.", icon="📥"); st.rerun()
                with r2[1]:
                    if st.button("Delete", key=f"d_{job['id']}", use_container_width=True):
                        if api_client.delete_job(job["id"]): st.toast("Deleted.", icon="🗑️"); st.rerun()

                if st.button("🪄 AI Generate JD", key=f"ai_{job['id']}", use_container_width=True):
                    with st.spinner("Generating…"):
                        payload = {k: job.get(k, v) for k, v in [
                            ("title",""), ("department",""), ("location","Remote"),
                            ("experience_min",3), ("experience_max",8),
                            ("salary_min",100000), ("salary_max",150000),
                            ("employment_type","Full-time"), ("hiring_manager",""),
                            ("deadline",""), ("status","Active"), ("description",""),
                            ("responsibilities",[]), ("requirements",[]),
                            ("preferred_skills",[]), ("benefits",[]),
                        ]}
                        payload["nice_to_have_skills"] = []
                        res = api_client.generate_jd(payload)
                        if res:
                            payload.update(res)
                            api_client.update_job(job["id"], payload)
                            st.toast("JD updated via AI!", icon="🪄"); st.rerun()
                        else:
                            st.error("AI Generation failed.")

        st.markdown("<div style='height:10px;'></div>", unsafe_allow_html=True)
