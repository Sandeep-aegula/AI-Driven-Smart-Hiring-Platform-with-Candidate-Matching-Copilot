"""
AI Interview module — Python wrappers for the two isolated custom
Streamlit components (device check, live interview). These are the ONLY
custom components in the application and are used exclusively inside this
module.
"""
from __future__ import annotations

import os

import streamlit.components.v1 as components

_HERE = os.path.dirname(os.path.abspath(__file__))

_device_check_func = components.declare_component(
    "ai_interview_device_check", path=os.path.join(_HERE, "_device_check_component")
)
_live_interview_func = components.declare_component(
    "ai_interview_live", path=os.path.join(_HERE, "_live_interview_component")
)


def device_check_widget(key: str | None = None) -> dict | None:
    """Requests microphone permission and reports status.

    Returns a dict like {"microphone": bool} once resolved, or None before
    the browser has responded. No camera is requested.
    """
    return _device_check_func(key=key, default=None)


def live_interview_widget(
    question: str,
    question_index: int,
    total_questions: int,
    stop: bool = False,
    completed: bool = False,
    result: str = "",
    key: str | None = None,
) -> dict | None:
    """The immersive, full-screen live interview. Portals its UI directly
    into the parent document body (covering the normal HR dashboard chrome
    without modifying it) and drives TTS + live SpeechRecognition + a
    3-second silence timer entirely in the browser. No camera.

    Returns one of:
      - {"type": "transcript_final", "seq": int, "question_index": int,
        "text": str} when the candidate's answer has been finalized.
      - {"type": "back_to_list"} when the candidate dismisses the completion
        screen. This click tears the overlay down itself (client-side,
        synchronously) before this value is ever sent back to Python -- do
        NOT also call this widget with stop=True in response, that races the
        following st.rerun() and can leave the overlay stuck on screen (the
        overlay lives in the parent document, not this component's own
        iframe, so it survives the iframe being unmounted).
      - None otherwise.

    Pass completed=True + result="PASS"/"FAIL" once the final answer has
    been processed to switch the SAME overlay into its completion view
    (avatar hidden, result badge + "Back to AI Interviews" button) instead
    of tearing down and handing off to a separate Streamlit screen.

    stop=True is kept only for the "leave without finishing" abort path
    (e.g. an unrecoverable error) where no further interaction is expected.
    """
    return _live_interview_func(
        question=question,
        question_index=question_index,
        total_questions=total_questions,
        stop=stop,
        completed=completed,
        result=result,
        key=key,
        default=None,
    )
