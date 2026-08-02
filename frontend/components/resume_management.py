import time
import pandas as pd
import streamlit as st
from frontend.components import api_client
from frontend.services.cache import get_jobs_cached, invalidate_candidates
from frontend.components.file_uploader import file_uploader_simple

# Inject custom CSS for better alignment
_RESUME_CSS = """
<style>
/* File uploader styling */
.stFileUploader > div > div {
    border: 2px dashed #E2E8F0 !important;
    border-radius: 12px !important;
    padding: 32px !important;
    background-color: #FAFAFA !important;
    transition: all 0.2s ease !important;
    min-height: 120px !important;
}
.stFileUploader > div > div:hover {
    border-color: #6366F1 !important;
    background-color: #F5F3FF !important;
}
.stFileUploader > div > div[data-drag-active="true"] {
    border-color: #6366F1 !important;
    background-color: #EEF2FF !important;
}

/* Text area styling */
.stTextArea textarea {
    border: 2px solid #E2E8F0 !important;
    border-radius: 12px !important;
    padding: 16px !important;
    font-family: 'Plus Jakarta Sans', sans-serif !important;
    font-size: 14px !important;
    line-height: 1.6 !important;
    background-color: #FFFFFF !important;
    color: #0F172A !important;
    min-height: 200px !important;
}
.stTextArea textarea:focus {
    border-color: #6366F1 !important;
    box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.15) !important;
    outline: none !important;
}
.stTextArea textarea::placeholder {
    color: #94A3B8 !important;
    font-style: italic !important;
}

/* Button styling */
.stButton > button[kind="primary"] {
    background: linear-gradient(135deg, #6366F1 0%, #4F46E5 100%) !important;
    border: none !important;
    border-radius: 10px !important;
    padding: 12px 24px !important;
    font-weight: 600 !important;
    font-size: 14px !important;
    transition: all 0.2s ease !important;
}
.stButton > button[kind="primary"]:hover {
    transform: translateY(-1px) !important;
    box-shadow: 0 4px 12px rgba(99, 102, 241, 0.35) !important;
}
.stButton > button:disabled {
    opacity: 0.5 !important;
    cursor: not-allowed !important;
}

/* Selectbox styling */
.stSelectbox > div > div {
    border: 1px solid #E2E8F0 !important;
    border-radius: 10px !important;
    background-color: #FFFFFF !important;
}
.stSelectbox > div > div:focus-within {
    border-color: #6366F1 !important;
    box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.15) !important;
}

/* Container borders */
.stContainer > div[data-testid="stVerticalBlockBorderWrapper"] {
    border: 1px solid #E2E8F0 !important;
    border-radius: 16px !important;
    box-shadow: 0 1px 3px rgba(0,0,0,0.02) !important;
}

/* Tabs styling */
.stTabs [data-baseweb="tab-list"] {
    gap: 8px !important;
    background-color: transparent !important;
}
.stTabs [data-baseweb="tab"] {
    background-color: #F8FAFC !important;
    border-radius: 10px !important;
    padding: 10px 20px !important;
    font-weight: 600 !important;
}
.stTabs [aria-selected="true"] {
    background-color: #EEF2FF !important;
    color: #4F46E5 !important;
}

/* Section headers */
h3 {
    font-weight: 700 !important;
    color: #0F172A !important;
}
h4 {
    font-weight: 700 !important;
    color: #0F172A !important;
}
h5 {
    font-weight: 700 !important;
    color: #0F172A !important;
}

</style>
"""

def render_resume_management():
    st.markdown(_RESUME_CSS, unsafe_allow_html=True)
    
    st.markdown("""
    <h1 style="font-size:1.6rem;font-weight:800;color:#0F172A;margin:0 0 4px 0;">
        📄 Resume Management & AI Parsing
    </h1>
    <p style="font-size:0.85rem;color:#64748B;margin:0 0 20px 0;font-weight:500;">
        Upload resumes, extract structured data, and automatically score candidates against open roles.
    </p>
    """, unsafe_allow_html=True)
    
    # Global Job Selector
    jobs = get_jobs_cached()
    active_jobs = [j for j in jobs if j.get("status") == "Active"]
    job_options = {j["id"]: f"{j['title']} ({j['department']})" for j in active_jobs}
    
    if not job_options:
        st.warning("You must have at least one Active Job opening to score resumes against.")
        return
        
    st.markdown("### 1. Select Target Job")
    selected_job_id = st.selectbox(
        "Which role are these resumes for?",
        options=list(job_options.keys()),
        format_func=lambda x: job_options[x]
    )
    
    tab_single, tab_bulk, tab_candidates = st.tabs(["Upload Single Resume", "Bulk Upload", "Parsed Candidates"])
    
    with tab_single:
        _render_single_upload(selected_job_id)
        
    with tab_bulk:
        _render_bulk_upload(selected_job_id)
        
    with tab_candidates:
        _render_candidates_grid()


