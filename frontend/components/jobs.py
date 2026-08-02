"""
components/jobs.py — HirePilot Job Management Page
====================================================
Renders the full Jobs page: Manual Entry, AI Document Upload, and Paginated List.
"""
import math
import datetime
import pandas as pd
import streamlit as st
from frontend.components import api_client
from frontend.services.cache import get_jobs_cached, invalidate_jobs
from frontend.components.api_client import publish_job, pause_job, close_job
from frontend.components.file_uploader import file_uploader_simple

def render_jobs() -> None:
    st.markdown("""
    <h1 style="font-size:1.6rem;font-weight:800;color:#0F172A;margin:0 0 4px 0;">
        💼 Job Management
    </h1>
    <p style="font-size:0.85rem;color:#64748B;margin:0 0 20px 0;font-weight:500;">
        Create job postings manually or use AI to generate them from requisition documents.
    </p>
    """, unsafe_allow_html=True)
    
    # Define main tabs
    tab_list, tab_manual, tab_ai = st.tabs(["📋 Job Listings", "✍️ Manual Entry", "🪄 Upload Document (AI Generate)"])
    
    with tab_list:
        _render_job_list()
        
    with tab_manual:
        _render_manual_entry()
        
    with tab_ai:
        _render_ai_upload()

def _render_manual_entry():
    st.markdown("### Create Job Posting Manually")
    st.info("Fill in the basic details and required skills. Our AI will draft the full job description, responsibilities, and qualifications for you.")
    
    if "manual_job_state" not in st.session_state:
        st.session_state.manual_job_state = "input" # "input" or "review"
        st.session_state.manual_job_draft = {}
        st.session_state.manual_job_payload = {}
        
    if st.session_state.manual_job_state == "input":
        with st.form("manual_job_form"):
            # Group 1: Basic Info
            with st.expander("📝 Basic Information", expanded=True):
                col1, col2 = st.columns(2)
                with col1:
                    title = st.text_input("Job Title *", placeholder="e.g. Senior Software Engineer")
                    department = st.text_input("Department *", placeholder="e.g. Engineering")
                    location = st.text_input("Location", placeholder="e.g. San Francisco, CA")
                    employment_type = st.selectbox("Employment Type", ["Full-time", "Part-time", "Contract", "Internship"])
                with col2:
                    openings = st.number_input("Number of Openings", min_value=1, value=1)
                    work_mode = st.selectbox("Work Mode", ["Remote", "Hybrid", "On-site"])
                    hiring_deadline = st.date_input("Hiring Deadline")
                    experience_required = st.text_input("Experience Required", placeholder="e.g. 3-5 years")
                    salary_range = st.text_input("Salary Range", placeholder="e.g. ₹120k - ₹150k")
            
            # Group 2: Skills
            with st.expander("🛠️ Skills & Requirements", expanded=True):
                col3, col4 = st.columns(2)
                with col3:
                    required_skills = st.text_area("Required Skills (one per line) *", height=100)
                    technical_skills = st.text_area("Technical Skills (one per line)", height=100)
                with col4:
                    preferred_skills = st.text_area("Preferred Skills (one per line)", height=100)
                    soft_skills = st.text_area("Soft Skills (one per line)", height=100)
                    
            submitted = st.form_submit_button("🪄 Generate JD", type="primary")
            if submitted:
                if not title or not department or not required_skills:
                    st.error("Please fill in Job Title, Department, and Required Skills.")
                else:
                    st.session_state.manual_job_payload = {
                        "title": title,
                        "department": department,
                        "location": location,
                        "employment_type": employment_type,
                        "openings": openings,
                        "work_mode": work_mode,
                        "deadline": hiring_deadline.isoformat(),
                        "experience_required": experience_required,
                        "salary_range": salary_range,
                        "required_skills": [s.strip() for s in required_skills.split("\n") if s.strip()],
                        "preferred_skills": [s.strip() for s in preferred_skills.split("\n") if s.strip()],
                        "technical_skills": [s.strip() for s in technical_skills.split("\n") if s.strip()],
                        "soft_skills": [s.strip() for s in soft_skills.split("\n") if s.strip()]
                    }
                    
                    with st.spinner("AI is generating your job description..."):
                        # Send everything to the generate_jd endpoint
                        # The endpoint expects JobCreate schema
                        gen_payload = {**st.session_state.manual_job_payload, "description": "", "status": "Active"}
                        res = api_client.generate_jd(gen_payload)
                        
                        if res:
                            st.session_state.manual_job_draft = res
                            st.session_state.manual_job_state = "review"
                            st.rerun()
                        else:
                            st.error("Failed to generate JD. Please ensure backend and Ollama are running.")

    elif st.session_state.manual_job_state == "review":
        st.markdown("#### Review & Edit Generated Job Description")
        draft = st.session_state.manual_job_draft
        payload = st.session_state.manual_job_payload
        
        st.info(f"**{payload['title']}** - {payload['department']} ({payload['location']})")
        
        description = st.text_area("Job Description Summary *", value=draft.get("description", ""), height=150)
        
        col5, col6 = st.columns(2)
        with col5:
            # The AI endpoint returns "responsibilities"
            responsibilities_val = "\n".join(draft.get("responsibilities", []))
            responsibilities = st.text_area("Responsibilities (one per line)", value=responsibilities_val, height=150)
        with col6:
            # Use 'requirements' or 'qualifications' depending on the AI endpoint output
            reqs = draft.get("requirements", [])
            reqs.extend(draft.get("qualifications", [])) # In case it returned qualifications
            qualifications = st.text_area("Qualifications (one per line)", value="\n".join(reqs), height=150)
            
        c1, c2 = st.columns(2)
        with c1:
            if st.button("💾 Save Job Posting", type="primary", width="stretch"):
                if not description:
                    st.error("Job Description Summary cannot be empty.")
                else:
                    final_payload = {
                        **payload,
                        "description": description,
                        "responsibilities": [s.strip() for s in responsibilities.split("\n") if s.strip()],
                        "qualifications": [s.strip() for s in qualifications.split("\n") if s.strip()],
                        "status": "Active"
                    }
                    res = api_client.create_job(final_payload)
                    if res:
                        st.success("Job posting created successfully!")
                        invalidate_jobs()
                        st.session_state.manual_job_state = "input"
                        st.session_state.manual_job_payload = {}
                        st.session_state.manual_job_draft = {}
                    else:
                        st.error("Failed to save job posting.")
        with c2:
            if st.button("Cancel & Clear", width="stretch"):
                st.session_state.manual_job_state = "input"
                st.session_state.manual_job_payload = {}
                st.session_state.manual_job_draft = {}
                st.rerun()

