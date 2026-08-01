import streamlit as st

_NAV_ITEMS = [
    "Dashboard",
    "Jobs",
    "Candidates",
    "Resume Parser",
    "AI Screening",
    "Interviews",
    "Employees",
    "Analytics",
    "Reports",
    "AI Copilot"
]

def render_sidebar():

    current = st.session_state.get("current_page", "Dashboard")

    with st.sidebar:

        st.title("HirePilot")
        st.caption("AI Recruitment & Talent Management")

        st.divider()

        st.caption("NAVIGATION")

        for page in _NAV_ITEMS:

            if page == current:
                label = f" {page}"
            else:
                label = page

            # if st.button(
            #     label,
            #     key=f"nav_{page}",
            #     width="stretch",
            #     type="tertiary",
            # ):
                st.session_state.current_page = page
                st.rerun()

        st.divider()

        st.caption("ACCOUNT")

        if st.button(
            "Logout",
            key="logout",
            width="stretch",
            type="tertiary",
        ):
            st.session_state.current_page = "Dashboard"
            st.rerun()