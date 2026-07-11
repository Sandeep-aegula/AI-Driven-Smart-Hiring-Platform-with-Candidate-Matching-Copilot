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
    Renders the persistent top header row.
    Layout:  [Breadcrumb]  ···  [Search | Notifications | Date | Theme | Avatar]
    """
    current = st.session_state.get("current_page", "Dashboard")
    page_label = _PAGE_LABELS.get(current, current)
    today_str = datetime.date.today().strftime("%b %d, %Y")

    # ── Row: breadcrumb (left) + controls (right) ─────────────────────────
    col_left, col_right = st.columns([4, 6])

    with col_left:
        st.markdown(f"""
        <div class="hp-header-breadcrumb">
            <span class="hp-header-breadcrumb-root">
                <i class="fa-solid fa-layer-group"></i>&nbsp; Workspaces
            </span>
            <span class="hp-header-breadcrumb-sep">/</span>
            <span class="hp-header-breadcrumb-page">{page_label}</span>
        </div>
        """, unsafe_allow_html=True)

    with col_right:
        # ── Sub-columns: search | action icons ───────────────────────────
        col_search, col_icons = st.columns([5, 5])

        with col_search:
            st.session_state["search_query"] = st.text_input(
                label="Global search",
                placeholder="🔍  Search candidates, jobs, tags…",
                value=st.session_state.get("search_query", ""),
                label_visibility="collapsed",
                key="__header_search__",
            )

        with col_icons:
            st.markdown(f"""
            <div class="hp-header-right">
                <!-- Notification Bell -->
                <div class="hp-notif-btn" title="Notifications">
                    <i class="fa-regular fa-bell"></i>
                    <span class="hp-notif-badge"></span>
                </div>
                <!-- Date chip -->
                <div class="hp-date-chip">
                    <i class="fa-regular fa-calendar"></i>
                    {today_str}
                </div>
                <!-- Avatar -->
                <div class="hp-avatar" title="HR Recruiter">
                    HR
                </div>
            </div>
            """, unsafe_allow_html=True)

    # ── Divider ───────────────────────────────────────────────────────────
    st.markdown(
        "<hr style='margin:8px 0 20px 0; border:none; "
        "border-top:1px solid #F1F5F9;'>",
        unsafe_allow_html=True,
    )
