import streamlit as st
import os
import sys
import datetime

# Setup path to import api_client
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
project_root = os.path.dirname(parent_dir)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from frontend.components import api_client
from frontend.services.cache import get_interviews_cached, get_candidates_cached, invalidate_interviews
from frontend.services.app_state import AppState
from frontend.components.page_utils import setup_page, render_sidebar_footer

# Page Config
st.set_page_config(
    page_title="Interview Management - HirePilot",
    page_icon="📅",
    layout="wide",
    initial_sidebar_state="expanded"
)

setup_page("Interview Management", "Schedule and coordinate candidate interviews", page_key=__file__)

# State initialization
if "selected_interview_id" not in st.session_state:
    st.session_state.selected_interview_id = None
if "interview_question_sets" not in st.session_state:
    st.session_state.interview_question_sets = {}

# Load Candidates and Interviews
candidates = api_client.get_candidates()
interviews = api_client.get_interviews()
job_titles = {job.get("id"): job.get("title") for job in api_client.get_jobs()}

QUESTION_ROUNDS = ["HR", "Technical", "Coding", "Behavioral", "Managerial"]


def _interview_label(interview: dict) -> str:
    candidate = interview.get("candidate_name", "Unknown candidate")
    job = interview.get("job_title") or job_titles.get(interview.get("job_id")) or "Unknown (N/A)"
    round_name = interview.get("round") or interview.get("stage") or "Unspecified round"
    return f"{candidate} — {job} — {round_name} — {interview.get('date', 'Unknown date')}"


@st.fragment
def render_question_generator(interview_options: list[dict]):
    """Keep AI controls and generation isolated from the interview list above."""
    st.markdown("#### AI Interview Question Generator")
    if not interview_options:
        st.info("Schedule an interview to generate interview questions.")
        return

    ordered = sorted(interview_options, key=lambda item: f"{item.get('date', '')} {item.get('time', '')}", reverse=True)
    selected_id = st.selectbox(
        "Interview",
        options=[item.get("id") for item in ordered],
        index=0,
        format_func=lambda interview_id: _interview_label(next(item for item in ordered if item.get("id") == interview_id)),
        key="ai_question_interview",
    )
    selected = next(item for item in ordered if item.get("id") == selected_id)
    stored_round = selected.get("round")
    round_index = QUESTION_ROUNDS.index(stored_round) if stored_round in QUESTION_ROUNDS else QUESTION_ROUNDS.index("Technical")

    controls = st.columns(3)
    with controls[0]:
        round_type = st.selectbox("Round type", QUESTION_ROUNDS, index=round_index, key=f"ai_question_round_{selected_id}")
    with controls[1]:
        difficulty = st.selectbox("Difficulty", ["Easy", "Medium", "Hard"], index=1, key=f"ai_question_difficulty_{selected_id}")
    with controls[2]:
        count = st.number_input("Number of questions", min_value=1, max_value=15, value=5, step=1, key=f"ai_question_count_{selected_id}")

    resolved_job_title = selected.get("job_title") or job_titles.get(selected.get("job_id"))
    job_unresolved = not selected.get("job_id") or not resolved_job_title or resolved_job_title == "Unknown (N/A)"
    if job_unresolved:
        st.warning("This interview has an unresolved job (Unknown (N/A)). Link it to a job before generating role-specific questions.")

    cache_key = (selected_id, round_type, difficulty, int(count))
    actions = st.container(horizontal=True)
    with actions:
        generate_clicked = st.button("Generate Questions", type="primary", disabled=job_unresolved, key=f"generate_questions_{selected_id}")
        regenerate_clicked = st.button("Regenerate", disabled=job_unresolved, key=f"regenerate_questions_{selected_id}")

    if generate_clicked or regenerate_clicked:
        with st.spinner("Qwen2.5-Coder is generating interview questions..."):
            response = api_client.generate_interview_questions(
                selected_id, round_type, difficulty, int(count), regenerate=regenerate_clicked
            )
        if response:
            st.session_state.interview_question_sets[cache_key] = response
        else:
            st.error("Question generation could not be completed. Please try again.")

    result = st.session_state.interview_question_sets.get(cache_key)
    if result:
        if result.get("warning"):
            st.warning(result["warning"])
        if result.get("cached"):
            st.caption("Showing the saved question set for this interview configuration.")
        for index, question in enumerate(result.get("questions", []), start=1):
            with st.expander(f"{index}. {question.get('question', 'Interview question')}"):
                st.markdown("**Model answer**")
                st.write(question.get("model_answer", ""))
                st.markdown("**Evaluation guideline**")
                st.write(question.get("evaluation_guideline", ""))

