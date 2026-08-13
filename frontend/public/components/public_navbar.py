"""
_render_public_navbar.py — HirePilot Public Site Navbar
=========================================================

Renders the top navigation bar for the public-facing website
(Home, About Us, Careers, HR Sign In).

This is a standalone component so its CSS scoping and layout
can be edited independently of app.py.
"""

import streamlit as st


def _render_public_navbar(active_page: str, on_hr_sign_in=None) -> None:
    """
    Render the public site navbar.

    Args:
        active_page: one of "home", "about", "careers" — used to
            highlight the corresponding nav button.
        on_hr_sign_in: callback invoked when "HR Sign In" is clicked.
            Passed in from app.py so this file doesn't need to import
            open_hr_login() directly (avoids a circular import back
            into app.py).
    """
    st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)

    # Scoped CSS: only affects buttons inside this navbar's container,
    # not any other st.button() elsewhere on the site.
    st.markdown(
    """
    <style>
    div[class*="st-key-hp_public_navbar"] {
        position: fixed;
        top: 0;
        left: 0;
        right: 0;
        z-index: 1000;
        background: rgba(255, 255, 255, 0.95);
        backdrop-filter: blur(12px);
        -webkit-backdrop-filter: blur(12px);
        border-bottom: 1px solid #E2E8F0;
        padding: 1rem 2rem;
    }
    div[class*="st-key-hp_public_navbar"] button {
        padding: 0.5rem 1rem !important;
        border: none !important;
        box-shadow: none !important;
    }
    div[class*="st-key-hp_public_navbar"] button:focus {
        box-shadow: none !important;
        outline: none !important;
    }
    div[class*="st-key-hp_public_navbar"] button[kind="secondary"] {
        border: none !important;
        background: transparent !important;
    }
    div[class*="st-key-hp_public_navbar"] button[kind="secondary"]:hover {
        background: rgba(30, 64, 175, 0.06) !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

    with st.container(key="hp_public_navbar"):
        col_logo, col_nav, col_hr = st.columns([4, 3, 1], vertical_alignment="center")

        with col_logo:
            st.markdown(
                 """
                <div class="hp-navbar-logo" style="display: flex; flex-direction: row; align-items: center; gap: 8px; padding: 8px 0; text-align: left;">
                    <div style="background: #1E40AF; width: 36px; height: 36px; border-radius: 8px; display: flex; align-items: center; justify-content: center; color: white; font-weight: 800; font-size: 1rem; flex-shrink: 0;">HP</div>
                    <div>
                        <div style="font-size: 1.3rem; font-weight: 800; color: #1E40AF; line-height: 1.2;">HIREPILOT</div>
                        <div style="font-size: 0.75rem; font-weight: 500; color: #64748B; margin-top: 2px;">AI Recruitment Platform</div>
                    </div>
                </div>
                """,
    unsafe_allow_html=True,
)

        with col_nav:
            nav_cols = st.columns([1, 1, 1], vertical_alignment="center")
            with nav_cols[0]:
                if st.button("Home", key="nv_home", use_container_width=True,
                             type="primary" if active_page == "home" else "secondary"):
                    st.session_state.public_page = "Home"
                    st.rerun()
            with nav_cols[1]:
                if st.button("About Us", key="nv_about", use_container_width=True,
                             type="primary" if active_page == "about" else "secondary"):
                    st.session_state.public_page = "About Us"
                    st.rerun()
            with nav_cols[2]:
                if st.button("Careers", key="nv_car", use_container_width=True,
                             type="primary" if active_page == "careers" else "secondary"):
                    st.session_state.public_page = "Careers"
                    st.rerun()

        with col_hr:
            if st.button("HR Sign In", key="nv_hr", use_container_width=True, type="primary"):
                if on_hr_sign_in is not None:
                    on_hr_sign_in()

    st.markdown("<div style='height: 8px;'></div>", unsafe_allow_html=True)


# frontend/public/views/*.py (used by app1.py) import this function without the
# leading underscore, while frontend/app.py imports the underscored name above —
# both pre-existing, both still needed, so this alias satisfies both call sites
# without renaming (and breaking) either one.
render_public_navbar = _render_public_navbar