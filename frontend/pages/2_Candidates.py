import streamlit as st
import os
import sys

# Setup path to import api_client
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from frontend.components import api_client
from frontend.services.cache import get_candidates_cached
from frontend.services.app_state import AppState
from frontend.components.page_utils import setup_page, render_sidebar_footer

# Page Config
st.set_page_config(
    page_title="Candidate Management - HirePilot",
    page_icon="👥",
    layout="wide",
    initial_sidebar_state="expanded"
)

setup_page("Candidate Profiles", "Manage and screen applicants", page_key=__file__)

# State initialization
if "selected_cand_id" not in st.session_state:
    st.session_state.selected_cand_id = None

# Top Section Filters
col_search, col_status, col_exp, col_skills = st.columns([3.5, 2.1, 2.1, 2.1])

with col_search:
    search = st.text_input("Search Candidates", value="", placeholder="Search by name, title...", label_visibility="collapsed")
with col_status:
    status_filter = st.selectbox("Status Filter", ["All", "Applied", "Shortlisted", "Interview Scheduled", "Approved", "Rejected"], index=0, label_visibility="collapsed")
with col_exp:
    exp_filter = st.selectbox("Experience Filter", ["All", "Junior (0-2 Yrs)", "Mid-level (3-5 Yrs)", "Senior (6+ Yrs)"], index=0, label_visibility="collapsed")
with col_skills:
    skill_filter = st.selectbox("Skills Filter", ["All", "Python", "SQL", "FastAPI", "React", "Docker", "Machine Learning"], index=0, label_visibility="collapsed")

# Load candidate roster
cands = api_client.get_candidates(search=search, status=status_filter, skill=skill_filter)

# Filter Experience locally
if exp_filter != "All":
    if "Junior" in exp_filter:
        cands = [c for c in cands if c.get("years_experience", 0) <= 2]
    elif "Mid-level" in exp_filter:
        cands = [c for c in cands if 3 <= c.get("years_experience", 0) <= 5]
    elif "Senior" in exp_filter:
        cands = [c for c in cands if c.get("years_experience", 0) >= 6]

# Layout Selection (Split-pane or full screen)
is_drawer_open = st.session_state.selected_cand_id is not None
if is_drawer_open:
    list_col, drawer_col = st.columns([1.1, 0.9])
else:
    list_col = st.container()
    drawer_col = None

