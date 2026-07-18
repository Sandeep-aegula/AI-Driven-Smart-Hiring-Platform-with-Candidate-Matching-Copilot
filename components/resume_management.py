import time
import pandas as pd
import streamlit as st
from frontend.components import api_client
from frontend.services.cache import get_jobs_cached, invalidate_candidates

def render_resume_management():
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
    st.markdown("#### Upload Single Resume")
    uploaded_file = st.file_uploader("Choose a file (PDF, DOCX, TXT)", type=["pdf", "docx", "txt"], key="single_upload")
    
    if "single_candidate_id" not in st.session_state:
        st.session_state.single_candidate_id = None
        
    if uploaded_file and not st.session_state.single_candidate_id:
        if st.button("🪄 Upload & Analyze", type="primary"):
            with st.spinner("AI is analyzing the resume and computing a match score... (up to 30s)"):
                res = api_client.upload_single_resume(uploaded_file.getvalue(), uploaded_file.name, job_id)
                if res and "candidate_id" in res:
                    st.session_state.single_candidate_id = res["candidate_id"]
                    st.success("Successfully analyzed!")
                    st.rerun()
                else:
                    st.error("Failed to analyze resume.")
                    
    if st.session_state.single_candidate_id:
        _render_draft_preview(st.session_state.single_candidate_id)


def _render_bulk_upload(job_id: int):
    st.markdown("#### Bulk Upload")
    st.info("Upload multiple resumes at once. AI will process them concurrently in the background.")
    
    uploaded_files = st.file_uploader("Choose files (PDF, DOCX, TXT)", type=["pdf", "docx", "txt"], accept_multiple_files=True, key="bulk_upload")
    
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
    draft = api_client.preview_candidate_draft(candidate_id)
    if not draft:
        st.error("Could not load candidate draft.")
        return
        
    st.markdown("##### Review & Edit Extracted Details")
    parsed = draft.get("parsed_json", {})
    
    col1, col2 = st.columns(2)
    with col1:
        name = st.text_input("Full Name", value=parsed.get("name", ""))
        email = st.text_input("Email", value=parsed.get("email", ""))
        phone = st.text_input("Phone", value=parsed.get("phone", ""))
    with col2:
        github = st.text_input("GitHub", value=parsed.get("github", ""))
        linkedin = st.text_input("LinkedIn", value=parsed.get("linkedin", ""))
        match_score = st.number_input("Match Score", value=parsed.get("match_score", 0), min_value=0, max_value=100)
        
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