# Divide screen into Left list/calendar and Right forms/AI utilities
col_left, col_right = st.columns([1.2, 0.8])

with col_left:
    # 1. Today's & Upcoming Interviews
    st.markdown("#### <i class='fa-solid fa-clipboard-list' style='color:#6366F1;'></i> Upcoming & Past Interviews", unsafe_allow_html=True)
    if not interviews:
        st.markdown("<p style='color:#64748B;'>No interviews scheduled.</p>", unsafe_allow_html=True)
    else:
        for idx, i in enumerate(interviews):
            status_color = "#10B981" if i.get("status") == "Scheduled" else ("#6366F1" if i.get("status") == "Completed" else "#EF4444")
            
            with st.container(border=True):
                c_row1, c_row2 = st.columns([3.5, 1.5])
                with c_row1:
                    st.markdown(f"""
                    <div>
                        <span class="badge-blue" style="font-size:0.7rem; padding:2px 8px; border-radius:9999px;">{i.get('stage')}</span>
                        <div style="font-weight: 800; font-size: 1.05rem; color:#0F172A; margin-top:4px;">{i.get('candidate_name')}</div>
                        <div style="font-size: 0.8rem; color: #64748B; margin-top:2px;">
                            <i class="fa-solid fa-clock"></i> {i.get('date')} at {i.get('time')} • <strong>Interviewer:</strong> {i.get('interviewer')}
                        </div>
                        <div style="font-size:0.75rem; color:#4F46E5; margin-top:4px; font-weight:600;">
                            <i class="fa-solid fa-link"></i> <a href="{i.get('meeting_link')}" target="_blank">{i.get('meeting_link')}</a>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                with c_row2:
                    st.markdown(f"<div style='text-align:right; font-weight:700; color:{status_color}; font-size:0.8rem;'>{i.get('status')}</div>", unsafe_allow_html=True)
                    st.markdown("<div style='height:12px;'></div>", unsafe_allow_html=True)
                    
                    # Selection triggers for logging feedback
                    if st.button("Feedback / Notes", key=f"feed_btn_{i.get('id')}", width="stretch"):
                        st.session_state.selected_interview_id = i.get('id')
                        st.rerun()
                        
            st.markdown("<div style='height:8px;'></div>", unsafe_allow_html=True)

    st.markdown("<div style='height: 15px;'></div>", unsafe_allow_html=True)
    with st.container(border=True):
        render_question_generator(interviews)

    # 2. Calendar Widget Grid
    st.markdown("<div style='height: 20px;'></div>", unsafe_allow_html=True)
    st.markdown("#### <i class='fa-solid fa-calendar' style='color:#6366F1;'></i> Monthly Overview", unsafe_allow_html=True)
    
    # Render mock calendar slots (7 columns: Mon-Sun)
    days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    cols_cal = st.columns(7)
    for index, d in enumerate(days):
        cols_cal[index].markdown(f"<div style='text-align:center; font-weight:700; color:#475569; font-size:0.8rem;'>{d}</div>", unsafe_allow_html=True)
        
    cal_grid = [
        ["", "", "", "1", "2", "3", "4"],
        ["5", "6", "7", "8", "9", "10", "11 📅"],
        ["12", "13", "14", "15", "16", "17", "18"],
        ["19", "20", "21", "22", "23", "24", "25"],
        ["26", "27", "28", "29", "30", "31", ""]
    ]
    for row in cal_grid:
        cols_row = st.columns(7)
        for index, day in enumerate(row):
            bg_color = "#F8FAFC" if day else "transparent"
            border = "1px solid #E2E8F0" if day else "none"
            accent_border = "border-top: 3px solid #6366F1;" if "📅" in day else ""
            cols_row[index].markdown(f"""
            <div style="background-color: {bg_color}; border: {border}; {accent_border} border-radius: 8px; padding: 8px; height: 50px; font-size: 0.78rem; font-weight: 600; color: #0F172A; text-align: left; margin-bottom: 5px;">
                {day}
            </div>
            """, unsafe_allow_html=True)

    # 3. Timeline History
    st.markdown("<div style='height: 20px;'></div>", unsafe_allow_html=True)
    st.markdown("#### <i class='fa-solid fa-timeline' style='color:#6366F1; margin-right:8px;'></i> Timeline Activities", unsafe_allow_html=True)
    activities = [
        {"time": "Just now",     "icon": "fa-calendar-days", "color": "#6366F1", "title": "Interview scheduled",       "desc": "Technical Assessment scheduled with Sarah Jenkins."},
        {"time": "2 hours ago",  "icon": "fa-comment-dots",   "color": "#10B981", "title": "Feedback submitted",         "desc": "Ava Morgan submitted feedback on candidate David Chen."},
        {"time": "Yesterday",    "icon": "fa-circle-check",  "color": "#3B82F6", "title": "HR screening completed",     "desc": "HR Culture Fit passed for Emily Taylor."}
    ]
    for event in activities:
        with st.container(border=True):
            tc1, tc2 = st.columns([4, 1])
            with tc1:
                st.markdown(f"<i class='fa-solid {event['icon']}' style='color:{event['color']}; margin-right:8px;'></i> **{event['title']}**", unsafe_allow_html=True)
                st.caption(event['desc'])
            with tc2:
                st.caption(event['time'])

with col_right:
    # 1. Schedule Interview Form
    with st.container(border=True):
        st.markdown("#### <i class='fa-solid fa-calendar-plus' style='color:#6366F1; margin-right:8px;'></i> Schedule Interview", unsafe_allow_html=True)
        
        if not candidates:
            st.warning("Please add candidates first.")
        else:
            cand_map = {c["name"]: c["id"] for c in candidates}
            selected_cand = st.selectbox("Candidate *", list(cand_map.keys()))
            stage = st.selectbox("Interview Stage", ["Technical Assessment", "Coding Round", "HR Culture Fit", "System Design"])
            interviewer = st.text_input("Assign Interviewer", value="Ava Morgan")
            
            c_date, c_time = st.columns(2)
            with c_date:
                date = st.date_input("Interview Date", value=datetime.date.today() + datetime.timedelta(days=1))
            with c_time:
                time = st.time_input("Interview Time", value=datetime.time(10, 0))
                
            meet_link = st.text_input("Meeting Link", value="https://meet.google.com/abc-defg-hij")
            
            if st.button("Schedule Session", type="primary", width="stretch"):
                payload = {
                    "candidate_id": cand_map[selected_cand],
                    "interviewer": interviewer,
                    "date": date.isoformat(),
                    "time": time.strftime("%H:%M"),
                    "stage": stage,
                    "meeting_link": meet_link
                }
                res = api_client.schedule_interview(payload)
                if res:
                    st.toast("Interview successfully scheduled!", icon="🎉")
                    st.rerun()

    # 2. Log Feedback Notes & Recommendation
    if st.session_state.selected_interview_id:
        st.markdown("<div style='height: 15px;'></div>", unsafe_allow_html=True)
        
        # Load active interview details
        active_int = next((i for i in interviews if i.get("id") == st.session_state.selected_interview_id), None)
        if active_int:
            with st.container(border=True):
                st.markdown(f"#### <i class='fa-solid fa-comment-medical' style='color:#6366F1; margin-right:8px;'></i> Log Feedback: {active_int.get('candidate_name')}", unsafe_allow_html=True)
                
                feedback = st.text_area("Feedback Notes", value=active_int.get("feedback_notes", ""), placeholder="Enter candidate performance details...")
                recommendation = st.selectbox("Recommendation", ["Select...", "Approve", "Shortlist", "Reject"], index=["Select...", "Approve", "Shortlist", "Reject"].index(active_int.get("recommendation", "Select...") or "Select..."))
                
                c_act1, c_act2 = st.columns(2)
                with c_act1:
                    if st.button("Save Feedback", type="primary", width="stretch"):
                        if recommendation == "Select...":
                            st.error("Please pick a recommendation.")
                        else:
                            res = api_client.add_interview_feedback(st.session_state.selected_interview_id, feedback, recommendation)
                            if res:
                                st.toast("Feedback logged successfully!", icon="✅")
                                st.session_state.selected_interview_id = None
                                st.rerun()
                with c_act2:
                    if st.button("Cancel Log", width="stretch"):
                        st.session_state.selected_interview_id = None
                        st.rerun()
