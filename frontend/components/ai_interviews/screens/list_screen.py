"""
AI Interview module — first screen.

Shows ONLY existing interview records with Round == "AI Interview", reusing
the existing GET /interviews endpoint (via frontend.components.api_client)
and the existing candidate/job caches. No duplicate candidate or interview
data is created or stored here.
"""
from __future__ import annotations

import streamlit as st

from frontend.components import api_client
from frontend.services.cache import get_candidates_cached, get_jobs_cached
from .. import state as ai_state

_TERMINAL_STATUSES = {"PASS", "FAIL"}


def render() -> None:
    st.markdown("""
    <h1 style="font-size:1.6rem;font-weight:800;color:#0F172A;margin:0 0 4px 0;">
        🤖 AI Interviews
    </h1>
    <hr style="margin:0 0 20px 0;border:none;border-top:1px solid #F1F5F9;">
    """, unsafe_allow_html=True)

    st.markdown(
        "<p style='color:#64748B;'>Select a scheduled AI Interview to begin.</p>",
        unsafe_allow_html=True,
    )

    if st.button("🔄 Refresh", key="ai_iv_list_refresh"):
        api_client.clear_interviews_cache()
        st.rerun()

    # Candidate/job enrichment + the interviews list itself are each a real
    # network round trip (and, on a cold cache, can take several seconds) --
    # without a visible loading state this reads as a hung/broken page
    # rather than "still working", so show one.
    with st.spinner("Loading AI interviews..."):
        cands = get_candidates_cached()
        cand_map = {c.get("id"): c for c in cands if isinstance(c, dict)}
        jobs = get_jobs_cached()
        job_map = {j["id"]: j["title"] for j in jobs}
        interviews = api_client.get_interviews(round_name="AI Interview")

    if not interviews:
        st.info("No AI interviews have been scheduled yet. Select \"AI Interview\" as the Round in Interviews → Schedule New to see it here.")
        return

    # Startable interviews (still "Scheduled") first, completed ones
    # (PASS/FAIL) after -- a stable sort keeps each group's original
    # relative order, it only reorders across the two groups.
    interviews = sorted(interviews, key=lambda iv: iv.get("status", "") in _TERMINAL_STATUSES)

    for iv in interviews:
        job_id = iv.get("job_id")
        cand = cand_map.get(iv.get("candidate_id"))
        candidate_name = cand.get("name", "Unknown") if cand else f"Unknown ({iv.get('candidate_id', 'N/A')})"

        # A candidate can only be scheduled for an interview by way of a real
        # application, and every application is tied to a real job -- so the
        # job always resolves. Fall back to the candidate's own job_title
        # (from their application) if the interview's own job_id doesn't
        # resolve, instead of showing an "Unknown" job.
        job_title = job_map.get(job_id) or (cand.get("job_title") if cand else None) or ""
        status = iv.get("status", "")

        with st.container(border=True):
            c1, c2 = st.columns([4, 1])
            with c1:
                st.markdown(f"**{candidate_name}**")
                if job_title:
                    st.caption(job_title)
                st.markdown(f"AI Interview &nbsp;·&nbsp; {iv.get('date', '')} {iv.get('time', '')}", unsafe_allow_html=True)
                st.caption(f"Status: {status}")
            with c2:
                if status in _TERMINAL_STATUSES:
                    st.metric("Result", status)
                else:
                    if st.button("Start AI Interview", key=f"ai_iv_start_{iv['id']}", type="primary"):
                        ai_state.reset_to_list()  # clear any stale prior session before selecting a new one
                        st.session_state["ai_iv_interview_id"] = iv["id"]
                        st.query_params["ai_iv_interview_id"] = str(iv["id"])
                        ai_state.go_to(ai_state.SCREEN_INSTRUCTIONS)
                        st.rerun()
