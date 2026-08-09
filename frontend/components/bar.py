import logging
import streamlit as st

from frontend.components.api_client import clear_hr_session_state, logout_user

logger = logging.getLogger(__name__)

_NAV_ITEMS = (
    ("Dashboard", ":material/dashboard:"),
    ("Jobs", ":material/work:"),
    ("Candidates", ":material/groups:"),
    ("Resume Parser", ":material/description:"),
    ("AI Screening", ":material/psychology:"),
    ("Interviews", ":material/event:"),
    ("AI Interviews", ":material/videocam:"),
    ("Communications", ":material/mail:"),
    ("Onboarding", ":material/assignment_ind:"),
    ("Employees", ":material/badge:"),
    ("Analytics", ":material/analytics:"),
    ("Reports", ":material/assessment:"),
    ("AI Copilot", ":material/smart_toy:"),
)


def render_sidebar() -> None:
    """Render the persistent, app-level navigation sidebar."""
    current = st.session_state.get("current_page", "Dashboard")

    with st.sidebar:
        st.title("HirePilot")
        st.caption("AI recruitment and talent management")
        st.space("small")
        st.caption("NAVIGATION")

        for page, icon in _NAV_ITEMS:
            if st.button(
                f"{page} (current)" if page == current else page,
                icon=icon,
                key=f"nav_{page}",
                width="stretch",
                type="secondary",
            ):
                st.session_state["current_page"] = page
                st.query_params["current_page"] = page
                st.rerun()

        st.space("medium")
        st.caption("ACCOUNT")
        if st.button(
            "Logout",
            icon=":material/logout:",
            key="logout",
            width="stretch",
            type="tertiary",
        ):
            try:
                logout_user()
            except Exception as exc:
                logger.warning("Backend logout call failed: %s", exc)
            clear_hr_session_state()
            st.query_params.clear()
            st.rerun()
