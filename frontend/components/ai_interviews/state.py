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
    # Restoring screen from query parameters if available
    q_screen = st.query_params.get("ai_iv_screen")
    if q_screen:
        st.session_state["ai_iv_screen"] = q_screen
    else:
        st.session_state.setdefault("ai_iv_screen", SCREEN_LIST)

    for key in _RESETTABLE_KEYS:
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
            st.session_state.setdefault(key, None)


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
