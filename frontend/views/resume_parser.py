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
from frontend.components.file_uploader import file_uploader_simple

# Page Config
st.set_page_config(
    page_title="Resume Parser - HirePilot",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="expanded"
)

setup_page("Resume Parser", "Upload and parse candidate resumes", page_key=__file__)

# Inject custom CSS for better input alignment
st.markdown("""
<style>
/* File uploader styling */
.stFileUploader > div > div {
    border: 2px dashed #E2E8F0 !important;
    border-radius: 12px !important;
    padding: 24px !important;
    background-color: #FAFAFA !important;
    transition: all 0.2s ease !important;
}
.stFileUploader > div > div:hover {
    border-color: #6366F1 !important;
    background-color: #F5F3FF !important;
}
.stFileUploader > div > div[data-drag-active="true"] {
    border-color: #6366F1 !important;
    background-color: #EEF2FF !important;
}

/* Text area for pasted resume */
.stTextArea textarea {
    border: 2px solid #E2E8F0 !important;
    border-radius: 12px !important;
    padding: 16px !important;
    font-family: 'Plus Jakarta Sans', sans-serif !important;
    font-size: 14px !important;
    line-height: 1.6 !important;
    background-color: #FFFFFF !important;
    color: #0F172A !important;
    min-height: 160px !important;
}
.stTextArea textarea:focus {
    border-color: #6366F1 !important;
    box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.15) !important;
    outline: none !important;
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
.stButton > button[kind="secondary"] {
    background-color: #FFFFFF !important;
    border: 1px solid #E2E8F0 !important;
    border-radius: 10px !important;
    padding: 12px 24px !important;
    font-weight: 600 !important;
    font-size: 14px !important;
    color: #475569 !important;
    transition: all 0.2s ease !important;
}
.stButton > button[kind="secondary"]:hover {
    background-color: #F8FAFC !important;
    border-color: #CBD5E1 !important;
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

/* Section headers */
h4 {
    font-weight: 700 !important;
    color: #0F172A !important;
}

/* Pills styling */
.stPills > div {
    gap: 8px !important;
}
.stPills button {
    background-color: #EEF2FF !important;
    color: #4F46E5 !important;
    border: 1px solid #E0E7FF !important;
    border-radius: 9999px !important;
    padding: 6px 14px !important;
    font-size: 13px !important;
    font-weight: 500 !important;
}

/* Table styling */
.custom-table th {
    background-color: #F8FAFC !important;
    font-weight: 700 !important;
    color: #475569 !important;
}
.custom-table td {
    color: #334155 !important;
}
.badge-strong {
    background-color: #ECFDF5 !important;
    color: #047857 !important;
    padding: 4px 12px !important;
    border-radius: 9999px !important;
    font-weight: 600 !important;
    font-size: 0.72rem !important;
}
</style>
""", unsafe_allow_html=True)

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
col_top_left, col_top_right = st.columns([1.15, 0.85], gap="large")

with col_top_left:
    with st.container(border=True):
        st.markdown("#### <i class='fa-solid fa-cloud-arrow-up' style='color:#6366F1;'></i> Upload Resumes", unsafe_allow_html=True)
        st.markdown("<p style='font-size: 0.82rem; color: #64748B; margin-bottom: 16px;'>PDF, DOCX, TXT • Bulk upload supported</p>", unsafe_allow_html=True)
        
        uploaded_files = file_uploader_simple(
            label="Drag and drop resumes here",
            accepted_types=["pdf", "docx", "txt"],
            max_size_mb=200,
            key="bulk_resume_file_uploader",
            multiple=True
        )
        
        if uploaded_files:
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            if st.button("Parse Resumes with Ollama AI", type="primary", width="stretch"):
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
        
        # --- PASTE RESUME TEXT ---
        with st.expander("📋 Or Paste Resume Text", expanded=False):
            st.markdown("<p style='font-size: 0.82rem; color: #64748B; margin-bottom: 10px;'>Paste raw resume text for instant AI parsing</p>", unsafe_allow_html=True)
            pasted_text = st.text_area(
                "Resume text",
                placeholder="Paste resume content here...",
                height=160,
                label_visibility="collapsed",
                key="pasted_resume_text"
            )
            if st.button("Parse Pasted Text", type="secondary", width="stretch", disabled=not st.session_state.get("pasted_resume_text", "").strip()):
                with st.spinner("Parsing with Ollama AI..."):
                    res = api_client.parse_resume_text(st.session_state.get("pasted_resume_text", ""))
                    if res:
                        st.toast("Successfully parsed pasted resume!", icon="✅")
                        st.session_state.selected_resume_id = None
                        st.rerun()
                    else:
                        st.error("Failed to parse pasted resume.")

