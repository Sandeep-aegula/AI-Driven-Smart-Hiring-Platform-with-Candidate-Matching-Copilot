import datetime
import streamlit as st
import pandas as pd

from frontend.components import api_client
from frontend.services.cache import get_candidates_cached, get_jobs_cached

def _init_state():
    if "interview_view" not in st.session_state:
        st.session_state["interview_view"] = "List"
    if "selected_interview_id" not in st.session_state:
        st.session_state["selected_interview_id"] = None
    if "schedule_candidate_id" not in st.session_state:
        st.session_state["schedule_candidate_id"] = None

def _navigate_to(view, iv_id=None):
    st.session_state["interview_view"] = view
    if iv_id is not None:
        st.session_state["selected_interview_id"] = iv_id
    st.rerun()

def _render_list_view():
    st.markdown("<h3 style='margin-bottom:0;'>📋 Upcoming & Past Interviews</h3>", unsafe_allow_html=True)
    st.markdown("<p style='color:#64748B;'>Manage your interview schedule.</p>", unsafe_allow_html=True)
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        status_filter = st.selectbox("Status", ["All", "Scheduled", "Feedback Logged", "Completed", "Cancelled"])
    with col2:
        round_filter = st.selectbox("Round", ["All", "HR Screen", "Technical", "Coding", "Behavioral", "System Design", "Managerial"])
    with col3:
        st.write("")
        st.write("")
        if st.button("🔄 Refresh"):
            api_client.clear_interviews_cache()
            st.rerun()
    with col4:
        st.write("")
        st.write("")
        if st.button("➕ Schedule New", type="primary", width="stretch"):
            st.session_state["schedule_candidate_id"] = None
            _navigate_to("Schedule")
            
    # Need to get jobs and candidates to map IDs to Names
    cands = get_candidates_cached()
    cand_map = {c.get("id"): c.get("name", "Unknown") for c in cands if isinstance(c, dict)}
    jobs = get_jobs_cached()
    job_map = {j["id"]: j["title"] for j in jobs}
            
    interviews = api_client.get_interviews(status=status_filter, round_name=round_filter)
    
    if not interviews:
        st.info("No interviews found for the given filters.")
        return
        
    # Render table
    data = []
    for iv in interviews:
        job_id = iv.get("job_id")
        data.append({
            "ID": iv["id"],
            "Candidate": cand_map.get(iv.get("candidate_id"), f"Unknown ({iv.get('candidate_id', 'N/A')})"),
            "Job": job_map.get(job_id, f"Unknown ({job_id if job_id is not None else 'N/A'})"),
            "Round": iv.get("round", ""),
            "Date": iv.get("date", ""),
            "Time": iv.get("time", ""),
            "Status": iv.get("status", "")
        })
        
    df = pd.DataFrame(data)
    
    event = st.dataframe(
        df,
        width="stretch",
        hide_index=True,
        selection_mode="single-row",
        on_select="rerun"
    )
    
    sel_rows = event.selection.rows
    if sel_rows:
        row_idx = sel_rows[0]
        iv_id = df.iloc[row_idx]["ID"]
        if st.button(f"View Interview #{iv_id} Details", type="primary"):
            _navigate_to("Detail", iv_id)


