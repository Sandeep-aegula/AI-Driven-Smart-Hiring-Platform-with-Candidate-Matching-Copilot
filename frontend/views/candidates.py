import streamlit as st
import os
import sys
import datetime
import httpx

# Setup path to import api_client
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
project_root = os.path.dirname(parent_dir)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

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

setup_page("Candidate Profiles", "Manage, rank and screen applicants with AI", page_key=__file__)

# ── State initialization ──────────────────────────────────────────────────────
if "selected_cand_id" not in st.session_state:
    st.session_state.selected_cand_id = None
if "rank_job_id" not in st.session_state:
    st.session_state.rank_job_id = None
if "ranked_candidates" not in st.session_state:
    st.session_state.ranked_candidates = None


# ══════════════════════════════════════════════════════════════════════════════
# HELPERS
# ══════════════════════════════════════════════════════════════════════════════

def call_ollama(prompt: str, model: str = "qwen2.5-coder:7b") -> str:
    """Call Ollama API directly and return text."""
    try:
        r = httpx.post(
            "http://localhost:11434/api/generate",
            json={"model": model, "prompt": prompt, "stream": False},
            timeout=90.0
        )
        if r.status_code == 200:
            return r.json().get("response", "").strip()
        return f"[Ollama error: {r.status_code}]"
    except Exception as e:
        return f"[Connection error: {e}]"


def score_candidate_vs_job(candidate: dict, job: dict) -> int:
    """Compute a simple match score between a candidate and a job."""
    cand_skills = set(
        (s.get("name") if isinstance(s, dict) else s).lower()
        for s in candidate.get("skills", [])
    )
    job_skills = set(r.lower() for r in job.get("requirements", []))
    if not job_skills:
        return candidate.get("match_score", 50)
    overlap = len(cand_skills & job_skills)
    base = int((overlap / len(job_skills)) * 100)
    exp_min = job.get("experience_min", 0)
    cand_exp = candidate.get("years_experience", 0)
    exp_bonus = 5 if cand_exp >= exp_min else 0
    return min(base + exp_bonus, 100)


def get_skill_gaps(candidate: dict, job: dict) -> tuple[list, list, list]:
    """Return (matched_skills, missing_skills, extra_skills)."""
    cand_skills = set(
        (s.get("name") if isinstance(s, dict) else s).lower()
        for s in candidate.get("skills", [])
    )
    job_skills = set(r.lower() for r in job.get("requirements", []))
    matched = sorted(cand_skills & job_skills)
    missing = sorted(job_skills - cand_skills)
    extra = sorted(cand_skills - job_skills)
    return matched, missing, extra


# ══════════════════════════════════════════════════════════════════════════════
# TOP BAR — AI RESUME RANKING
# ══════════════════════════════════════════════════════════════════════════════