with col_top_right:
    with st.container(border=True):
        st.markdown("#### <i class='fa-solid fa-clock-rotate-left' style='color:#6366F1;'></i> Upload History", unsafe_allow_html=True)
        st.markdown("<div style='height: 8px;'></div>", unsafe_allow_html=True)
        
        if uploads_list:
            # Create a nice list with radio selection
            for i, u in enumerate(uploads_list[:10]):
                candidate_name = u.get('name') or 'New Applicant'
                filename = u.get('filename', 'resume')
                created = u.get('created_at', '')[:10] if u.get('created_at') else ''
                
                is_selected = st.session_state.selected_resume_id == u["id"]
                
                # Use a container with custom styling
                with st.container():
                    col_radio, col_info = st.columns([0.08, 0.92], gap="small")
                    with col_radio:
                        if st.radio("Select upload", [u["id"]], index=0 if is_selected else None, key=f"hist_radio_{u['id']}", label_visibility="collapsed", horizontal=True):
                            st.session_state.selected_resume_id = u["id"]
                            st.rerun()
                    with col_info:
                        st.markdown(f"""
                        <div style='padding: 8px 12px; background-color: {"#EEF2FF" if is_selected else "#FAFAFA"}; border-radius: 10px; border: 1px solid {"#C7D2FE" if is_selected else "#F1F5F9"}; margin-bottom: 6px; cursor: pointer;'>
                            <div style='font-weight: 600; color: #0F172A; font-size: 0.88rem;'>📄 {filename}</div>
                            <div style='font-size: 0.8rem; color: #64748B; margin-top: 2px;'>{candidate_name} • {created}</div>
                        </div>
                        """, unsafe_allow_html=True)
        else:
            st.markdown("<p style='color: #64748B; font-size: 0.85rem; text-align: center; padding: 20px;'>No uploads recorded yet</p>", unsafe_allow_html=True)

st.markdown("<div style='height: 24px;'></div>", unsafe_allow_html=True)

# --- BOTTOM SECTION: SPLIT-PANE PREVIEW & PARSED INFO ---
selected_resume = None
if st.session_state.selected_resume_id and uploads_list:
    selected_resume = next((u for u in uploads_list if u["id"] == st.session_state.selected_resume_id), None)

if selected_resume:
    col_bot_left, col_bot_right = st.columns([1, 1], gap="large")
    
    # Left Side: Resume Preview (Raw text)
    with col_bot_left:
        with st.container(border=True):
            st.markdown("#### <i class='fa-solid fa-file-pdf' style='color:#EF4444;'></i> Resume Preview (Raw Text)", unsafe_allow_html=True)
            st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)
            st.text_area(
                "Raw extracted text",
                value=selected_resume.get("extracted_text", "No raw text available."),
                height=500,
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
                    <th style="padding: 12px; font-weight: 700; color: #475569;">Filename</th>
                    <th style="padding: 12px; font-weight: 700; color: #475569;">Candidate Name</th>
                    <th style="padding: 12px; font-weight: 700; color: #475569;">Email</th>
                    <th style="padding: 12px; font-weight: 700; color: #475569;">Phone</th>
                    <th style="padding: 12px; font-weight: 700; color: #475569;">Upload Status</th>
                </tr>
            </thead>
            <tbody>
        """, unsafe_allow_html=True)
        
        for u in uploads_list[:6]:
            st.markdown(f"""
            <tr style="border-bottom: 1px solid #F1F5F9;">
                <td style="padding: 12px; font-weight: 700; color: #4F46E5;">{u.get('filename')}</td>
                <td style="padding: 12px; color: #0F172A; font-weight: 600;">{u.get('name') or 'N/A'}</td>
                <td style="padding: 12px; color: #475569;">{u.get('email') or 'N/A'}</td>
                <td style="padding: 12px; color: #475569;">{u.get('phone') or 'N/A'}</td>
                <td style="padding: 12px;"><span class="badge-strong" style="background-color: #ECFDF5; color: #047857; font-size: 0.72rem; padding: 4px 12px;">{u.get('status')}</span></td>
            </tr>
            """, unsafe_allow_html=True)
            
        st.markdown("</tbody></table>", unsafe_allow_html=True)
    else:
        st.markdown("<p style='color: #64748B; font-size: 0.85rem; text-align: center; padding: 20px;'>No uploaded resumes found</p>", unsafe_allow_html=True)
