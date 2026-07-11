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
    st.rerun()


def _render_job_form():
    is_edit = st.session_state["job_action"] == "edit"
    job_id  = st.session_state.get("selected_job_id")
    job_data = {}
    if is_edit and job_id:
        job_data = api_client.get_job(job_id) or {}

    st.markdown(f"### {'Edit Job Details' if is_edit else 'Create New Job Listing'}")

    with st.expander("🪄 AI Job Description Assistant", expanded=True):
        st.markdown("<p style='font-size:0.85rem;color:#475569;'>Provide basic fields below and click Generate. "
                    "Our local Ollama model will construct a complete job description.</p>",
                    unsafe_allow_html=True)
        ai_title = st.text_input("Role Title",   value=job_data.get("title", ""), key="ai_title_input")
        ai_dept  = st.text_input("Department",   value=job_data.get("department", "Engineering"), key="ai_dept_input")
        ai_reqs  = st.text_area("Required Skills (comma separated)",
                                value=", ".join(job_data.get("requirements", [])) or "Python, SQL",
                                key="ai_reqs_input")
        if st.button("Generate Job Description with Ollama AI", type="primary", use_container_width=True):
            with st.spinner("AI is generating Job Description details… This may take up to 20 seconds…"):
                payload = {
                    "title": ai_title, "department": ai_dept, "location": "Remote",
                    "experience_min": 3, "experience_max": 8,
                    "salary_min": 100000, "salary_max": 150000,
                    "employment_type": "Full-time", "hiring_manager": "",
                    "deadline": "", "status": "Active", "description": "",
                    "responsibilities": [], "requirements": [s.strip() for s in ai_reqs.split(",") if s.strip()],
                    "preferred_skills": [], "nice_to_have_skills": [], "benefits": [],
                }
                res = api_client.generate_jd(payload)
                if res:
                    st.session_state["generated_jd_data"] = res
                    st.success("Successfully generated! Pre-populated in form inputs below.")
                else:
                    st.error("Ollama generator failed. Ensure your Ollama server is running locally.")

    src = st.session_state.get("generated_jd_data") or job_data

    with st.form("job_crud_form"):
        c1, c2 = st.columns(2)
        with c1:
            title          = st.text_input("Job Title *",     value=src.get("title", job_data.get("title", "")))
            department     = st.text_input("Department *",    value=src.get("department", job_data.get("department", "")))
            location       = st.text_input("Location",        value=src.get("location", job_data.get("location", "Remote")))
            emp_types      = ["Full-time", "Part-time", "Contract", "Internship"]
            emp_type       = st.selectbox("Employment Type",  emp_types,
                                          index=emp_types.index(job_data.get("employment_type", "Full-time")))
            hiring_manager = st.text_input("Hiring Manager",  value=job_data.get("hiring_manager", ""))
        with c2:
            exp_min  = st.number_input("Min Experience (Yrs)",  value=job_data.get("experience_min", 0),  min_value=0)
            exp_max  = st.number_input("Max Experience (Yrs)",  value=job_data.get("experience_max", 0),  min_value=0)
            sal_min  = st.number_input("Min Salary ($)",         value=job_data.get("salary_min", 0),      step=5000)
            sal_max  = st.number_input("Max Salary ($)",         value=job_data.get("salary_max", 0),      step=5000)
            dl_raw   = job_data.get("deadline")
            deadline = st.date_input("Application Deadline",
                                     value=datetime.datetime.strptime(dl_raw, "%Y-%m-%d").date()
                                     if dl_raw else datetime.date.today() + datetime.timedelta(days=30))

        description      = st.text_area("Job Description Summary",       value=src.get("description", ""))
        responsibilities = st.text_area("Responsibilities (one per line)",value="\n".join(src.get("responsibilities", [])))
        requirements     = st.text_area("Required Skills (one per line)", value="\n".join(src.get("requirements", [])))
        opt_skills       = st.text_area("Preferred Skills (one per line)",value="\n".join(src.get("preferred_skills", [])))
        benefits         = st.text_area("Benefits Package (one per line)",value="\n".join(src.get("benefits", [])))

        sc = st.columns([1.5, 1.5, 7])
        with sc[0]: submitted = st.form_submit_button("Save Job Opening", type="primary", use_container_width=True)
        with sc[1]: cancel    = st.form_submit_button("Cancel",           use_container_width=True)

        if cancel:
            _go_to_list()

        if submitted:
            if not title or not department:
                st.error("Title and Department are required.")
            else:
                payload = {
                    "title": title, "department": department, "location": location,
                    "experience_min": int(exp_min), "experience_max": int(exp_max),
                    "salary_min": int(sal_min),     "salary_max": int(sal_max),
                    "employment_type": emp_type,    "hiring_manager": hiring_manager,
                    "deadline": deadline.isoformat(),
                    "status": job_data.get("status", "Active"),
                    "description": description,
                    "responsibilities": [l.strip() for l in responsibilities.split("\n") if l.strip()],
                    "requirements":     [l.strip() for l in requirements.split("\n")     if l.strip()],
                    "preferred_skills": [l.strip() for l in opt_skills.split("\n")       if l.strip()],
                    "nice_to_have_skills": [], "benefits": [l.strip() for l in benefits.split("\n") if l.strip()],
                }
                if is_edit:
                    res = api_client.update_job(job_id, payload)
                    if res: st.toast("Job opening updated!", icon="✅"); _go_to_list()
                    else:   st.error("Failed to update job.")
                else:
                    res = api_client.create_job(payload)
                    if res: st.toast("Job opening created!", icon="🎉"); _go_to_list()
                    else:   st.error("Failed to create job.")


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
    with cd:  department = st.selectbox("Dept",    ["All","Engineering","Sales","Marketing","HR","Finance","Analytics"], label_visibility="collapsed")
    with cl:  location   = st.selectbox("Location",["All","Remote","On-site","Hybrid"],                                  label_visibility="collapsed")
    with cst: status     = st.selectbox("Status",  ["All","Active","Paused","Archived"],                                  label_visibility="collapsed")
    with ce:  exp_f      = st.selectbox("Exp",     ["All","Junior (0-2 Yrs)","Mid-level (3-5 Yrs)","Senior (6+ Yrs)"],   label_visibility="collapsed")
    with cb:
        if st.button("➕ Create Job", type="primary", use_container_width=True):
            st.session_state["job_action"] = "create"
            st.session_state["selected_job_id"] = None
            st.rerun()

    all_jobs = api_client.get_jobs(search=search, department=department, status=status)
    if location != "All":
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