with st.expander("🏆 AI Resume Matching & Candidate Ranking", expanded=False):
    st.markdown(
        "<p style='font-size:0.85rem; color:#64748B; margin:0 0 12px 0;'>"
        "Select a job opening to <strong>rank all candidates</strong> by resume match score. "
        "Powered by skill overlap analysis + experience fit.</p>",
        unsafe_allow_html=True
    )
    all_jobs = api_client.get_jobs() or []
    job_options = {f"{j.get('title')} — {j.get('department')}": j for j in all_jobs}

    rc1, rc2 = st.columns([4, 1])
    with rc1:
        selected_job_label = st.selectbox(
            "Select Job to Rank Against",
            ["— Choose a job —"] + list(job_options.keys()),
            label_visibility="collapsed"
        )
    with rc2:
        rank_btn = st.button("🔍 Rank Candidates", type="primary", width="stretch")

    if rank_btn and selected_job_label != "— Choose a job —":
        selected_job = job_options[selected_job_label]
        all_cands = api_client.get_candidates() or []
        ranked = []
        with st.spinner("Scoring candidates against job requirements…"):
            for c in all_cands:
                score = score_candidate_vs_job(c, selected_job)
                matched, missing, _ = get_skill_gaps(c, selected_job)
                ranked.append({**c, "computed_score": score, "matched_skills": matched, "missing_skills": missing})
        ranked.sort(key=lambda x: x["computed_score"], reverse=True)
        st.session_state.ranked_candidates = {"job": selected_job, "results": ranked}
        st.success(f"✅ Ranked {len(ranked)} candidates against **{selected_job.get('title')}**")

    if st.session_state.ranked_candidates:
        job = st.session_state.ranked_candidates["job"]
        results = st.session_state.ranked_candidates["results"]
        st.markdown(f"**Ranking results for: {job.get('title')} — {job.get('department')}**")
        for rank, c in enumerate(results, 1):
            score = c["computed_score"]
            bar_color = "#10B981" if score >= 75 else ("#F59E0B" if score >= 50 else "#EF4444")
            medal = "🥇" if rank == 1 else ("🥈" if rank == 2 else ("🥉" if rank == 3 else f"#{rank}"))
            matched = ", ".join(c["matched_skills"][:4]) or "None"
            missing = ", ".join(c["missing_skills"][:4]) or "None"
            with st.container(border=True):
                col_rank, col_info, col_bar = st.columns([0.5, 4, 2])
                with col_rank:
                    st.markdown(f"<div style='font-size:1.4rem; text-align:center; padding-top:6px;'>{medal}</div>", unsafe_allow_html=True)
                with col_info:
                    st.markdown(f"**{c.get('name')}** — {c.get('current_title') or 'Applicant'}")
                    st.caption(f"✅ Matched: {matched}   |   ❌ Missing: {missing}")
                with col_bar:
                    st.markdown(f"<div style='font-size:1.1rem; font-weight:800; color:{bar_color}; text-align:right;'>{score}%</div>", unsafe_allow_html=True)
                    st.progress(score / 100)
        if st.button("✕ Clear Rankings", key="clear_rankings"):
            st.session_state.ranked_candidates = None
            st.rerun()

