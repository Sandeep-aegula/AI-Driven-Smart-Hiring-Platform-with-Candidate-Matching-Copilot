"""
AI Interview module — instructions + microphone check screen.

Voice-only interview: no camera is requested or used anywhere in this
module.
"""
from __future__ import annotations

import streamlit as st

from .. import api as ai_api
from .. import state as ai_state
from ..live_components import device_check_widget

# Must match backend/database/ai_interview_repository.py's create_session default.
QUESTION_COUNT = 8

GUIDELINES = [
    "This is a voice-only AI interview -- no camera is used.",
    "Use headphones if possible -- without them, your microphone can pick up the AI interviewer's own voice as it speaks.",
    "Keep your microphone enabled throughout the interview.",
    "Stay in a quiet environment with minimal background noise.",
    "Answer each question clearly and briefly.",
    "Do not use another person to answer on your behalf.",
    "Do not intentionally leave the interview screen.",
    "Make sure your internet connection is stable.",
    "Do not refresh or close the browser during the interview.",
    "Do not mute the microphone while answering.",
]


def render() -> None:
    st.markdown("""
    <div style="background:linear-gradient(135deg,#EEF2FF,#F5F3FF);border:1px solid #E0E7FF;
                border-radius:16px;padding:28px 32px;margin-bottom:20px;">
        <div style="font-size:0.8rem;font-weight:700;color:#6366F1;letter-spacing:0.06em;
                    text-transform:uppercase;margin-bottom:6px;">AI Interview &nbsp;·&nbsp; Step 1 of 2</div>
        <h2 style="margin:0 0 6px 0;color:#0F172A;">Before You Begin</h2>
        <p style="margin:0;color:#475569;">This is a live, voice-based AI interview. Review the
        guidelines below, then grant microphone access to continue.</p>
    </div>
    """, unsafe_allow_html=True)

    with st.container(border=True):
        st.markdown("#### 📋 Interview Guidelines")
        for line in GUIDELINES:
            st.markdown(f"- {line}")
        st.markdown(f"- This interview will ask **{QUESTION_COUNT} short questions**, one at a time.")
        st.markdown(
            "- The AI interviewer will speak each question aloud, and you answer with your voice -- "
            "there is no text box. The interview automatically moves to the next question a few "
            "seconds after you stop speaking; no submit button needed."
        )
        st.caption(
            "Note: momentary things like hesitation or nervousness are not used to judge your answers."
        )

    st.write("")

    with st.container(border=True):
        st.markdown("#### 🎙️ Microphone Check")
        st.caption("Your browser will ask for microphone access. It's required to continue.")
        result = device_check_widget(key="ai_iv_device_check")
        if result is not None:
            st.session_state["ai_iv_device_check_result"] = result

    status = st.session_state.get("ai_iv_device_check_result")
    mic_ok = bool(status and status.get("microphone"))

    if status is not None and not mic_ok:
        st.error("Microphone access is required for the AI interview.")

    st.write("")
    col1, col2 = st.columns([1, 1])
    with col1:
        if st.button("← Back", key="ai_iv_instructions_back"):
            ai_state.reset_to_list()
            st.rerun()
    with col2:
        if st.button("Start Interview", type="primary", disabled=not mic_ok, key="ai_iv_start_interview_btn"):
            interview_id = st.session_state["ai_iv_interview_id"]
            try:
                with st.spinner("Preparing your AI interview..."):
                    # Explicit "Start Interview" click -- always begin fresh,
                    # never silently resume old half-finished progress.
                    session = ai_api.start_or_resume_session(interview_id, fresh=True)
                st.session_state["ai_iv_session"] = session
                ai_state.go_to(ai_state.SCREEN_INTERVIEW)
                st.rerun()
            except Exception as exc:
                st.error(f"Unable to start the AI interview: {exc}")
        if not mic_ok:
            st.caption("The microphone check above must pass before you can start.")
