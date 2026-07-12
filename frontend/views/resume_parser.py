import streamlit as st
import os
import sys
import shutil

# Setup path to import api_client
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
project_root = os.path.dirname(parent_dir)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from frontend.components import api_client
from frontend.services.cache import get_uploads_cached, invalidate_uploads
from frontend.services.app_state import AppState
from frontend.components.page_utils import setup_page, render_sidebar_footer

# Page Config
st.set_page_config(
    page_title="Resume Parser - HirePilot",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="expanded"
)

setup_page("Resume Parser", "Upload and parse candidate resumes", page_key=__file__)

# State initialization
if "selected_resume_id" not in st.session_state:
    st.session_state.selected_resume_id = None

UPLOAD_DIR = os.path.join(parent_dir, "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

# Load upload history
uploads_list = api_client.get_upload_history()

# If nothing selected, select first item from history as default
if st.session_state.selected_resume_id is None and uploads_list:
    st.session_state.selected_resume_id = uploads_list[0]["id"]

# --- TOP SECTION: UPLOADER & UPLOAD HISTORY ---
col_top_left, col_top_right = st.columns([1.1, 0.9])

with col_top_left:
    with st.container(border=True):
        st.markdown("#### <i class='fa-solid fa-cloud-arrow-up' style='color:#6366F1;'></i> Drag & Drop Resumes", unsafe_allow_html=True)
        st.markdown("<p style='font-size: 0.82rem; color: #64748B; margin-bottom: 15px;'>Support PDF, DOCX • Bulk Upload enabled</p>", unsafe_allow_html=True)
        
        uploaded_files = st.file_uploader(
            "Select files",
            type=["pdf", "docx"],
            accept_multiple_files=True,
            label_visibility="collapsed",
            key="bulk_resume_file_uploader"
        )
        
        if uploaded_files:
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            if st.button("Parse Resumes with Ollama AI", type="primary", use_container_width=True):
                success_count = 0
                for idx, file in enumerate(uploaded_files):
                    status_text.markdown(f"AI parsing: *{file.name}* (Ollama qwen2.5-coder)...")

                    # Read bytes from the Streamlit UploadedFile
                    file_bytes = file.read()

                    # Also save a local copy for preview
                    file_path = os.path.join(UPLOAD_DIR, file.name)
                    with open(file_path, "wb") as f:
                        f.write(file_bytes)

                    # Upload + parse via backend
                    res = api_client.upload_resume(file_bytes, file.name)
                    if res:
                        success_count += 1
                        st.toast(f"Successfully parsed {file.name}!", icon="✅")
                    else:
                        st.error(f"Failed to parse resume: {file.name}")

                    progress = int(((idx + 1) / len(uploaded_files)) * 100)
                    progress_bar.progress(progress)

                status_text.markdown(f"### 🎉 Successfully parsed {success_count} / {len(uploaded_files)} resume(s)!")
                st.session_state.selected_resume_id = None  # Force reload latest
                st.rerun()

with col_top_right:
    with st.container(border=True):
        st.markdown("#### <i class='fa-solid fa-clock-rotate-left' style='color:#6366F1;'></i> Upload History", unsafe_allow_html=True)
        st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)
        
        if uploads_list:
            uploads_html_container = "<div style='display: flex; flex-direction: column; gap: 8px; max-height: 180px; overflow-y: auto;'>"
            st.markdown(uploads_html_container, unsafe_allow_html=True)
            
            # Selectbox for clean selection without radio buttons
            upload_map = {f"📄 {u.get('filename', 'resume')} ({u.get('name') or 'New Applicant'})": u["id"] for u in uploads_list}
            selected_label = st.selectbox(
                "Select File to View Parsed Details",
                list(upload_map.keys()),
                index=0,
                key="uploaded_file_selection"
            )
            st.session_state.selected_resume_id = upload_map[selected_label]
        else:
            st.markdown("<p style='color: #64748B; font-size: 0.85rem;'>No uploads recorded yet.</p>", unsafe_allow_html=True)

st.markdown("<div style='height: 24px;'></div>", unsafe_allow_html=True)

# --- BOTTOM SECTION: SPLIT-PANE PREVIEW & PARSED INFO ---
selected_resume = None
if st.session_state.selected_resume_id and uploads_list:
    selected_resume = next((u for u in uploads_list if u["id"] == st.session_state.selected_resume_id), None)

