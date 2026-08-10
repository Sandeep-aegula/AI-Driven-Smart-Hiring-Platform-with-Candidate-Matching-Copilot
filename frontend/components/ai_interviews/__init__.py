"""
AI Interview module — isolated feature package.

render_ai_interviews() is the single entry point used by frontend/app.py's
existing routing (unchanged import path: from
frontend.components.ai_interviews import render_ai_interviews), matching
what every other page in this application already does.

Structure:
    api.py              isolated API client for the new /api/ai-interviews/* backend
    state.py            isolated st.session_state helpers (all keys prefixed ai_iv_)
    tts.py               isolated browser text-to-speech
    screens/
        list_screen.py          scheduled AI Interviews (Round == "AI Interview")
        instructions_screen.py  Before You Begin + microphone check
        interview_screen.py     the live voice interview
        complete_screen.py      final PASS/FAIL

No file outside this package is part of the AI Interview module.
"""
from __future__ import annotations

import streamlit as st

from . import state as ai_state
from .screens import list_screen, instructions_screen, interview_screen, complete_screen


def render_ai_interviews() -> None:
    ai_state.init_state()

    screen = st.session_state["ai_iv_screen"]

    if screen == ai_state.SCREEN_LIST:
        list_screen.render()
    elif screen == ai_state.SCREEN_INSTRUCTIONS:
        instructions_screen.render()
    elif screen == ai_state.SCREEN_INTERVIEW:
        interview_screen.render()
    elif screen == ai_state.SCREEN_COMPLETE:
        complete_screen.render()
    else:
        ai_state.reset_to_list()
        list_screen.render()