with list_col:
    if not cands:
        st.markdown("<p style='text-align: center; color: #64748B; font-weight: 500; padding: 40px 0;'>No candidates match the criteria.</p>", unsafe_allow_html=True)
    else:
        for c in cands:
            match_color = "#10B981" if c.get("match_score", 0) >= 85 else ("#F59E0B" if c.get("match_score", 0) >= 70 else "#EF4444")
            skills_html = "".join([f'<span class="tag" style="background-color:#EEF2FF; color:#4F46E5; border:1px solid #E0E7FF;">{s.get("name") if isinstance(s, dict) else s}</span>' for s in (c.get("skills", [])[:4])])
            if len(c.get("skills", [])) > 4:
                skills_html += f'<span class="tag" style="background-color: #EEF2FF; color: #4F46E5;">+{len(c.get("skills", [])) - 4} more</span>'

            # Fetch resumes to display indicator
            c_details = api_client.get_candidate(c["id"]) or {}
            resumes = c_details.get("resumes", [])
            has_resume = len(resumes) > 0
            resume_file_indicator = f"📄 {resumes[-1]['filename']}" if has_resume else "❌ No Resume Uploaded"

            with st.container(border=True):
                # Avatar & Name block
                col_avatar, col_body = st.columns([1, 6])
                with col_avatar:
                    initials = "".join([part[0] for part in c.get('name', 'C').split()[:2]])
                    st.markdown(f"""
                    <div style="width: 44px; height: 44px; border-radius: 50%; background-color: #EEF2FF; border: 1.5px solid #6366F1; display: flex; align-items: center; justify-content: center; font-weight: 800; color: #6366F1; font-size: 14px; margin: 5px auto;">
                        {initials}
                    </div>
                    """, unsafe_allow_html=True)
                with col_body:
                    st.markdown(f"""
                    <div>
                        <div style="display: flex; align-items: center; gap: 8px;">
                            <span style="font-weight: 800; font-size: 1.1rem; color: #0F172A;">{c.get('name')}</span>
                            <span class="badge-blue" style="background-color: #ECFDF5; color: #047857; font-size: 0.65rem; padding: 2px 10px; border-radius:9999px;">{c.get('status')}</span>
                            <span class="badge-strong" style="background-color: {match_color}10; color: {match_color}; font-size: 0.65rem; padding: 2px 10px; border-radius:9999px;">{c.get('match_score', 0)}% Match</span>
                        </div>
                        <p style="font-size: 0.8rem; color: #64748B; margin: 2px 0 6px 0;">
                            {c.get('current_title') or 'Applicant'} • {c.get('years_experience')} Yrs Exp • {c.get('location')}
                        </p>
                        <div style="font-size: 0.72rem; color: #475569; margin-bottom: 8px;"><i class="fa-solid fa-file-contract"></i> <strong>Resume:</strong> {resume_file_indicator}</div>
                        <div>{skills_html}</div>
                    </div>
                    """, unsafe_allow_html=True)

                # Card Actions Grid
                st.markdown("<div style='height: 8px;'></div>", unsafe_allow_html=True)
                btn_cols = st.columns(5)
                
                with btn_cols[0]:
                    if st.button("View Profile", key=f"view_profile_btn_{c['id']}", use_container_width=True):
                        st.session_state.selected_cand_id = c["id"]
                        st.rerun()
                
                with btn_cols[1]:
                    if st.button("AI Summary", key=f"ai_summary_btn_{c['id']}", use_container_width=True, type="secondary"):
                        st.session_state[f"ai_sum_open_{c['id']}"] = not st.session_state.get(f"ai_sum_open_{c['id']}", False)
                        st.rerun()
                        
                with btn_cols[2]:
                    if st.button("Compare", key=f"compare_btn_{c['id']}", use_container_width=True, type="secondary"):
                        # Redirect to screening page
                        st.session_state.selected_eval_cand_id = c["id"]
                        st.switch_page("pages/4_AI_Screening.py")
                        
                with btn_cols[3]:
                    if st.button("Interview", key=f"interview_btn_{c['id']}", use_container_width=True, type="secondary"):
                        res = api_client.update_candidate_status(c["id"], "Interview Scheduled")
                        if res:
                            st.toast("Status updated to Interview Scheduled!", icon="📅")
                            st.rerun()
                            
                with btn_cols[4]:
                    if st.button("Resume", key=f"resume_btn_{c['id']}", use_container_width=True, type="secondary"):
                        st.session_state[f"resume_preview_open_{c['id']}"] = not st.session_state.get(f"resume_preview_open_{c['id']}", False)
                        st.rerun()

            # Render Inline AI Summary if toggled
            if st.session_state.get(f"ai_sum_open_{c['id']}", False):
                with st.container(border=True):
                    st.markdown("**🤖 AI Candidate Summary:**")
                    st.write(c.get("summary") or "AI summary details parsed successfully.")
                    
            # Render Inline Resume Preview if toggled
            if st.session_state.get(f"resume_preview_open_{c['id']}", False):
                with st.container(border=True):
                    st.markdown("**📄 Parsed Resume Details:**")
                    if has_resume:
                        r = resumes[-1]
                        st.markdown(f"**Education:** {', '.join(r.get('education', []))}")
                        st.markdown(f"**Certifications:** {', '.join(r.get('certifications', []))}")
                        st.markdown(f"**Experience Summary:** {', '.join(r.get('experience', []))}")
                    else:
                        st.write("No parsed resume details available. Upload a resume file first.")
            st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)