def _render_ai_upload():
    st.markdown("### Upload Document (AI Generate)")
    st.info("Upload a job requisition or raw notes (PDF, DOCX, TXT) and let AI generate a polished job description.")
    
    uploaded_file = file_uploader_simple(
        label="Drag and drop document here",
        accepted_types=["pdf", "docx", "txt"],
        max_size_mb=200,
        key="ai_upload_document"
    )
    
    if "ai_draft_generated" not in st.session_state:
        st.session_state.ai_draft_generated = False
        st.session_state.ai_draft_data = None
        st.session_state.ai_raw_text = None
        
    if uploaded_file and not st.session_state.ai_draft_generated:
        if st.button("🪄 Generate with AI", type="primary"):
            with st.spinner("AI is analyzing document and drafting job description... (up to 30s)"):
                bytes_data = uploaded_file.getvalue()
                res = api_client.upload_and_generate_jd(bytes_data, uploaded_file.name)
                if res and "draft" in res:
                    st.session_state.ai_draft_generated = True
                    st.session_state.ai_draft_data = res["draft"]
                    st.session_state.ai_raw_text = res["raw_text"]
                    st.rerun()
                else:
                    st.error("Failed to generate job description. Ensure the backend and Ollama are running.")
                    
    if st.session_state.ai_draft_generated and st.session_state.ai_draft_data:
        st.markdown("#### Review & Edit Draft")
        draft = st.session_state.ai_draft_data
        
        # Meta info required for saving that AI might not generate well
        col1, col2 = st.columns(2)
        with col1:
            title = st.text_input("Job Title *", value="Generated Title (Please Edit)")
            department = st.text_input("Department *", value="Engineering")
            location = st.text_input("Location", value="Remote")
        with col2:
            employment_type = st.selectbox("Employment Type", ["Full-time", "Part-time", "Contract", "Internship"], key="ai_emp_type")
            openings = st.number_input("Number of Openings", min_value=1, value=1, key="ai_openings")
            work_mode = st.selectbox("Work Mode", ["Remote", "Hybrid", "On-site"], key="ai_work_mode")

        st.markdown("##### AI Extracted Content")
        new_draft = {
            "job_description": st.text_area("Job Description Summary *", value=draft.get("job_description", ""), height=150),
            "experience_required": st.text_input("Experience Required", value=draft.get("experience_required", "")),
            "education_requirements": st.text_input("Education Requirements", value=draft.get("education_requirements", "")),
            "required_skills": st.text_area("Required Skills (one per line) *", value="\n".join(draft.get("required_skills", [])), height=100),
            "preferred_skills": st.text_area("Preferred Skills (one per line)", value="\n".join(draft.get("preferred_skills", [])), height=100),
            "responsibilities": st.text_area("Responsibilities (one per line)", value="\n".join(draft.get("responsibilities", [])), height=100),
            "qualifications": st.text_area("Qualifications (one per line)", value="\n".join(draft.get("qualifications", [])), height=100)
        }
        
        c1, c2, c3 = st.columns(3)
        with c1:
            if st.button("💾 Save Job Posting", type="primary", width="stretch"):
                if not title or not department or not new_draft["required_skills"] or not new_draft["job_description"]:
                    st.error("Please fill in all required fields (*).")
                else:
                    payload = {
                        "title": title,
                        "department": department,
                        "location": location,
                        "employment_type": employment_type,
                        "openings": openings,
                        "work_mode": work_mode,
                        "experience_required": new_draft["experience_required"],
                        "required_skills": [s.strip() for s in new_draft["required_skills"].split("\n") if s.strip()],
                        "preferred_skills": [s.strip() for s in new_draft["preferred_skills"].split("\n") if s.strip()],
                        "description": new_draft["job_description"],
                        "responsibilities": [s.strip() for s in new_draft["responsibilities"].split("\n") if s.strip()],
                        "qualifications": [s.strip() for s in new_draft["qualifications"].split("\n") if s.strip()],
                        "status": "Active"
                    }
                    if api_client.create_job(payload):
                        st.success("Job posting created successfully!")
                        invalidate_jobs()
                        # Reset form
                        st.session_state.ai_draft_generated = False
                        st.session_state.ai_draft_data = None
                        st.session_state.ai_raw_text = None
                    else:
                        st.error("Failed to save job posting.")
        with c2:
            if st.button("🪄 Regenerate Draft", width="stretch"):
                with st.spinner("Regenerating..."):
                    # Current draft arrays need to be lists for JSON
                    req_payload = {
                        "job_description": new_draft["job_description"],
                        "experience_required": new_draft["experience_required"],
                        "education_requirements": new_draft["education_requirements"],
                        "required_skills": [s.strip() for s in new_draft["required_skills"].split("\n") if s.strip()],
                        "preferred_skills": [s.strip() for s in new_draft["preferred_skills"].split("\n") if s.strip()],
                        "responsibilities": [s.strip() for s in new_draft["responsibilities"].split("\n") if s.strip()],
                        "qualifications": [s.strip() for s in new_draft["qualifications"].split("\n") if s.strip()],
                    }
                    res = api_client.regenerate_jd(0, st.session_state.ai_raw_text, req_payload)
                    if res and "draft" in res:
                        st.session_state.ai_draft_data = res["draft"]
                        st.toast("Draft Regenerated!", icon="✅")
                        st.rerun()
                    else:
                        st.error("Failed to regenerate draft.")
        with c3:
            if st.button("Cancel & Clear", width="stretch"):
                st.session_state.ai_draft_generated = False
                st.session_state.ai_draft_data = None
                st.session_state.ai_raw_text = None
                st.rerun()


