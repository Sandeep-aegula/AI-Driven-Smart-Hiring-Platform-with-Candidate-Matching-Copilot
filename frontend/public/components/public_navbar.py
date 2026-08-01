"""Public navigation bar for HirePilot's public-facing website.

This component renders a consistent top navigation bar across all public pages.
"""

import streamlit as st


def render_public_navbar(active_page="home"):
    """Render the public navigation bar.

    Args:
        active_page: The currently active public page key.
    """
    st.markdown(
        """
        <nav class="hp-navbar" id="hp-navbar">
          <div class="hp-navbar-inner">
            <a href="#home" class="hp-navbar-logo"
               onclick="document.getElementById('hp-mobile-menu').classList.remove('open')">
              <div class="logo-icon">HP</div>
              <div>
                <div class="logo-text">HIREPILOT</div>
                <div class="logo-subtext">AI Recruitment Platform</div>
              </div>
            </a>
            <button class="hp-navbar-toggle"
                    onclick="document.getElementById('hp-mobile-menu').classList.toggle('open')"
                    aria-label="Toggle menu">
              <span></span><span></span><span></span>
            </button>
            <div class="hp-navbar-links" id="hp-mobile-menu">
        """,
        unsafe_allow_html=True,
    )

    pages = [
        ("Home", "home", "home"),
        ("About Us", "about", "about"),
        ("Careers", "careers", "careers"),
    ]

    for label, anchor, key in pages:
        css_class = "active" if active_page == key else ""
        st.markdown(
            f'<a href="?public_page={key}" class="hp-navbar-links {css_class}" '
            f'onclick="document.getElementById(\'hp-mobile-menu\').classList.toggle(\'open\')">'
            f'{label}</a>',
            unsafe_allow_html=True,
        )

    st.markdown(
        """
        </div>
        <div class="hp-navbar-actions" id="hp-navbar-actions">
        """,
        unsafe_allow_html=True,
    )

    # HR Sign In button
    if st.button("HR Sign In", key="public_signin_btn", type="primary"):
        st.session_state.public_page = "hr_login"
        st.query_params["public_page"] = "hr_login"
        st.rerun()

    # Mobile sign-in button (hidden on desktop via CSS)
    st.markdown(
        """
        </div>
        </div>
        </nav>
        <div class="hp-navbar-actions" id="hp-mobile-actions" style="display:none;">
          <button class="hp-btn hp-btn-primary hp-btn-sm"
                  onclick="const ev = new Event('click'); document.getElementById('public_signin_btn').dispatchEvent(ev);">
            HR Sign In
          </button>
        </div>
        """,
        unsafe_allow_html=True,
    )
