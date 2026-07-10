import streamlit as st
import os
import sys
import datetime

# Setup path to import api_client
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

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
    st.rerun()

# --- JOB CREATE / EDIT FORM VIEW ---
if st.session_state.job_action in ("create", "edit"):
    is_edit = st.session_state.job_action == "edit"
    job_id = st.session_state.selected_job_id

    job_data = {}
    if is_edit and job_id:
        job_data = api_client.get_job(job_id) or {}

    st.markdown(f"### { 'Edit Job Details' if is_edit else 'Create New Job Listing' }")
    
    # AI JD Prompt Helper Section
    with st.expander("🪄 AI Job Description Assistant", expanded=True):
        st.markdown("<p style='font-size: 0.85rem; color: #475569;'>Provide basic fields below and click Generate. Our local Ollama model will construct a complete job description, requirements list, and benefits package.</p>", unsafe_allow_html=True)
        ai_title = st.text_input("Role Title", value=job_data.get("title", ""), key="ai_title_input")
        ai_dept = st.text_input("Department", value=job_data.get("department", "Engineering"), key="ai_dept_input")
        ai_reqs = st.text_area("Required Skills (comma separated)", value=", ".join(job_data.get("requirements", [])) or "Python, SQL", key="ai_reqs_input")
        
        if st.button("Generate Job Description with Ollama AI", type="primary", use_container_width=True):
            with st.spinner("AI is generating Job Description details... This may take up to 20 seconds..."):
                payload = {
                    "title": ai_title,
                    "department": ai_dept,
                    "location": "Remote",
                    "experience_min": 3,
                    "experience_max": 8,
                    "salary_min": 100000,
                    "salary_max": 150000,
                    "employment_type": "Full-time",
                    "hiring_manager": "",
                    "deadline": "",
                    "status": "Active",
                    "description": "",
                    "responsibilities": [],
                    "requirements": [s.strip() for s in ai_reqs.split(",") if s.strip()],
                    "preferred_skills": [],
                    "nice_to_have_skills": [],
                    "benefits": []
                }
                res = api_client.generate_jd(payload)
                if res:
                    st.session_state.generated_jd_data = res
                    st.success("Successfully generated details! Pre-populated in form inputs below.")
                else:
                    st.error("Ollama generator failed to respond. Ensure your Ollama server is running locally.")

    # Form Fields source
    form_source = st.session_state.generated_jd_data if st.session_state.generated_jd_data else job_data

    with st.form("job_crud_form"):
        col1, col2 = st.columns(2)
        with col1:
            title = st.text_input("Job Title *", value=form_source.get("title", job_data.get("title", "")))
            department = st.text_input("Department *", value=form_source.get("department", job_data.get("department", "")))
            location = st.text_input("Location", value=form_source.get("location", job_data.get("location", "Remote")))
            emp_type = st.selectbox("Employment Type", ["Full-time", "Part-time", "Contract", "Internship"], index=["Full-time", "Part-time", "Contract", "Internship"].index(job_data.get("employment_type", "Full-time")))
            hiring_manager = st.text_input("Hiring Manager", value=job_data.get("hiring_manager", ""))
        
        with col2:
            exp_min = st.number_input("Minimum Experience Required (Yrs)", value=job_data.get("experience_min", 0), min_value=0)
            exp_max = st.number_input("Maximum Experience Required (Yrs)", value=job_data.get("experience_max", 0), min_value=0)
            sal_min = st.number_input("Minimum Salary ($)", value=job_data.get("salary_min", 0), step=5000)
            sal_max = st.number_input("Maximum Salary ($)", value=job_data.get("salary_max", 0), step=5000)
            deadline = st.date_input("Application Deadline", value=datetime.datetime.strptime(job_data.get("deadline"), "%Y-%m-%d").date() if job_data.get("deadline") else datetime.date.today() + datetime.timedelta(days=30))

        description = st.text_area("Job Description Summary", value=form_source.get("description", ""))
        
        responsibilities = st.text_area("Responsibilities (one per line)", value="\n".join(form_source.get("responsibilities", [])))
        requirements = st.text_area("Required Skills (one per line)", value="\n".join(form_source.get("requirements", [])))
        optional_skills = st.text_area("Optional Skills / Preferred Skills (one per line)", value="\n".join(form_source.get("preferred_skills", [])))
        benefits = st.text_area("Benefits Package (one per line)", value="\n".join(form_source.get("benefits", [])))

        submit_cols = st.columns([1.5, 1.5, 7])
        with submit_cols[0]:
            submitted = st.form_submit_button("Save Job opening", type="primary", use_container_width=True)
        with submit_cols[1]:
            cancel = st.form_submit_button("Cancel", use_container_width=True)

        if cancel:
            go_to_list()

        if submitted:
            if not title or not department:
                st.error("Title and Department are required.")
            else:
                payload = {
                    "title": title,
                    "department": department,
                    "location": location,
                    "experience_min": int(exp_min),
                    "experience_max": int(exp_max),
                    "salary_min": int(sal_min),
                    "salary_max": int(sal_max),
                    "employment_type": emp_type,
                    "hiring_manager": hiring_manager,
                    "deadline": deadline.isoformat(),
                    "status": job_data.get("status", "Active"),
                    "description": description,
                    "responsibilities": [line.strip() for line in responsibilities.split("\n") if line.strip()],
                    "requirements": [line.strip() for line in requirements.split("\n") if line.strip()],
                    "preferred_skills": [line.strip() for line in optional_skills.split("\n") if line.strip()],
                    "nice_to_have_skills": [],
                    "benefits": [line.strip() for line in benefits.split("\n") if line.strip()]
                }
                
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