if selected_resume:
    col_bot_left, col_bot_right = st.columns([1, 1])
    
    # Left Side: Resume Preview (Raw text)
    with col_bot_left:
        with st.container(border=True):
            st.markdown("#### <i class='fa-solid fa-file-pdf' style='color:#EF4444;'></i> Resume Preview (Raw Text)", unsafe_allow_html=True)
            st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)
            st.text_area(
                "Raw extracted text",
                value=selected_resume.get("extracted_text", "No raw text available."),
                height=450,
                disabled=True,
                label_visibility="collapsed"
            )

    # Right Side: Parsed Information
    with col_bot_right:
        # Fetch actual parsed_json payload
        parsed_data = selected_resume.get("parsed_json", {})
        if not parsed_data:
            # Fallback mapper
            parsed_data = selected_resume
            
        with st.container(border=True):
            st.markdown("#### <i class='fa-solid fa-wand-magic-sparkles' style='color:#6366F1;'></i> Parsed Information", unsafe_allow_html=True)
            st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)
            
            # Sub-Tabs for different sections
            parsed_tab_id, parsed_tab_skills, parsed_tab_career, parsed_tab_edu, parsed_tab_others = st.tabs([
                "👤 Identity", "⚡ Skills", "💼 Career", "🎓 Education", "🏆 Others"
            ])
            
            with parsed_tab_id:
                st.markdown(f"**Name:** {parsed_data.get('name') or 'N/A'}")
                st.markdown(f"**Email:** {parsed_data.get('email') or 'N/A'}")
                st.markdown(f"**Phone:** {parsed_data.get('phone') or 'N/A'}")
                for label, key in [("LinkedIn", "linkedin"), ("GitHub", "github"), ("Portfolio", "portfolio")]:
                    url = parsed_data.get(key) or ""
                    if url.startswith(("https://", "http://")):
                        st.link_button(f"{label} profile", url, width="content")
                    else:
                        st.markdown(f"**{label}:** N/A")
                
            with parsed_tab_skills:
                st.markdown("**Extracted Skills Tags:**")
                skills = parsed_data.get("skills", [])
                if skills:
                    st.pills(
                        "Skills",
                        skills,
                        selection_mode="multi",
                        default=skills,
                        disabled=True,
                        label_visibility="collapsed",
                        width="stretch",
                        key=f"parsed_skills_{selected_resume['id']}",
                    )
                else:
                    st.write("No skills tags extracted.")
                    
            with parsed_tab_career:
                st.markdown("**Work Experience:**")
                experience = parsed_data.get("experience", [])
                if experience:
                    for exp in experience:
                        st.markdown(f"- {exp}")
                else:
                    st.write("No work experience parsed.")
                    
                st.markdown("<div style='height: 15px;'></div>", unsafe_allow_html=True)
                st.markdown("**Projects:**")
                projects = parsed_data.get("projects", [])
                if projects:
                    for proj in projects:
                        st.markdown(f"- {proj}")
                else:
                    st.write("No projects parsed.")
                    
            with parsed_tab_edu:
                st.markdown("**Education History:**")
                education = parsed_data.get("education", [])
                if education:
                    for edu in education:
                        st.markdown(f"- {edu}")
                else:
                    st.write("No education details parsed.")
                    
                st.markdown("<div style='height: 15px;'></div>", unsafe_allow_html=True)
                st.markdown("**Certifications:**")
                certs = parsed_data.get("certifications", [])
                if certs:
                    for cert in certs:
                        st.markdown(f"- {cert}")
                else:
                    st.write("No certifications parsed.")
                    
            with parsed_tab_others:
                st.markdown("**Languages spoken:**")
                languages = parsed_data.get("languages", [])
                if languages:
                    for lang in languages:
                        st.markdown(f"- {lang}")
                else:
                    st.write("No languages specified.")
                    
                st.markdown("<div style='height: 15px;'></div>", unsafe_allow_html=True)
                st.markdown("**Key Achievements:**")
                achievements = parsed_data.get("achievements", [])
                if achievements:
                    for ach in achievements:
                        st.markdown(f"- {ach}")
                else:
                    st.write("No achievements extracted.")

# --- BOTTOM SECTION: RECENT UPLOADS TABLE ---
st.markdown("<div style='height: 20px;'></div>", unsafe_allow_html=True)
with st.container(border=True):
    st.markdown("#### <i class='fa-solid fa-list' style='color:#6366F1;'></i> Recent Uploads", unsafe_allow_html=True)
    st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)
    
    if uploads_list:
        st.markdown("""
        <table class="custom-table" style="width: 100%; border-collapse: collapse; text-align: left; font-size: 0.88rem;">
            <thead>
                <tr style="background-color: #F8FAFC; border-bottom: 2px solid #E2E8F0;">
                    <th style="padding: 10px; font-weight: 700; color: #475569;">Filename</th>
                    <th style="padding: 10px; font-weight: 700; color: #475569;">Candidate Name</th>
                    <th style="padding: 10px; font-weight: 700; color: #475569;">Email</th>
                    <th style="padding: 10px; font-weight: 700; color: #475569;">Phone</th>
                    <th style="padding: 10px; font-weight: 700; color: #475569;">Upload Status</th>
                </tr>
            </thead>
            <tbody>
        """, unsafe_allow_html=True)
        
        for u in uploads_list[:6]:
            st.markdown(f"""
            <tr style="border-bottom: 1px solid #F1F5F9;">
                <td style="padding: 10px; font-weight: 700; color: #4F46E5;">{u.get('filename')}</td>
                <td style="padding: 10px; color: #0F172A; font-weight: 600;">{u.get('name') or 'N/A'}</td>
                <td style="padding: 10px; color: #475569;">{u.get('email') or 'N/A'}</td>
                <td style="padding: 10px; color: #475569;">{u.get('phone') or 'N/A'}</td>
                <td style="padding: 10px;"><span class="badge-strong" style="background-color: #ECFDF5; color: #047857; font-size: 0.72rem; padding: 2px 10px;">{u.get('status')}</span></td>
            </tr>
            """, unsafe_allow_html=True)
            
        st.markdown("</tbody></table>", unsafe_allow_html=True)
    else:
        st.write("No uploaded resumes found.")