# --- SPLIT PANE PROFILE DRAWER ---
if drawer_col and st.session_state.selected_cand_id:
    cand = api_client.get_candidate(st.session_state.selected_cand_id)
    resumes = cand.get("resumes", [])
    has_resume = len(resumes) > 0
    
    with drawer_col:
        with st.container(border=True):
            # Header actions
            head_col1, head_col2 = st.columns([8, 2])
            with head_col1:
                st.markdown(f"### <i class='fa-solid fa-user-tie' style='color:#6366F1;'></i> Profile Details")
            with head_col2:
                if st.button("✕ Close", key="close_drawer_btn", use_container_width=True):
                    st.session_state.selected_cand_id = None
                    st.rerun()
                    
            st.markdown(f"""
            <div style="background-color: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 12px; padding: 16px; margin-bottom: 15px;">
                <h4 style="margin: 0; color:#0F172A; font-weight:800;">{cand.get('name')}</h4>
                <p style="margin:2px 0 0 0; font-size:0.8rem; color:#4F46E5; font-weight:600;">{cand.get('current_title') or 'Applicant'}</p>
                <div style="font-size:0.75rem; color:#64748B; margin-top:6px;">Status: <strong>{cand.get('status')}</strong></div>
            </div>
            """, unsafe_allow_html=True)
            
            # Sub-Tabs
            tab_summary, tab_details, tab_timeline, tab_notes = st.tabs(["📝 Overview", "📄 Resume", "⏳ Timeline", "💬 Notes"])
            
            with tab_summary:
                st.markdown("**Contact Information:**")
                st.markdown(f"- **Email:** {cand.get('email')}")
                st.markdown(f"- **Phone:** {cand.get('phone') or 'N/A'}")
                st.markdown(f"- **Location:** {cand.get('location') or 'Remote'}")
                
                st.markdown("<div style='height: 8px;'></div>", unsafe_allow_html=True)
                st.markdown("**Social Links:**")
                li_link = f"[LinkedIn]({cand.get('linkedin')})" if cand.get('linkedin') else "LinkedIn (Not linked)"
                gh_link = f"[GitHub]({cand.get('github')})" if cand.get('github') else "GitHub (Not linked)"
                st.markdown(f"- <i class='fa-brands fa-linkedin' style='color:#0077b5;'></i> {li_link}", unsafe_allow_html=True)
                st.markdown(f"- <i class='fa-brands fa-github' style='color:#333;'></i> {gh_link}", unsafe_allow_html=True)
                
                st.markdown("<div style='height: 8px;'></div>", unsafe_allow_html=True)
                st.markdown("**Extracted Profile Fields:**")
                
                # Render parsed education/certifications
                if has_resume:
                    r = resumes[-1]
                    st.markdown("**Education:**")
                    for edu in r.get("education", []):
                        st.markdown(f"- {edu}")
                    
                    st.markdown("**Certifications:**")
                    for cert in r.get("certifications", []):
                        st.markdown(f"- {cert}")
                else:
                    st.write("No parsed resume fields available.")
                    
            with tab_details:
                st.markdown("**Parsed Resume Preview:**")
                if has_resume:
                    r = resumes[-1]
                    st.markdown("**Experience:**")
                    for exp in r.get("experience", []):
                        st.markdown(f"- {exp}")
                        
                    st.markdown("**Projects:**")
                    for proj in r.get("projects", []):
                        st.markdown(f"- {proj}")
                        
                    with st.expander("Show raw extracted text"):
                        st.text_area("Extracted text", value=r.get("extracted_text", ""), height=200, disabled=True, label_visibility="collapsed")
                else:
                    st.write("No resume file loaded yet.")
                    
            with tab_timeline:
                st.markdown("**Activity Timeline History:**")
                # Compile timeline list
                timeline = []
                timeline.append({"title": "Application Started", "desc": "Candidate profile registered.", "time": cand.get("created_at")})
                
                # Add notes info to timeline
                for note in cand.get("notes", []):
                    timeline.append({"title": f"Note by {note.get('author')}", "desc": note.get("note"), "time": note.get("created_at")})
                    
                # Sort timeline by time
                timeline.sort(key=lambda t: t.get("time", ""), reverse=True)
                
                timeline_html = "<div style='display: flex; flex-direction: column; gap: 14px; margin-top: 10px;'>"
                for idx, event in enumerate(timeline):
                    time_str = datetime.datetime.fromisoformat(event["time"]).strftime("%b %d, %H:%M") if event.get("time") else "Just now"
                    timeline_html += f"""
                    <div style="display: flex; gap: 10px;">
                        <div style="display: flex; flex-direction: column; align-items: center;">
                            <div style="width: 18px; height: 18px; border-radius: 50%; background-color: #6366F1; border: 3px solid #EEF2FF;"></div>
                            { '<div style="width: 2px; flex-grow: 1; background-color: #E2E8F0;"></div>' if idx < len(timeline)-1 else '' }
                        </div>
                        <div style="padding-bottom: 10px;">
                            <div style="font-weight: 700; color: #0F172A; font-size: 0.8rem;">{event['title']}</div>
                            <div style="font-size: 0.76rem; color: #64748B; margin-top: 1px;">{event['desc']}</div>
                            <div style="font-size: 0.68rem; color: #94A3B8; margin-top: 2px; font-weight:500;">{time_str}</div>
                        </div>
                    </div>
                    """
                timeline_html += "</div>"
                st.markdown(timeline_html, unsafe_allow_html=True)
                
            with tab_notes:
                st.markdown("**Recruiter Notes:**")
                new_note = st.text_area("Write note...", placeholder="Enter review remarks...", label_visibility="collapsed", key="drawer_note_input")
                if st.button("Save Note", type="primary", use_container_width=True):
                    if new_note.strip():
                        res = api_client.add_candidate_note(cand["id"], new_note.strip())
                        if res:
                            st.toast("Note appended!", icon="📝")
                            st.rerun()
                            
                # List existing notes
                notes = cand.get("notes", [])
                if notes:
                    notes_html = "<div style='display: flex; flex-direction: column; gap: 10px; margin-top: 15px; max-height: 200px; overflow-y: auto;'>"
                    for n in notes:
                        time_str = datetime.datetime.fromisoformat(n["created_at"]).strftime("%b %d, %H:%M") if n.get("created_at") else "Just now"
                        notes_html += f"""
                        <div style="background-color: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 8px; padding: 10px 12px;">
                            <div style="display: flex; justify-content: space-between; font-size: 0.7rem; color: #64748B; font-weight: 600; margin-bottom: 4px;">
                                <span>{n.get('author', 'Recruiter')}</span>
                                <span>{time_str}</span>
                            </div>
                            <p style="margin: 0; font-size: 0.78rem; color: #334155;">{n.get('note')}</p>
                        </div>
                        """
                    notes_html += "</div>"
                    st.markdown(notes_html, unsafe_allow_html=True)
                else:
                    st.write("No notes added yet.")

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
