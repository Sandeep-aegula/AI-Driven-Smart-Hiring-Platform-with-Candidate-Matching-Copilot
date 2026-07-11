"""
components/interviews.py — HirePilot Interview Management Page
"""
import datetime
import streamlit as st
from frontend.components import api_client


def render_interviews() -> None:
    for key, val in [("selected_interview_id", None), ("generated_questions", None)]:
        if key not in st.session_state:
            st.session_state[key] = val

    st.markdown("""
    <h1 style="font-size:1.6rem;font-weight:800;color:#0F172A;margin:0 0 4px 0;">
        📅 Interview Management
    </h1>
    <p style="font-size:0.85rem;color:#64748B;margin:0 0 20px 0;font-weight:500;">
        Schedule and coordinate candidate interviews
    </p>
    <hr style="margin:0 0 20px 0;border:none;border-top:1px solid #F1F5F9;">
    """, unsafe_allow_html=True)

    candidates = api_client.get_candidates()
    interviews = api_client.get_interviews()

    col_left, col_right = st.columns([1.2, 0.8])

    # ── Left: Scheduled Sessions + Calendar + Timeline ────────────────────
    with col_left:
        st.markdown("<h4 style='font-size:1rem;font-weight:700;color:#0F172A;margin:0 0 12px 0;'>"
                    "<i class='fa-solid fa-clipboard-list' style='color:#6366F1;'></i>"
                    " Scheduled Sessions</h4>", unsafe_allow_html=True)
        if not interviews:
            st.markdown("<p style='color:#64748B;'>No interviews scheduled yet.</p>", unsafe_allow_html=True)
        else:
            for iv in interviews:
                sc = {"Scheduled":"#10B981","Completed":"#6366F1"}.get(iv.get("status",""),"#EF4444")
                with st.container(border=True):
                    r1, r2 = st.columns([3.5, 1.5])
                    with r1:
                        st.markdown(f"""
                        <div>
                            <span class="badge-blue" style="font-size:0.7rem;padding:2px 8px;border-radius:9999px;">
                                {iv.get('stage')}</span>
                            <div style="font-weight:800;font-size:1rem;color:#0F172A;margin-top:4px;">
                                {iv.get('candidate_name')}</div>
                            <div style="font-size:0.8rem;color:#64748B;margin-top:2px;">
                                <i class="fa-solid fa-clock"></i> {iv.get('date')} at {iv.get('time')} •
                                <strong>Interviewer:</strong> {iv.get('interviewer')}
                            </div>
                            <div style="font-size:0.75rem;color:#4F46E5;margin-top:4px;font-weight:600;">
                                <i class="fa-solid fa-link"></i>
                                <a href="{iv.get('meeting_link','#')}" target="_blank">{iv.get('meeting_link','')}</a>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                    with r2:
                        st.markdown(f"<div style='text-align:right;font-weight:700;color:{sc};font-size:0.8rem;'>"
                                    f"{iv.get('status')}</div>", unsafe_allow_html=True)
                        st.markdown("<div style='height:12px;'></div>", unsafe_allow_html=True)
                        if st.button("Feedback / Notes", key=f"feed_{iv.get('id')}", use_container_width=True):
                            st.session_state["selected_interview_id"] = iv.get("id")
                            st.rerun()
                st.markdown("<div style='height:8px;'></div>", unsafe_allow_html=True)

        # Calendar
        st.markdown("<div style='height:20px;'></div>", unsafe_allow_html=True)
        st.markdown("<h4 style='font-size:1rem;font-weight:700;color:#0F172A;margin:0 0 10px 0;'>"
                    "<i class='fa-solid fa-calendar' style='color:#6366F1;'></i> Monthly Overview</h4>",
                    unsafe_allow_html=True)
        days = ["Mon","Tue","Wed","Thu","Fri","Sat","Sun"]
        day_cols = st.columns(7)
        for i, d in enumerate(days):
            day_cols[i].markdown(f"<div style='text-align:center;font-weight:700;color:#475569;font-size:0.8rem;'>{d}</div>",
                                 unsafe_allow_html=True)
        cal = [["","","","1","2","3","4"],["5","6","7","8","9","10","11 📅"],
               ["12","13","14","15","16","17","18"],["19","20","21","22","23","24","25"],
               ["26","27","28","29","30","31",""]]
        for row in cal:
            rc = st.columns(7)
            for i, day in enumerate(row):
                bg  = "#F8FAFC" if day else "transparent"
                brd = "1px solid #E2E8F0" if day else "none"
                top = "border-top:3px solid #6366F1;" if "📅" in day else ""
                rc[i].markdown(f"""
                <div style="background:{bg};border:{brd};{top}border-radius:8px;
                            padding:8px;height:50px;font-size:0.78rem;font-weight:600;
                            color:#0F172A;margin-bottom:5px;">{day}</div>
                """, unsafe_allow_html=True)

        # Activity Timeline
        st.markdown("<div style='height:20px;'></div>", unsafe_allow_html=True)
        st.markdown("<h4 style='font-size:1rem;font-weight:700;color:#0F172A;margin:0 0 10px 0;'>"
                    "<i class='fa-solid fa-timeline' style='color:#6366F1;'></i> Timeline</h4>",
                    unsafe_allow_html=True)
        activities = [
            {"time":"Just now",     "title":"Interview scheduled",   "desc":"Technical Assessment — Sarah Jenkins."},
            {"time":"2 hours ago",  "title":"Feedback submitted",    "desc":"Ava Morgan submitted feedback on David Chen."},
            {"time":"Yesterday",    "title":"HR screening complete", "desc":"HR Culture Fit passed for Emily Taylor."},
        ]
        html = "<div style='display:flex;flex-direction:column;gap:12px;margin-top:10px;'>"
        for ev in activities:
            html += f"""
            <div style="display:flex;gap:10px;">
                <div style="display:flex;flex-direction:column;align-items:center;">
                    <div style="width:14px;height:14px;border-radius:50%;background:#6366F1;border:2.5px solid #EEF2FF;"></div>
                    <div style="width:1.5px;flex-grow:1;background:#E2E8F0;min-height:20px;"></div>
                </div>
                <div>
                    <span style="font-weight:700;color:#0F172A;font-size:0.8rem;">{ev['title']}</span>
                    <span style="font-size:0.72rem;color:#64748B;margin-left:8px;">{ev['time']}</span>
                    <div style="font-size:0.76rem;color:#475569;margin-top:1px;">{ev['desc']}</div>
                </div>
            </div>"""
        html += "</div>"
        st.markdown(html, unsafe_allow_html=True)

    # ── Right: Schedule Form + AI Questions + Feedback ────────────────────
    with col_right:
        with st.container(border=True):
            st.markdown("<h4 style='font-size:1rem;font-weight:700;color:#0F172A;margin:0 0 10px 0;'>"
                        "<i class='fa-solid fa-calendar-plus' style='color:#6366F1;'></i>"
                        " Schedule Interview</h4>", unsafe_allow_html=True)
            if not candidates:
                st.warning("Add candidates first.")
            else:
                cand_map   = {c["name"]: c["id"] for c in candidates}
                sel_cand   = st.selectbox("Candidate *", list(cand_map.keys()))
                stage      = st.selectbox("Stage", ["Technical Assessment","Coding Round","HR Culture Fit","System Design"])
                interviewer= st.text_input("Interviewer", value="Ava Morgan")
                dc, tc     = st.columns(2)
                with dc: date = st.date_input("Date", value=datetime.date.today() + datetime.timedelta(days=1))
                with tc: time = st.time_input("Time", value=datetime.time(10,0))
                meet_link  = st.text_input("Meeting Link", value="https://meet.google.com/abc-defg-hij")
                if st.button("Schedule Session", type="primary", use_container_width=True):
                    payload = {"candidate_id": cand_map[sel_cand], "interviewer": interviewer,
                               "date": date.isoformat(), "time": time.strftime("%H:%M"),
                               "stage": stage, "meeting_link": meet_link}
                    if api_client.schedule_interview(payload):
                        st.toast("Interview scheduled!", icon="🎉"); st.rerun()

        st.markdown("<div style='height:15px;'></div>", unsafe_allow_html=True)

        with st.container(border=True):
            st.markdown("<h4 style='font-size:1rem;font-weight:700;color:#0F172A;margin:0 0 6px 0;'>"
                        "<i class='fa-solid fa-wand-magic-sparkles' style='color:#6366F1;'></i>"
                        " Generate Interview Questions</h4>", unsafe_allow_html=True)
            st.markdown("<p style='font-size:0.8rem;color:#64748B;'>Generate questions based on candidate skills.</p>",
                        unsafe_allow_html=True)
            ai_stage  = st.selectbox("Category", ["Technical","Coding","Behavioral","HR"], key="ai_q_stage")
            ai_skills = st.text_input("Candidate Skills (comma separated)", value="Python, FastAPI, SQL")
            if st.button("Generate Questions with Ollama AI", type="secondary", use_container_width=True):
                with st.spinner("Generating…"):
                    skills_list = [s.strip() for s in ai_skills.split(",") if s.strip()]
                    res = api_client.generate_interview_questions(ai_stage, skills_list)
                    if res:
                        st.session_state["generated_questions"] = res
                        st.success("Questions generated!")
                    else:
                        st.error("Ollama generator failed.")
            if st.session_state.get("generated_questions"):
                st.markdown("<div style='margin-top:10px;background:#EEF2FF;border-left:3px solid #6366F1;"
                            "padding:10px;border-radius:4px;'>", unsafe_allow_html=True)
                for i, q in enumerate(st.session_state["generated_questions"]):
                    st.markdown(f"**Q{i+1}:** *{q}*")
                st.markdown("</div>", unsafe_allow_html=True)

        # Feedback Panel
        if st.session_state.get("selected_interview_id"):
            st.markdown("<div style='height:15px;'></div>", unsafe_allow_html=True)
            active = next((iv for iv in interviews
                           if iv.get("id") == st.session_state["selected_interview_id"]), None)
            if active:
                with st.container(border=True):
                    st.markdown(f"<h4 style='font-size:1rem;font-weight:700;color:#0F172A;margin:0 0 10px 0;'>"
                                f"<i class='fa-solid fa-comment-medical' style='color:#6366F1;'></i>"
                                f" Log Feedback: {active.get('candidate_name')}</h4>",
                                unsafe_allow_html=True)
                    feedback = st.text_area("Feedback Notes", value=active.get("feedback_notes",""),
                                            placeholder="Enter performance details…")
                    recs_opts = ["Select…","Approve","Shortlist","Reject"]
                    rec = st.selectbox("Recommendation", recs_opts,
                                       index=recs_opts.index(active.get("recommendation","Select…") or "Select…"))
                    fa1, fa2 = st.columns(2)
                    with fa1:
                        if st.button("Save Feedback", type="primary", use_container_width=True):
                            if rec == "Select…": st.error("Pick a recommendation.")
                            else:
                                r = api_client.add_interview_feedback(
                                    st.session_state["selected_interview_id"], feedback, rec)
                                if r:
                                    st.toast("Feedback saved!", icon="✅")
                                    st.session_state["selected_interview_id"] = None
                                    st.rerun()
                    with fa2:
                        if st.button("Cancel", use_container_width=True):
                            st.session_state["selected_interview_id"] = None; st.rerun()