def _render_job_list():
    cs, cd, cl, cst = st.columns([2.5, 2, 2, 2])
    with cs:  search = st.text_input("Search", value="", placeholder="Search by title...", label_visibility="collapsed")
    with cd:  department = st.selectbox("Dept", ["All Departments","Engineering","Sales","Marketing","HR","Finance"], label_visibility="collapsed")
    with cl:  location = st.selectbox("Location", ["All Locations","Remote","On-site","Hybrid"], label_visibility="collapsed")
    with cst: status = st.selectbox("Status", ["All Statuses","draft","published","paused","closed"], label_visibility="collapsed")
    
    dept_api = "All" if department == "All Departments" else department
    status_api = "All" if status == "All Statuses" else status

    all_jobs = get_jobs_cached(search=search, department=dept_api, status=status_api)
    if location != "All Locations":
        all_jobs = [j for j in all_jobs if location.lower() in j.get("location","").lower()]

    if not all_jobs:
        st.info("No job openings found.")
        return

    # Flatten nested lists/dicts for dataframe display
    df_data = []
    for j in all_jobs:
        df_data.append({
            "ID": j.get("id"),
            "Status": "🟢 Published" if j.get("status") == "published" else ("🟡 Paused" if j.get("status") == "paused" else ("⚪ Closed" if j.get("status") == "closed" else "📝 Draft")),
            "Title": j.get("title"),
            "Department": j.get("department"),
            "Location": j.get("location"),
            "Type": j.get("employment_type"),
            "Exp": j.get("experience_required", f"{j.get('experience_min', 0)}+ Yrs"),
            "Openings": j.get("openings", 1),
            "Applicants": j.get("applications_count", 0),
            "Updated": j.get("updated_at", "")[:10]
        })
        
    df = pd.DataFrame(df_data)
    
    # Pagination
    ROWS_PER_PAGE = 25
    total_pages = math.ceil(len(df) / ROWS_PER_PAGE)
    
    if "job_page_num" not in st.session_state:
        st.session_state.job_page_num = 1
        
    st.session_state.job_page_num = max(1, min(st.session_state.job_page_num, total_pages))
    
    start_idx = (st.session_state.job_page_num - 1) * ROWS_PER_PAGE
    end_idx = start_idx + ROWS_PER_PAGE
    df_page = df.iloc[start_idx:end_idx]
    
    # Render dataframe
    st.dataframe(
        df_page,
        width="stretch",
        hide_index=True,
        column_config={
            "ID": st.column_config.NumberColumn(width="small"),
            "Status": st.column_config.TextColumn(width="small"),
            "Title": st.column_config.TextColumn(width="medium"),
            "Updated": st.column_config.TextColumn(width="small")
        }
    )
    
    # Pagination controls
    if total_pages > 1:
        pc1, pc2, pc3 = st.columns([1, 2, 1])
        with pc1:
            if st.button("⬅️ Previous", disabled=(st.session_state.job_page_num == 1)):
                st.session_state.job_page_num -= 1
                st.rerun()
        with pc2:
            st.markdown(f"<div style='text-align:center;padding-top:6px;'>Page {st.session_state.job_page_num} of {total_pages} (Total: {len(df)} jobs)</div>", unsafe_allow_html=True)
        with pc3:
            if st.button("Next ➡️", disabled=(st.session_state.job_page_num == total_pages)):
                st.session_state.job_page_num += 1
                st.rerun()

    st.markdown("---")
    st.markdown("### Manage Job Status")
    manage_cols = st.columns([2, 1, 1, 1])
    
    with manage_cols[0]:
        job_options = {j["id"]: f"{j['title']} (ID: {j['id']})" for j in all_jobs}
        selected_manage_job = st.selectbox("Select Job to Manage", options=list(job_options.keys()), format_func=lambda x: job_options[x])
        
    if selected_manage_job:
        job_to_manage = next((j for j in all_jobs if j["id"] == selected_manage_job), None)
        if job_to_manage:
            with manage_cols[1]:
                if st.button("🚀 Publish", width="stretch", disabled=(job_to_manage.get("status") == "published")):
                    publish_job(selected_manage_job)
                    st.toast("Job published successfully!")
                    st.rerun()
            with manage_cols[2]:
                if st.button("⏸️ Pause", width="stretch", disabled=(job_to_manage.get("status") in ["paused", "closed"])):
                    pause_job(selected_manage_job)
                    st.toast("Job paused successfully!")
                    st.rerun()
            with manage_cols[3]:
                if st.button("⛔ Close", width="stretch", disabled=(job_to_manage.get("status") == "closed")):
                    close_job(selected_manage_job)
                    st.toast("Job closed successfully!")
                    st.rerun()