# --- JOB DETAILS PANEL VIEW ---
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
                    <p style="font-size: 0.9rem; color: #64748B; margin: 4px 0 0 0;"><i class="fa-solid fa-location-dot"></i> {job.get('location')} • {job.get('employment_type')}</p>
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
                st.markdown("#### <i class='fa-solid fa-file-lines' style='color:#6366F1;'></i> Description", unsafe_allow_html=True)
                st.write(job.get("description") or "No description summary provided.")
            
            st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)
            with st.container(border=True):
                st.markdown("#### <i class='fa-solid fa-list-check' style='color:#6366F1;'></i> Responsibilities", unsafe_allow_html=True)
                if job.get("responsibilities"):
                    for item in job["responsibilities"]:
                        st.markdown(f"- {item}")
                else:
                    st.write("No responsibilities provided.")

        with col_v2:
            with st.container(border=True):
                st.markdown("#### <i class='fa-solid fa-square-check' style='color:#6366F1;'></i> Required & Optional Skills", unsafe_allow_html=True)
                reqs = job.get("requirements", [])
                opts = job.get("preferred_skills", [])
                if reqs:
                    st.markdown("**Required Skills:**")
                    for item in reqs:
                        st.markdown(f"- <span style='color:#312E81; font-weight:600;'>{item}</span>", unsafe_allow_html=True)
                if opts:
                    st.markdown("<div style='height: 8px;'></div>", unsafe_allow_html=True)
                    st.markdown("**Optional Skills:**")
                    for item in opts:
                        st.markdown(f"- *{item}*")
                if not reqs and not opts:
                    st.write("No skills specified.")
            
            st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)
            with st.container(border=True):
                st.markdown("#### <i class='fa-solid fa-gift' style='color:#6366F1;'></i> Benefits Package", unsafe_allow_html=True)
                bens = job.get("benefits", [])
                if bens:
                    for item in bens:
                        st.markdown(f"- {item}")
                else:
                    st.write("No benefits package details logged.")

        st.markdown("<div style='height: 20px;'></div>", unsafe_allow_html=True)
        if st.button("← Back to Job Openings List", type="primary"):
            go_to_list()

# --- JOBS LIST VIEW (DEFAULT) ---
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
        # Display Job Cards Grid
        for idx, job in enumerate(all_jobs):
            # Render skills badges
            req_skills = job.get("requirements", [])
            skills_html = "".join([f'<span class="tag" style="background-color:#EEF2FF; color:#4F46E5; border:1px solid #E0E7FF;">{s}</span>' for s in req_skills[:4]])
            if len(req_skills) > 4:
                skills_html += f'<span class="tag" style="background-color: #EEF2FF; color: #4F46E5;">+{len(req_skills) - 4} more</span>'

            # Status color mapping
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
                            <strong>Dept:</strong> {job.get('department')} • <strong>Location:</strong> {job.get('location')} • <strong>Type:</strong> {job.get('employment_type')}
                        </p>
                        <div style="display: flex; gap: 18px; font-size: 0.8rem; color: #475569; margin-bottom: 10px;">
                            <span><i class="fa-solid fa-briefcase"></i> Experience: {job.get('experience_min')} - {job.get('experience_max')} Yrs</span>
                            <span><i class="fa-solid fa-money-bill-wave"></i> Salary: ${job.get('salary_min'):,} - ${job.get('salary_max'):,}</span>
                            <span><i class="fa-solid fa-user-group"></i> Applications: {job.get('applications_count', 0)}</span>
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
                            # Convert dict to schema payload
                            payload = {
                                "title": job.get("title"),
                                "department": job.get("department"),
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
                                # Save back to json
                                payload.update(res)
                                api_client.update_job(job.get('id'), payload)
                                st.toast("Job description successfully updated via Ollama AI!", icon="🪄")
                                st.rerun()
                            else:
                                st.error("AI Generation failed. Check Ollama server.")
            st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)

# Sidebar footer metadata
with st.sidebar:
    st.markdown("""
    <div style="margin-top: 80px; padding: 16px 10px 0 10px; border-top: 1px solid #1E293B;">
        <div style="display: flex; align-items: center; gap: 10px; opacity: 0.85;">
            <div style="background-color: #1E293B; width: 28px; height: 28px; border-radius: 6px; display: flex; align-items: center; justify-content: center; font-size: 12px; color: #6366F1;">
                <i class="fa-solid fa-rocket"></i>
            </div>
            <div>
                <div style="font-weight: 700; color: #E2E8F0; font-size: 0.78rem;">HirePilot v1.2</div>
                <div style="font-size: 0.65rem; color: #64748B;">Plan: Enterprise</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