st.markdown("<div style='height:10px;'></div>", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# FILTER BAR
# ══════════════════════════════════════════════════════════════════════════════

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

# ══════════════════════════════════════════════════════════════════════════════
# SPLIT-PANE LAYOUT
# ══════════════════════════════════════════════════════════════════════════════

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
            skills_html = "".join([
                f'<span class="tag" style="background-color:#EEF2FF; color:#4F46E5; border:1px solid #E0E7FF;">{s.get("name") if isinstance(s, dict) else s}</span>'
                for s in (c.get("skills", [])[:4])
            ])
            if len(c.get("skills", [])) > 4:
                skills_html += f'<span class="tag" style="background-color: #EEF2FF; color: #4F46E5;">+{len(c.get("skills", [])) - 4} more</span>'

            c_details = api_client.get_candidate(c["id"]) or {}
            resumes = c_details.get("resumes", [])
            has_resume = len(resumes) > 0
            resume_file_indicator = f"📄 {resumes[-1]['filename']}" if has_resume else "❌ No Resume Uploaded"

            with st.container(border=True):
                col_avatar, col_body = st.columns([1, 6])
                with col_avatar:
                    initials = "".join([part[0] for part in c.get('name', 'C').split()[:2]])
                    st.markdown(f"""
                    <div style="width: 44px; height: 44px; border-radius: 50%; background-color: #EEF2FF; border: 1.5px solid #6366F1;
                                display: flex; align-items: center; justify-content: center; font-weight: 800; color: #6366F1; font-size: 14px; margin: 5px auto;">
                        {initials}
                    </div>
                    """, unsafe_allow_html=True)
                with col_body:
                    st.markdown(f"""
                    <div>
                        <div style="display: flex; align-items: center; gap: 8px;">
                            <span style="font-weight: 800; font-size: 1.1rem; color: #0F172A;">{c.get('name')}</span>
                            <span style="background-color: #ECFDF5; color: #047857; font-size: 0.65rem; padding: 2px 10px; border-radius:9999px; font-weight:700;">{c.get('status')}</span>
                            <span style="background-color: {match_color}15; color: {match_color}; font-size: 0.65rem; padding: 2px 10px; border-radius:9999px; font-weight:700;">{c.get('match_score', 0)}% Match</span>
                        </div>
                        <p style="font-size: 0.8rem; color: #64748B; margin: 2px 0 6px 0;">
                            {c.get('current_title') or 'Applicant'} &bull; {c.get('years_experience')} Yrs Exp &bull; {c.get('location')}
                        </p>
                        <div style="font-size: 0.72rem; color: #475569; margin-bottom: 8px;"><strong>Resume:</strong> {resume_file_indicator}</div>
                        <div>{skills_html}</div>
                    </div>
                    """, unsafe_allow_html=True)

                st.markdown("<div style='height: 8px;'></div>", unsafe_allow_html=True)
                btn_cols = st.columns(5)

                with btn_cols[0]:
                    if st.button("View Profile", key=f"view_profile_btn_{c['id']}", width="stretch"):
                        st.session_state.selected_cand_id = c["id"]
                        st.rerun()

                with btn_cols[1]:
                    if st.button("AI Summary", key=f"ai_summary_btn_{c['id']}", width="stretch", type="secondary"):
                        st.session_state[f"ai_sum_open_{c['id']}"] = not st.session_state.get(f"ai_sum_open_{c['id']}", False)
                        st.rerun()

                with btn_cols[2]:
                    if st.button("Compare", key=f"compare_btn_{c['id']}", width="stretch", type="secondary"):
                        st.session_state.selected_eval_cand_id = c["id"]
                        st.switch_page("pages/4_AI_Screening.py")

                with btn_cols[3]:
                    if st.button("Interview", key=f"interview_btn_{c['id']}", width="stretch", type="secondary"):
                        res = api_client.update_candidate_status(c["id"], "Interview Scheduled")
                        if res:
                            st.toast("Status updated to Interview Scheduled!", icon="📅")
                            st.rerun()

                with btn_cols[4]:
                    if st.button("Resume", key=f"resume_btn_{c['id']}", width="stretch", type="secondary"):
                        st.session_state[f"resume_preview_open_{c['id']}"] = not st.session_state.get(f"resume_preview_open_{c['id']}", False)
                        st.rerun()

            if st.session_state.get(f"ai_sum_open_{c['id']}", False):
                with st.container(border=True):
                    st.markdown("**<i class='fa-solid fa-robot' style='color:#6366F1; margin-right:6px;'></i> AI Candidate Summary:**", unsafe_allow_html=True)
                    st.write(c.get("summary") or "AI summary details parsed successfully.")

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


# ══════════════════════════════════════════════════════════════════════════════
# SPLIT-PANE PROFILE DRAWER — with new AI tabs
# ══════════════════════════════════════════════════════════════════════════════

if drawer_col and st.session_state.selected_cand_id:
    cand = api_client.get_candidate(st.session_state.selected_cand_id)
    if not cand:
        st.error("Candidate not found.")
    else:
        resumes = cand.get("resumes", [])
        has_resume = len(resumes) > 0
        resume_text = resumes[-1].get("extracted_text", "") if has_resume else ""

        with drawer_col:
            with st.container(border=True):
                head_col1, head_col2 = st.columns([8, 2])
                with head_col1:
                    initials = "".join([part[0] for part in cand.get('name', 'C').split()[:2]])
                    st.markdown(f"""
                    <div style="display:flex; align-items:center; gap:12px;">
                        <div style="width:40px; height:40px; border-radius:50%; background:linear-gradient(135deg,#6366F1,#4F46E5);
                                    display:flex; align-items:center; justify-content:center; color:white; font-weight:800; font-size:14px; flex-shrink:0;">
                            {initials}
                        </div>
                        <div>
                            <div style="font-weight:800; font-size:1rem; color:#0F172A;">{cand.get('name')}</div>
                            <div style="font-size:0.75rem; color:#6366F1; font-weight:600;">{cand.get('current_title') or 'Applicant'}</div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                with head_col2:
                    if st.button("✕ Close", key="close_drawer_btn", width="stretch"):
                        st.session_state.selected_cand_id = None
                        st.rerun()

                st.markdown("<div style='height:8px;'></div>", unsafe_allow_html=True)

                # ── Tabs: now includes AI Chat & Skill Gap ──────────────────
                tab_summary, tab_details, tab_skillgap, tab_chat, tab_timeline, tab_notes = st.tabs([
                    "📝 Overview", "📄 Resume", "🔍 Skill Gap", "💬 Chat AI", "⏳ Timeline", "🗒️ Notes"
                ])

                # ── Overview Tab ──────────────────────────────────────────────
                with tab_summary:
                    st.markdown("**Contact Information:**")
                    st.markdown(f"- **Email:** {cand.get('email')}")
                    st.markdown(f"- **Phone:** {cand.get('phone') or 'N/A'}")
                    st.markdown(f"- **Location:** {cand.get('location') or 'Remote'}")
                    st.markdown("<div style='height: 8px;'></div>", unsafe_allow_html=True)
                    st.markdown("**Social Links:**")
                    li_link = f"[LinkedIn]({cand.get('linkedin')})" if cand.get('linkedin') else "LinkedIn (Not linked)"
                    gh_link = f"[GitHub]({cand.get('github')})" if cand.get('github') else "GitHub (Not linked)"
                    st.markdown(f"- {li_link}")
                    st.markdown(f"- {gh_link}")
                    st.markdown("<div style='height: 8px;'></div>", unsafe_allow_html=True)
                    if has_resume:
                        r = resumes[-1]
                        st.markdown("**Education:**")
                        for edu in r.get("education", []):
                            st.markdown(f"- {edu}")
                        st.markdown("**Certifications:**")
                        for cert in r.get("certifications", []):
                            st.markdown(f"- {cert}")
                    else:
                        st.info("No parsed resume fields available.")

                # ── Resume Tab ────────────────────────────────────────────────
                with tab_details:
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
                        st.info("No resume file loaded yet. Upload via Resume Parser.")

                # ── Skill Gap Analysis Tab ────────────────────────────────────
                with tab_skillgap:
                    st.markdown("#### <i class='fa-solid fa-chart-bar' style='color:#6366F1; margin-right:8px;'></i> Skill Gap Analysis", unsafe_allow_html=True)
                    all_jobs_for_gap = api_client.get_jobs() or []
                    job_options_gap = {f"{j.get('title')} — {j.get('department')}": j for j in all_jobs_for_gap}

                    selected_gap_job = st.selectbox(
                        "Select Job to Analyse Against",
                        ["— Pick a job —"] + list(job_options_gap.keys()),
                        key=f"gap_job_select_{cand['id']}"
                    )

                    if selected_gap_job != "— Pick a job —":
                        gap_job = job_options_gap[selected_gap_job]
                        matched, missing, extra = get_skill_gaps(cand, gap_job)
                        score = score_candidate_vs_job(cand, gap_job)

                        score_color = "#10B981" if score >= 75 else ("#F59E0B" if score >= 50 else "#EF4444")
                        st.markdown(f"""
                        <div style="background:{score_color}10; border:1px solid {score_color}30; border-radius:12px; padding:12px 16px; margin-bottom:14px; text-align:center;">
                            <div style="font-size:2rem; font-weight:900; color:{score_color};">{score}%</div>
                            <div style="font-size:0.8rem; color:#64748B; font-weight:600;">Overall Match Score</div>
                        </div>
                        """, unsafe_allow_html=True)

                        gc1, gc2 = st.columns(2)
                        with gc1:
                            st.markdown("**<i class='fa-solid fa-circle-check' style='color:#10B981; margin-right:6px;'></i> Matched Skills**", unsafe_allow_html=True)
                            if matched:
                                for s in matched:
                                    st.markdown(f"<span style='background:#ECFDF5; color:#047857; padding:2px 8px; border-radius:6px; font-size:0.75rem; margin:2px; display:inline-block;'>{s}</span>", unsafe_allow_html=True)
                            else:
                                st.caption("No matching skills")
                        with gc2:
                            st.markdown("**<i class='fa-solid fa-circle-xmark' style='color:#EF4444; margin-right:6px;'></i> Missing Skills (Gaps)**", unsafe_allow_html=True)
                            if missing:
                                for s in missing:
                                    st.markdown(f"<span style='background:#FEF2F2; color:#991B1B; padding:2px 8px; border-radius:6px; font-size:0.75rem; margin:2px; display:inline-block;'>{s}</span>", unsafe_allow_html=True)
                            else:
                                st.caption("No skill gaps — perfect match!")

                        st.markdown("<div style='height:10px;'></div>", unsafe_allow_html=True)
                        if extra:
                            st.markdown("**<i class='fa-solid fa-lightbulb' style='color:#F59E0B; margin-right:6px;'></i> Additional Skills (not required but good to have)**", unsafe_allow_html=True)
                            for s in extra[:6]:
                                st.markdown(f"<span style='background:#EEF2FF; color:#4F46E5; padding:2px 8px; border-radius:6px; font-size:0.75rem; margin:2px; display:inline-block;'>{s}</span>", unsafe_allow_html=True)

                        st.markdown("<div style='height:12px;'></div>", unsafe_allow_html=True)

                        if st.button("🤖 Get AI Upskilling Recommendations", key=f"ai_gap_{cand['id']}", type="primary", width="stretch"):
                            if missing:
                                with st.spinner("Asking Ollama AI for recommendations…"):
                                    prompt = (
                                        f"A candidate named {cand.get('name')} is applying for the role of "
                                        f"'{gap_job.get('title')}' at {gap_job.get('department')} department. "
                                        f"They are missing the following skills: {', '.join(missing)}. "
                                        f"Provide a concise, actionable upskilling plan (3-5 bullet points) "
                                        f"with specific courses or resources they can use to close these gaps. "
                                        f"Be direct and practical."
                                    )
                                    advice = call_ollama(prompt)
                                    st.session_state[f"gap_advice_{cand['id']}"] = advice

                        if st.session_state.get(f"gap_advice_{cand['id']}"):
                            with st.container(border=True):
                                st.markdown("**<i class='fa-solid fa-robot' style='color:#6366F1; margin-right:6px;'></i> AI Upskilling Recommendations:**", unsafe_allow_html=True)
                                st.write(st.session_state[f"gap_advice_{cand['id']}"])

                # ── Chat with Resume Tab ──────────────────────────────────────
                with tab_chat:
                    st.markdown("#### <i class='fa-solid fa-comments' style='color:#6366F1; margin-right:8px;'></i> Chat with Resume using AI", unsafe_allow_html=True)
                    if not has_resume:
                        st.warning("No resume uploaded for this candidate. Please upload via the Resume Parser page first.")
                    else:
                        st.caption(f"Ask anything about **{cand.get('name')}'s** resume. Powered by Ollama ({cand.get('name', 'Candidate')}).")

                        # Initialize chat history
                        chat_key = f"chat_history_{cand['id']}"
                        if chat_key not in st.session_state:
                            st.session_state[chat_key] = []

                        # Render chat history
                        chat_container = st.container(height=300)
                        with chat_container:
                            if not st.session_state[chat_key]:
                                st.markdown(
                                    "<div style='text-align:center; color:#94A3B8; padding:40px 0; font-size:0.85rem;'>"
                                    "Ask a question about the candidate's resume…</div>",
                                    unsafe_allow_html=True
                                )
                            for msg in st.session_state[chat_key]:
                                role_label = "🧑 You" if msg["role"] == "user" else "🤖 AI"
                                bg = "#EEF2FF" if msg["role"] == "user" else "#F8FAFC"
                                border = "#6366F1" if msg["role"] == "user" else "#E2E8F0"
                                align = "flex-end" if msg["role"] == "user" else "flex-start"
                                st.markdown(f"""
                                <div style="display:flex; justify-content:{align}; margin-bottom:8px;">
                                    <div style="max-width:90%; background:{bg}; border:1px solid {border};
                                                border-radius:12px; padding:8px 12px; font-size:0.82rem; color:#0F172A;">
                                        <div style="font-size:0.68rem; color:#94A3B8; font-weight:600; margin-bottom:3px;">{role_label}</div>
                                        {msg['content']}
                                    </div>
                                </div>
                                """, unsafe_allow_html=True)

                        # Input area
                        with st.form(key=f"chat_form_{cand['id']}", clear_on_submit=True):
                            cf1, cf2 = st.columns([5, 1])
                            with cf1:
                                user_q = st.text_input(
                                    "Your question",
                                    placeholder="e.g. Does this candidate have FastAPI experience?",
                                    label_visibility="collapsed"
                                )
                            with cf2:
                                send = st.form_submit_button("Send ➤", width="stretch")

                        if send and user_q.strip():
                            st.session_state[chat_key].append({"role": "user", "content": user_q.strip()})
                            with st.spinner("AI is reading the resume…"):
                                context = resume_text[:3000] if resume_text else (
                                    f"Candidate: {cand.get('name')}, Title: {cand.get('current_title')}, "
                                    f"Skills: {', '.join(s.get('name') if isinstance(s, dict) else s for s in cand.get('skills', []))}, "
                                    f"Experience: {cand.get('years_experience')} years"
                                )
                                prompt = (
                                    f"You are a recruitment assistant. Based on the following resume/candidate information, "
                                    f"answer the recruiter's question precisely and concisely.\n\n"
                                    f"RESUME/CANDIDATE INFO:\n{context}\n\n"
                                    f"QUESTION: {user_q.strip()}\n\n"
                                    f"ANSWER:"
                                )
                                answer = call_ollama(prompt)
                            st.session_state[chat_key].append({"role": "ai", "content": answer})
                            st.rerun()

                        if st.session_state.get(chat_key):
                            if st.button("🗑️ Clear Chat", key=f"clear_chat_{cand['id']}"):
                                st.session_state[chat_key] = []
                                st.rerun()

                # ── Timeline Tab ──────────────────────────────────────────────
                with tab_timeline:
                    st.markdown("**Activity Timeline:**")
                    timeline = [{"title": "Application Started", "desc": "Candidate profile registered.", "time": cand.get("created_at")}]
                    for note in cand.get("notes", []):
                        timeline.append({"title": f"Note by {note.get('author')}", "desc": note.get("note"), "time": note.get("created_at")})
                    timeline.sort(key=lambda t: t.get("time", ""), reverse=True)

                    for idx, event in enumerate(timeline):
                        try:
                            time_str = datetime.datetime.fromisoformat(event["time"]).strftime("%b %d, %H:%M") if event.get("time") else "Just now"
                        except Exception:
                            time_str = "Just now"
                        with st.container(border=True):
                            st.markdown(f"**{event['title']}**")
                            st.caption(f"{event['desc']}  —  {time_str}")

                # ── Notes Tab ────────────────────────────────────────────────
                with tab_notes:
                    st.markdown("**Recruiter Notes:**")
                    new_note = st.text_area("Write note...", placeholder="Enter review remarks...", label_visibility="collapsed", key="drawer_note_input")
                    if st.button("Save Note", type="primary", width="stretch"):
                        if new_note.strip():
                            res = api_client.add_candidate_note(cand["id"], new_note.strip())
                            if res:
                                st.toast("Note appended!", icon="📝")
                                st.rerun()

                    notes = cand.get("notes", [])
                    for n in notes:
                        try:
                            time_str = datetime.datetime.fromisoformat(n["created_at"]).strftime("%b %d, %H:%M") if n.get("created_at") else "Just now"
                        except Exception:
                            time_str = "Just now"
                        with st.container(border=True):
                            nc1, nc2 = st.columns([3, 1])
                            with nc1:
                                st.markdown(f"**{n.get('author', 'Recruiter')}**")
                                st.write(n.get("note"))
                            with nc2:
                                st.caption(time_str)

                    if not notes:
                        st.info("No notes added yet.")