def _render_single_upload(job_id: int):
    st.markdown("### 2. Upload Single Resume")
    
    # Sub-tabs for input method
    input_method_file, input_method_text = st.tabs([
        "📁 Upload File", "📋 Paste Text"
    ])
    
    if "single_candidate_id" not in st.session_state:
        st.session_state.single_candidate_id = None
    if "single_draft_data" not in st.session_state:
        st.session_state.single_draft_data = None
    
    with input_method_file:
        with st.container(border=True):
            st.subheader("Resume Upload")
            
            uploaded_file = file_uploader_simple(
                label="Drag and drop resume here",
                accepted_types=["pdf", "docx", "txt"],
                max_size_mb=200,
                key="single_upload"
            )
            
            st.caption("Supported formats: PDF, DOCX, TXT • Maximum file size: 200 MB")
            
            if uploaded_file:
                st.markdown(f"""
                <div style='padding: 10px 14px; background-color: #EEF2FF; border-radius: 10px; border: 1px solid #C7D2FE; margin: 12px 0;'>
                    <div style='font-weight: 600; color: #4F46E5; font-size: 0.88rem;'>📄 {uploaded_file.name}</div>
                    <div style='font-size: 0.78rem; color: #64748B; margin-top: 2px;'>{uploaded_file.size / 1024:.1f} KB</div>
                </div>
                """, unsafe_allow_html=True)
                
                if not st.session_state.single_candidate_id:
                    if st.button("🪄 Upload & Analyze", type="primary", width="stretch", key="analyze_file_btn"):
                        with st.spinner("AI is analyzing the resume and computing a match score... (up to 30s)"):
                            res = api_client.upload_single_resume(uploaded_file.getvalue(), uploaded_file.name, job_id)
                            if res and "candidate_id" in res:
                                st.session_state.single_candidate_id = res["candidate_id"]
                                st.session_state.single_draft_data = res  # Store the full response
                                st.success("Successfully analyzed!")
                                st.rerun()
                            else:
                                st.error("Failed to analyze resume.")
    
    with input_method_text:
        with st.container(border=True):
            st.subheader("Paste Resume Text")
            
            pasted_text = st.text_area(
                "Resume text",
                placeholder="Paste the full resume text here...\n\nExample:\nJohn Doe\njohn.doe@email.com\n+1-555-0123\n\nSKILLS\nPython, FastAPI, PostgreSQL, Docker, AWS\n\nEXPERIENCE\nSenior Developer at TechCorp (2020-Present)\n- Built scalable APIs serving 1M+ users\n- Led team of 5 engineers\n\nEDUCATION\nBS Computer Science, MIT (2018)",
                height=280,
                label_visibility="visible",
                key="single_pasted_text"
            )
            
            st.caption("Paste the complete resume text including contact info, skills, experience, and education")
            
            has_text = bool(pasted_text.strip())
            
            if st.button("🪄 Parse & Analyze Text", type="primary", width="stretch", disabled=not has_text, key="analyze_text_btn"):
                with st.spinner("AI is parsing the resume text and computing a match score... (up to 30s)"):
                    res = api_client.parse_resume_text(pasted_text, "pasted_resume.txt")
                    if res and "candidate_id" in res:
                        st.session_state.single_candidate_id = res["candidate_id"]
                        st.session_state.single_draft_data = res  # Store the full response
                        st.success("Successfully analyzed!")
                        st.rerun()
                    else:
                        st.error("Failed to analyze resume text.")
            
            if not has_text:
                st.caption("👆 Paste resume text above to enable parsing")
                    
    # Show draft preview if we have a candidate ID
    if st.session_state.single_candidate_id:
        _render_draft_preview(st.session_state.single_candidate_id)


