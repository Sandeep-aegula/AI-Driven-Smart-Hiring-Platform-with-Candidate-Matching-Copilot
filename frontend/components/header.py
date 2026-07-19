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
        st.markdown(
            f"""
            <div style="display: flex; align-items: center; gap: 8px; font-size: 0.9rem;">
                <span style="color: #64748B;">📂 Workspaces</span>
                <span style="color: #94A3B8;">/</span>
                <span style="
                    background-color: #FFFFFF;
                    color: #111827;
                    border: 1px solid #E5E7EB;
                    border-radius: 8px;
                    padding: 6px 12px;
                    font-weight: 500;
                    font-size: 0.85rem;
                ">{page_label}</span>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col_right:
        if current == "Dashboard":
            col_space, col_info = st.columns([7, 3])
            with col_info:
                st.markdown(
                    f"""
                    <div style="display: flex; justify-content: flex-end; align-items: center;">
                        <span style="
                            background-color: #FFFFFF;
                            color: #111827;
                            border: 1px solid #E5E7EB;
                            border-radius: 8px;
                            padding: 8px 14px;
                            font-size: 0.85rem;
                            font-weight: 500;
                            display: flex;
                            align-items: center;
                            gap: 6px;
                        ">
                            <span style="color: #64748B;">📅</span>
                            <span>{today_str}</span>
                        </span>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
        else:
            col_search, col_info = st.columns([7, 3])

            with col_info:
                st.markdown(
                    f"""
                    <div style="display: flex; justify-content: flex-end; align-items: center;">
                        <span style="
                            background-color: #FFFFFF;
                            color: #111827;
                            border: 1px solid #E5E7EB;
                            border-radius: 8px;
                            padding: 8px 14px;
                            font-size: 0.85rem;
                            font-weight: 500;
                            display: flex;
                            align-items: center;
                            gap: 6px;
                        ">
                            <span style="color: #64748B;">📅</span>
                            <span>{today_str}</span>
                        </span>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

    # ── Divider ───────────────────────────────────────────────────────────
    st.divider()
