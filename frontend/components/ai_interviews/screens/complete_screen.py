"""
AI Interview module — completion screen.

Displays the final PASS/FAIL result. By this point the backend has already
written this same result to the existing interview record's existing
`status` field -- this screen does not perform any write itself.
"""
from __future__ import annotations

import streamlit as st

from .. import state as ai_state


def render() -> None:
    result = st.session_state.get("ai_iv_result", "")

    st.markdown("### Interview Completed")
    st.write("Thank you for completing your AI interview.")

    if result == "PASS":
        st.success("Result: PASS")
    elif result == "FAIL":
        st.error("Result: FAIL")
    else:
        st.info("Result: Pending")

    st.caption("This result has been recorded on the interview's existing record and is visible on the Interviews page.")

    if st.button("← Back to AI Interviews", type="primary", key="ai_iv_complete_back"):
        ai_state.reset_to_list()
        st.rerun()
