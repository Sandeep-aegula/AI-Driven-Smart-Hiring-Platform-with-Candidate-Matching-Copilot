import streamlit as st


_NAV_ITEMS = (
    ("Dashboard", ":material/dashboard:"),
    ("Jobs", ":material/work:"),
    ("Candidates", ":material/groups:"),
    ("Resume Parser", ":material/description:"),
    ("AI Screening", ":material/psychology:"),
    ("Interviews", ":material/event:"),
    ("Communications", ":material/mail:"),
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
            st.session_state["current_page"] = "Dashboard"
            st.rerun()
