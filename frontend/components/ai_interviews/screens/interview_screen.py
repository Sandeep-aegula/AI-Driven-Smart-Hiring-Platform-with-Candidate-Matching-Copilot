"""
AI Interview module — the live interview screen.

Fully automatic, voice-only, real-time flow rendered as an immersive
full-screen takeover (see _live_interview_component/index.html): a
human-like animated AI avatar speaks each question, the candidate's speech
is transcribed live, and after ~5 seconds of silence the answer is
automatically finalized and sent for evaluation -- no manual
Start/Stop/Submit buttons, no candidate camera.

This screen itself renders almost nothing in the normal Streamlit layout --
the component takes over the viewport while active. Only a tiny amount of
Python plumbing lives here: fetch the session, hand the current question to
the component, and process whatever finalized transcript it returns.
"""
from __future__ import annotations

import streamlit as st

from .. import api as ai_api
from .. import state as ai_state
from ..live_components import live_interview_widget


def render() -> None:
    # 1. Early check for back_to_list message to avoid rendering the widget again
    widget_val = st.session_state.get("ai_iv_live_widget")
    if widget_val and isinstance(widget_val, dict) and widget_val.get("type") == "back_to_list":
        ai_state.reset_to_list()
        st.rerun()
        return

    session = st.session_state.get("ai_iv_session")
    if not session:
        interview_id = st.session_state.get("ai_iv_interview_id")
        if interview_id:
            try:
                # Recovering from lost session state (e.g. a page refresh
                # mid-interview) -- resume the existing session unchanged
                # (fresh=False, the default). Do NOT pass fresh=True here:
                # that would wipe the candidate's in-progress answers just
                # because the tab reloaded.
                session = ai_api.start_or_resume_session(interview_id)
                st.session_state["ai_iv_session"] = session
            except Exception as exc:
                st.warning(f"Failed to restore AI interview session: {exc}")
                ai_state.go_to(ai_state.SCREEN_LIST)
                st.rerun()
                return
        else:
            st.warning("No active AI interview session.")
            ai_state.go_to(ai_state.SCREEN_LIST)
            st.rerun()
            return

    current_index = session["current_index"]
    total = session["target_question_count"]
    current_question = session["questions"][current_index]["question"]

    pending_error = st.session_state.get("ai_iv_answer_error")
    if pending_error:
        # Release the full-screen overlay while showing the retry prompt in
        # the normal page so the candidate has ordinary UI to click.
        live_interview_widget(
            question=current_question, question_index=current_index, total_questions=total,
            stop=True, key="ai_iv_live_widget",
        )
        st.error(pending_error)
        if st.button("🔁 Try Again", key="ai_iv_retry_answer"):
            st.session_state["ai_iv_answer_error"] = None
            st.rerun()
        return

    completed = bool(st.session_state.get("ai_iv_completed"))

    result = live_interview_widget(
        question=current_question,
        question_index=current_index,
        total_questions=total,
        completed=completed,
        result=st.session_state.get("ai_iv_result", "") or "",
        key="ai_iv_live_widget",
    )

    if completed:
        # The overlay is now showing its own completion view. Its "Back to
        # AI Interviews" button tears the overlay down itself (client-side,
        # synchronously) before sending this value, so it's always safe to
        # just reset state here -- no race with the overlay's teardown.
        if result and result.get("type") == "back_to_list":
            ai_state.reset_to_list()
            st.rerun()
        return

    already_processed = st.session_state.get("ai_iv_last_processed_seq")
    if (
        result
        and result.get("type") == "transcript_final"
        and result.get("question_index") == current_index
        and result.get("seq") != already_processed
    ):
        st.session_state["ai_iv_last_processed_seq"] = result.get("seq")
        transcript = (result.get("text") or "").strip()

        try:
            response = ai_api.submit_answer_text(session["id"], transcript)
        except Exception as exc:
            st.session_state["ai_iv_answer_error"] = str(exc)
            st.rerun()
            return

        if response.get("completed"):
            # Switch the SAME overlay into its completion view on the next
            # render instead of unmounting it -- see live_interview_widget's
            # docstring for why a stop=True + immediate rerun here would
            # race and can leave the overlay stuck on screen.
            st.session_state["ai_iv_result"] = response.get("result", "")
            st.session_state["ai_iv_completed"] = True
            st.query_params["ai_iv_result"] = response.get("result", "")
            st.query_params["ai_iv_completed"] = "True"
            st.rerun()
            return

        refreshed = ai_api.get_session(session["id"])
        if refreshed:
            st.session_state["ai_iv_session"] = refreshed
        st.rerun()
