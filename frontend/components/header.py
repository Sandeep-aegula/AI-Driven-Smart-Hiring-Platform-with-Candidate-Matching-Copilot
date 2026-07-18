"""
shared/header.py — HirePilot Persistent Header
================================================
Renders the top bar: page breadcrumb, search, notifications,
current date, and theme toggle.

Called ONCE per rerun from app.py immediately after the sidebar.
Never re-initialises the sidebar or injects CSS.
"""

import datetime
import streamlit as st


# Page-label to breadcrumb mapping (emoji stripped for the breadcrumb display)
_PAGE_LABELS: dict[str, str] = {
    "Dashboard":     "Dashboard",
    "Jobs":          "Job Management",
    "Candidates":    "Candidate Profiles",
    "Resume Parser": "Resume Parser",
    "AI Screening":  "AI Screening",
    "Interviews":    "Interview Management",
    "Employees":     "Employee Roster",
    "Analytics":     "Analytics Dashboard",
    "Reports":       "Reports",
    "AI Copilot":    "AI Copilot",
    "About":         "About HirePilot",
}


def render_header() -> None:
    """
    Renders the persistent top header row using native Streamlit columns and text.
    """
    current = st.session_state.get("current_page", "Dashboard")
    page_label = _PAGE_LABELS.get(current, current)
    today_str = datetime.date.today().strftime("%b %d, %Y")

    # ── Row: breadcrumb (left) + controls (right) ─────────────────────────
    col_left, col_right = st.columns([6, 4])

    with col_left:
        st.markdown(f"📂 **Workspaces** / `{page_label}`")

    with col_right:
        if current == "Dashboard":
            col_space, col_info = st.columns([7, 3])
            with col_info:
                st.markdown(f"📅 `{today_str}`")
        else:
            col_search, col_info = st.columns([7, 3])



            with col_info:
                st.markdown(f"📅 `{today_str}`")

    # ── Divider ───────────────────────────────────────────────────────────
    st.divider()