def _render_schedule_view():
    st.markdown("<h3 style='margin-bottom:0;'>➕ Schedule New Interview</h3>", unsafe_allow_html=True)
    if st.button("← Back to List"):
        _navigate_to("List")
        
    cands = get_candidates_cached()
    jobs = get_jobs_cached()
    if not cands or not jobs:
        st.warning("Please ensure there are Candidates and Jobs in the system before scheduling.")
        return
        
    c_map = {c.get("name", "Unknown"): c.get("id") for c in cands if isinstance(c, dict)}
    j_map = {j["title"]: j["id"] for j in jobs}
    
    # Pre-fill logic
    prefill_cid = st.session_state.get("schedule_candidate_id")
    default_c_idx = 0
    if prefill_cid:
        for i, c in enumerate(cands):
            if isinstance(c, dict) and c.get("id") == prefill_cid:
                default_c_idx = i
                break
                
    with st.container(border=True):
        col1, col2 = st.columns(2)
        with col1:
            sel_cand_name = st.selectbox("Candidate *", list(c_map.keys()), index=default_c_idx)
            sel_job_title = st.selectbox("Job *", list(j_map.keys()))
            iv_round = st.selectbox("Round *", ["HR Screen", "Technical", "Coding", "Behavioral", "System Design", "Managerial"])
            iv_type = st.selectbox("Type", ["Online", "Offline"])
            platform = st.selectbox("Meeting Platform", ["Google Meet", "Zoom", "Microsoft Teams", "In-person"])
        with col2:
            date = st.date_input("Date *", min_value=datetime.date.today())
            time = st.time_input("Time *", value=datetime.time(10, 0))
            duration = st.number_input("Duration (mins) *", value=60, step=15)
            timezone = st.selectbox("Timezone", ["UTC", "America/New_York", "America/Los_Angeles", "Europe/London", "Asia/Kolkata"])
            
        link = st.text_input("Meeting Link (if Online)")
        recruiter = st.text_input("Interviewer Name(s) (comma separated)")
        instructions = st.text_area("Instructions for Candidate")
        
        if st.button("Schedule Interview", type="primary"):
            payload = {
                "candidate_id": c_map[sel_cand_name],
                "job_id": j_map[sel_job_title],
                "date": date.isoformat(),
                "time": time.strftime("%H:%M"),
                "duration": duration,
                "round": iv_round,
                "type": iv_type,
                "meeting_platform": platform,
                "meeting_link": link,
                "panel_members": [x.strip() for x in recruiter.split(",") if x.strip()],
                "recruiter_name": recruiter,
                "instructions": instructions,
                "timezone": timezone
            }
            res = api_client.schedule_interview(payload)
            if res:
                st.toast("Interview scheduled!", icon="✅")
                _navigate_to("List")


