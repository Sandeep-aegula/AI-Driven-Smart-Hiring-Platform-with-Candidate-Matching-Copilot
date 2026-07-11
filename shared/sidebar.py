"""
shared/sidebar.py — HirePilot Custom SPA Sidebar
==================================================
Enterprise SaaS navigation sidebar (Linear / Stripe / Notion inspired).

Rules:
  • NO st.radio, NO Streamlit pages, NO st.switch_page
  • Navigation is driven purely by st.session_state["current_page"]
  • Sidebar is rendered on EVERY rerun from app.py — Streamlit persists it
  • The sidebar does NOT trigger a full page reload
"""

import streamlit as st

# ── Navigation menu definition ───────────────────────────────────────────────
_NAV_ITEMS = [
    {"page": "Dashboard",      "icon": "\uf015", "label": "Dashboard"},
    {"page": "Jobs",           "icon": "\uf0b1", "label": "Jobs"},
    {"page": "Candidates",     "icon": "\uf0c0", "label": "Candidates"},
    {"page": "Resume Parser",  "icon": "\uf15c", "label": "Resume Parser"},
    {"page": "AI Screening",   "icon": "\uf544", "label": "AI Screening"},
    {"page": "Interviews",     "icon": "\uf133", "label": "Interviews"},
    {"page": "Employees",      "icon": "\uf2c2", "label": "Employees"},
    {"page": "Analytics",      "icon": "\uf201", "label": "Analytics"},
    {"page": "Reports",        "icon": "\uf56c", "label": "Reports"},
    {"page": "AI Copilot",     "icon": "\uf0d0", "label": "AI Copilot"},
]


def render_sidebar() -> None:
    """
    Render the persistent custom sidebar navigation.
    This is called once per rerun from app.py inside `with st.sidebar:`.
    """
    with st.sidebar:
        # ── Logo & Brand ──────────────────────────────────────────────────
        st.markdown("""
        <div style="
            display: flex; align-items: center; gap: 12px;
            padding: 20px 16px 18px 16px;
            border-bottom: 1px solid #1E293B;
        ">
            <div style="
                background: linear-gradient(135deg, #6366F1, #4F46E5);
                width: 38px; height: 38px; border-radius: 10px;
                display: flex; align-items: center; justify-content: center;
                font-size: 18px; color: white;
                box-shadow: 0 4px 14px rgba(99,102,241,0.40);
                flex-shrink: 0;
            ">
                <i class="fa-solid fa-paper-plane" style="transform: rotate(-10deg);"></i>
            </div>
            <div>
                <div style="font-weight:800; color:#F8FAFC; font-size:1.15rem;
                            letter-spacing:-0.01em; line-height:1;">HirePilot</div>
                <div style="font-size:0.6rem; color:#64748B; font-weight:600;
                            margin-top:3px; text-transform:uppercase;
                            letter-spacing:0.07em;">AI Recruitment &amp; Talent</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # ── Nav Label ─────────────────────────────────────────────────────
        st.markdown("""
        <div style="font-size:0.6rem; font-weight:700; color:#334155;
                    text-transform:uppercase; letter-spacing:0.10em;
                    padding: 14px 16px 6px 16px;">
            Main Navigation
        </div>
        """, unsafe_allow_html=True)

        current = st.session_state.get("current_page", "Dashboard")

        # ── Navigation Buttons ────────────────────────────────────────────
        for item in _NAV_ITEMS:
            page   = item["page"]
            icon   = item["icon"]
            label  = item["label"]
            is_active = current == page

            # Build CSS for this button inline via markdown + button
            if is_active:
                btn_style = """
                    background: linear-gradient(135deg,
                        rgba(99,102,241,0.22), rgba(79,70,229,0.16)) !important;
                    color: #FFFFFF !important;
                    border-left: 3px solid #6366F1 !important;
                    border-radius: 0 8px 8px 0 !important;
                    font-weight: 700 !important;
                    padding-left: 9px !important;
                """
            else:
                btn_style = """
                    background: transparent !important;
                    color: #94A3B8 !important;
                    border: none !important;
                    border-radius: 8px !important;
                    font-weight: 500 !important;
                """

            # Use st.button for click handling; style overridden via inline CSS
            st.markdown(f"""
            <style>
            div[data-testid="stButton"] > button[kind="secondary"][data-test-id="hp-nav-{page}"] {{
                {btn_style}
            }}
            </style>
            """, unsafe_allow_html=True)

            # Render as a full-width button
            col_pad, col_btn = st.columns([0.05, 0.95])
            with col_btn:
                clicked = st.button(
                    f"{icon}  {label}",
                    key=f"nav_{page}",
                    use_container_width=True,
                    type="secondary",
                    help=page,
                )

                if clicked and not is_active:
                    st.session_state["current_page"] = page
                    st.rerun()

        # ── Divider ───────────────────────────────────────────────────────
        st.markdown("""
        <div style="height:1px; background:#1E293B; margin: 10px 16px;"></div>
        """, unsafe_allow_html=True)

        # ── Bottom Profile Card ───────────────────────────────────────────
        st.markdown("""
        <div style="
            padding: 14px 16px;
            border-top: 1px solid #1E293B;
            display: flex;
            align-items: center;
            gap: 10px;
            margin-top: 8px;
        ">
            <div style="
                width: 34px; height: 34px; border-radius: 50%;
                background: linear-gradient(135deg, #6366F1, #4F46E5);
                display: flex; align-items: center; justify-content: center;
                font-size: 13px; font-weight: 800; color: white; flex-shrink: 0;
            ">HR</div>
            <div style="flex-grow:1; min-width:0;">
                <div style="font-weight:700; color:#E2E8F0; font-size:0.82rem;
                            line-height:1; white-space:nowrap; overflow:hidden;
                            text-overflow:ellipsis;">HR Recruiter</div>
                <div style="font-size:0.64rem; color:#64748B; margin-top:3px;
                            display:flex; align-items:center; gap:4px;">
                    <span style="width:6px; height:6px; border-radius:50%;
                                 background:#10B981; display:inline-block;
                                 flex-shrink:0;"></span>
                    Online
                </div>
            </div>
            <div style="
                font-size:0.6rem; color:#475569;
                background:#1E293B;
                padding:2px 8px; border-radius:9999px;
                font-weight:600; white-space:nowrap; flex-shrink:0;
            ">v1.0</div>
        </div>
        """, unsafe_allow_html=True)