def _render_bulk_upload(job_id: int):
    st.markdown("#### Bulk Upload")
    st.info("Upload multiple resumes at once. AI will process them concurrently in the background.")
    
    uploaded_files = file_uploader_simple(
        label="Drag and drop multiple resumes here",
        accepted_types=["pdf", "docx", "txt"],
        max_size_mb=200,
        key="bulk_upload",
        multiple=True
    )
    
    if "batch_id" not in st.session_state:
        st.session_state.batch_id = None
        
    if uploaded_files and not st.session_state.batch_id:
        if st.button("🪄 Upload & Analyze All", type="primary"):
            files_list = [(f.name, f.getvalue()) for f in uploaded_files]
            res = api_client.start_bulk_upload(files_list, job_id)
            if res and "batch_id" in res:
                st.session_state.batch_id = res["batch_id"]
                st.rerun()
            else:
                st.error("Failed to start bulk upload.")
                
    if st.session_state.batch_id:
        batch_id = st.session_state.batch_id
        st.markdown("##### Processing Status")
        
        status = api_client.poll_batch_status(batch_id)
        if status:
            total = status["total_files"]
            processed = status["processed_files"]
            prog = processed / total if total > 0 else 0
            
            st.progress(prog, text=f"Processed {processed} of {total} resumes...")
            st.write(f"✅ Successful: {status['successful']} | ❌ Failed: {status['failed']}")
            
            if status["is_complete"]:
                st.success("Bulk upload complete! Check the 'Parsed Candidates' tab.")
                if st.button("Clear & Upload More"):
                    st.session_state.batch_id = None
                    invalidate_candidates()
                    st.rerun()
            else:
                time.sleep(2)
                st.rerun()


def _render_draft_preview(candidate_id: int):
    # Use stored draft data if available, otherwise fetch from API
    if st.session_state.get("single_draft_data") and st.session_state.single_draft_data.get("candidate_id") == candidate_id:
        draft = st.session_state.single_draft_data
    else:
        draft = api_client.preview_candidate_draft(candidate_id)
    
    if not draft:
        st.error("Could not load candidate draft.")
        return
        
    st.markdown("##### Review & Edit Extracted Details")
    parsed = draft.get("parsed_json", {})
    
    # Identity section
    col1, col2 = st.columns(2)
    with col1:
        name = st.text_input("Full Name", value=parsed.get("name", ""))
        email = st.text_input("Email", value=parsed.get("email", ""))
        phone = st.text_input("Phone", value=parsed.get("phone", ""))
    with col2:
        github = st.text_input("GitHub", value=parsed.get("github", ""))
        linkedin = st.text_input("LinkedIn", value=parsed.get("linkedin", ""))
        match_score = st.number_input("Match Score", value=parsed.get("match_score", 0), min_value=0, max_value=100)
        
    # Skills section
    skills = parsed.get("skills", [])
    if skills:
        st.markdown("**Skills**")
        st.pills(
            "Skills",
            skills,
            selection_mode="multi",
            default=skills,
            disabled=True,
            label_visibility="collapsed",
            width="stretch",
            key=f"draft_skills_{candidate_id}",
        )
    
    # Experience section
    experience = parsed.get("experience", [])
    if experience:
        st.markdown("**Experience**")
        for exp in experience:
            st.markdown(f"- {exp}")
    
    # Education section
    education = parsed.get("education", [])
    if education:
        st.markdown("**Education**")
        for edu in education:
            st.markdown(f"- {edu}")
        
    summary = st.text_area("AI Resume Summary", value=parsed.get("resume_summary", ""), height=100)
    
    if st.button("💾 Confirm & Save Profile", type="primary"):
        payload = {
            "name": name,
            "email": email,
            "phone": phone,
            "github": github,
            "linkedin": linkedin,
            "match_score": match_score,
            "summary": summary,
            "status": "Applied"
        }
        if api_client.update_candidate(candidate_id, payload):
            st.success("Candidate profile saved!")
            st.session_state.single_candidate_id = None
            st.session_state.single_draft_data = None
            invalidate_candidates()
            time.sleep(1)
            st.rerun()
        else:
            st.error("Failed to save candidate profile.")


def _render_candidates_grid():
    candidates = api_client.get_candidates()
    if not candidates:
        st.info("No candidates found.")
        return
        
    # Sort by match score descending
    candidates = sorted(candidates, key=lambda x: x.get("match_score", 0), reverse=True)
    
    for c in candidates:
        score = c.get("match_score", 0)
        color = "#10B981" if score >= 80 else ("#F59E0B" if score >= 50 else "#EF4444")
        rec = c.get("hire_recommendation", "N/A")
        
        with st.container(border=True):
            col1, col2, col3 = st.columns([3, 1, 1])
            with col1:
                st.markdown(f"**{c.get('name')}** - {c.get('email')}")
                st.markdown(f"<span style='color:#64748B;font-size:0.85rem;'>{c.get('summary', '')[:150]}...</span>", unsafe_allow_html=True)
            with col2:
                st.markdown(f"**Match Score**: <span style='color:{color};font-weight:bold;font-size:1.2rem;'>{score}%</span>", unsafe_allow_html=True)
            with col3:
                st.markdown(f"**AI Rec**: {rec}")
                if st.button("View Full Profile", key=f"view_{c['id']}"):
                    st.toast("Profile view placeholder (See Module 4)", icon="ℹ️")