def _render_detail_view():
    iv_id = st.session_state.get("selected_interview_id")
    if not iv_id:
        st.warning("No interview selected.")
        _navigate_to("List")
        return
        
    iv = api_client.get_interview(iv_id)
    if not iv:
        st.error("Interview not found.")
        _navigate_to("List")
        return

    cands = get_candidates_cached()
    cand = next((c for c in cands if isinstance(c, dict) and c.get("id") == iv.get("candidate_id")), None)
    jobs = get_jobs_cached()
    job = next((j for j in jobs if isinstance(j, dict) and j.get("id") == iv.get("job_id")), None)

    cand_name = cand.get("name", "Unknown") if cand else f"Candidate {iv.get('candidate_id', 'N/A')}"
    job_title = job["title"] if job else f"Job {iv.get('job_id', 'N/A')}"

    st.markdown(f"<h3>{cand_name} - {iv.get('round')} Interview</h3>", unsafe_allow_html=True)
    if st.button("← Back to List"):
        _navigate_to("List")
        
    t1, t2, t3, t4 = st.tabs(["Schedule Info", "AI Questions", "Feedback & Decision", "Email"])
    
    with t1:
        st.markdown(f"""
        **Job**: {job_title}  
        **Status**: {iv.get('status')}  
        **Date**: {iv.get('date')}  
        **Time**: {iv.get('time')} ({iv.get('timezone', 'UTC')})  
        **Duration**: {iv.get('duration')} mins  
        **Platform**: {iv.get('meeting_platform')}  
        **Link**: [{iv.get('meeting_link')}]({iv.get('meeting_link')})  
        **Interviewer(s)**: {iv.get('recruiter_name')}  
        """)
        
    with t2:
        st.markdown("Generate targeted interview questions based on the candidate's resume and job requirements.")
        c1, c2, c3 = st.columns(3)
        round_options = ["HR", "Technical", "Coding", "Behavioral", "Managerial"]
        stored_round = iv.get("round") if iv.get("round") in round_options else "Technical"
        with c1: round_type = st.selectbox("Round type", round_options, index=round_options.index(stored_round))
        with c2: diff = st.selectbox("Difficulty", ["Easy", "Medium", "Hard"], index=1)
        with c3: num_q = st.number_input("Number of Questions", min_value=1, max_value=15, value=3)

        question_cache_key = f"{round_type.lower()}|{diff.lower()}|{int(num_q)}"
        
        if st.button("Generate Questions", type="primary"):
            with st.spinner("AI is generating questions..."):
                response = api_client.generate_interview_questions(iv_id, round_type, diff, int(num_q))
                if response and response.get("questions"):
                    st.success("Questions Generated!")
                    api_client.clear_interviews_cache()
                    st.rerun()
                else:
                    st.error("Failed to generate questions.")
                    
        qs_cached = iv.get("generated_question_sets", {}).get(question_cache_key, [])
        if qs_cached:
            st.markdown("### Generated Questions")
            for i, q in enumerate(qs_cached):
                with st.expander(f"Q{i+1}: {q.get('question', '')}"):
                    st.markdown("**Model Answer:**")
                    st.write(q.get("model_answer", ""))
                    st.markdown("**Evaluation Guideline:**")
                    st.write(q.get("evaluation_guideline", ""))

    with t3:
        fb = iv.get("feedback", {})
        with st.form("feedback_form"):
            st.markdown("#### Log Feedback")
            c1, c2 = st.columns(2)
            with c1:
                t = st.slider("Technical", 0, 10, int(fb.get("technical_evaluation", 0)))
                c = st.slider("Communication", 0, 10, int(fb.get("communication_rating", 0)))
                cd = st.slider("Coding", 0, 10, int(fb.get("coding_assessment", 0)))
            with c2:
                p = st.slider("Problem Solving", 0, 10, int(fb.get("problem_solving", 0)))
                b = st.slider("Behavioral", 0, 10, int(fb.get("behavioral_assessment", 0)))
                
            notes = st.text_area("Interview Notes", fb.get("interview_notes", ""))
            
            if st.form_submit_button("Save Feedback"):
                payload = {
                    "technical_evaluation": t, "communication_rating": c, 
                    "coding_assessment": cd, "problem_solving": p, "behavioral_assessment": b,
                    "interview_notes": notes
                }
                res = api_client.add_interview_feedback(iv_id, payload)
                if res:
                    st.toast("Feedback saved!")
                    api_client.clear_interviews_cache()
                    st.rerun()

        st.markdown("---")
        st.markdown("#### Final Decision")
        cur_dec = iv.get("decision", "")
        dec_opts = ["", "Selected", "Rejected", "Hold", "Next Round"]
        idx = dec_opts.index(cur_dec) if cur_dec in dec_opts else 0
        new_dec = st.selectbox("Decision", dec_opts, index=idx)
        if st.button("Log Decision"):
            if new_dec:
                res = api_client.log_interview_decision(iv_id, new_dec)
                if res:
                    st.success(f"Decision '{new_dec}' logged!")
                    api_client.clear_interviews_cache()
                    st.rerun()
            else:
                st.error("Please select a decision.")

    with t4:
        st.markdown("Draft an email to the candidate regarding this interview.")
        mode = "Result" if iv.get("decision") else "Invitation"
        mode_sel = st.selectbox("Email Mode", ["Invitation", "Result"], index=0 if mode == "Invitation" else 1)
        
        draft_key = f"iv_draft_{iv_id}_{mode_sel}"
        if st.button(f"Generate {mode_sel} Draft"):
            with st.spinner("Drafting email..."):
                draft = api_client.draft_interview_email(iv_id, mode_sel)
                if draft:
                    st.session_state[draft_key] = draft
                else:
                    st.error("Failed to generate draft.")
                    
        draft_data = st.session_state.get(draft_key)
        if draft_data:
            subj = st.text_input("Subject", value=draft_data.get("subject", ""))
            body = st.text_area("Body", value=draft_data.get("body", ""), height=250)
            if st.button("Send Email", type="primary"):
                with st.spinner("Sending..."):
                    res = api_client.send_interview_email(iv_id, subj, body)
                    if res:
                        st.success("Email sent! (Saved to candidate history)")
                        del st.session_state[draft_key]
                    else:
                        st.error("Failed to send email.")
                        
        st.markdown("#### Email History")
        history = api_client.get_interview_email_history(iv_id)
        if not history:
            st.info("No emails sent yet.")
        else:
            for h in history:
                with st.expander(f"{h.get('sent_at')} - {h.get('subject')}"):
                    st.text(h.get("body"))


def render_interview_management():
    _init_state()
    
    st.markdown("""
    <h1 style="font-size:1.6rem;font-weight:800;color:#0F172A;margin:0 0 4px 0;">
        📅 Interview Management
    </h1>
    <hr style="margin:0 0 20px 0;border:none;border-top:1px solid #F1F5F9;">
    """, unsafe_allow_html=True)
    
    view = st.session_state["interview_view"]
    if view == "List":
        _render_list_view()
    elif view == "Schedule":
        _render_schedule_view()
    elif view == "Detail":
        _render_detail_view()
