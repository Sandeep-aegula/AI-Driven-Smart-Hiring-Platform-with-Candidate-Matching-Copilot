"""
AI Interview module — isolated session-state helpers.

All keys are namespaced with "ai_iv_" so this module can never collide with
any other page's st.session_state usage.
"""
from __future__ import annotations

import streamlit as st

SCREEN_LIST = "list"
SCREEN_INSTRUCTIONS = "instructions"
SCREEN_INTERVIEW = "interview"
SCREEN_COMPLETE = "complete"

_RESETTABLE_KEYS = (
    "ai_iv_interview_id",
    "ai_iv_session",
    "ai_iv_device_check_result",
    "ai_iv_context",
    "ai_iv_last_processed_seq",
    "ai_iv_answer_error",
    "ai_iv_result",
    "ai_iv_completed",
    "ai_iv_live_widget",
)


def init_state() -> None:
    # Restore screen from query parameters, but ONLY to seed a fresh session
    # (e.g. a hard page refresh, where st.session_state was wiped but the
    # URL still has ?ai_iv_screen=... on it). Once st.session_state already
    # holds a value, it must always win over the query string on every later
    # rerun -- otherwise a still-in-flight/stale browser URL (e.g. right
    # after reset_to_list() updates query params and calls st.rerun(), before
    # the browser has round-tripped the new URL back) can clobber a state
    # change we just made, snapping the screen right back to where it was.
    # This is exactly what caused "Back to AI Interviews" to appear to do
    # nothing but exit full-screen: reset_to_list() correctly flipped the
    # screen to SCREEN_LIST, but the next init_state() call re-read the old
    # ai_iv_screen=interview from the not-yet-updated URL and overwrote it.
    if "ai_iv_screen" not in st.session_state:
        st.session_state["ai_iv_screen"] = st.query_params.get("ai_iv_screen") or SCREEN_LIST

    for key in _RESETTABLE_KEYS:
        if key in st.session_state:
            continue
        q_val = st.query_params.get(key)
        if q_val is not None:
            if key == "ai_iv_completed":
                st.session_state[key] = (q_val.lower() == "true")
            elif key == "ai_iv_interview_id":
                try:
                    st.session_state[key] = int(q_val)
                except ValueError:
                    st.session_state[key] = q_val
            else:
                st.session_state[key] = q_val
        else:
            st.session_state[key] = None


def go_to(screen: str) -> None:
    st.session_state["ai_iv_screen"] = screen
    st.query_params["ai_iv_screen"] = screen


def reset_to_list() -> None:
    st.session_state["ai_iv_screen"] = SCREEN_LIST
    st.query_params["ai_iv_screen"] = SCREEN_LIST
    for key in _RESETTABLE_KEYS:
        st.session_state[key] = None
        if key in st.query_params:
            del st.query_params[key]
