"""Public navigation bar for HirePilot's public-facing website.

This component renders a consistent top navigation bar across all public pages.
"""

import streamlit as st


def render_public_navbar(active_page="home"):
    """Render the public navigation bar.

    Args:
        active_page: The currently active public page key.
    """
    # Single complete HTML block for the entire navbar
    nav_html = f"""
    <nav class="hp-navbar" id="hp-navbar">
      <div class="hp-navbar-inner">
        <a href="?public_page=home" class="hp-navbar-logo" onclick="document.getElementById('hp-mobile-menu').classList.remove('open')">
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
          <a href="?public_page=home" class="hp-navbar-links {'active' if active_page == 'home' else ''}"
             onclick="document.getElementById('hp-mobile-menu').classList.remove('open')">Home</a>
          <a href="?public_page=about" class="hp-navbar-links {'active' if active_page == 'about' else ''}"
             onclick="document.getElementById('hp-mobile-menu').classList.toggle('open')">About Us</a>
          <a href="?public_page=careers" class="hp-navbar-links {'active' if active_page == 'careers' else ''}"
             onclick="document.getElementById('hp-mobile-menu').classList.toggle('open')">Careers</a>
          <a href="?public_page=how-it-works" class="hp-navbar-links {'active' if active_page == 'how_it_works' else ''}"
             onclick="document.getElementById('hp-mobile-menu').classList.toggle('open')">How It Works</a>
          <a href="?public_page=contact" class="hp-navbar-links {'active' if active_page == 'contact' else ''}"
             onclick="document.getElementById('hp-mobile-menu').classList.toggle('open')">Contact</a>
        </div>
        <div class="hp-navbar-actions" id="hp-navbar-actions">
          <a href="?public_page=hr_login" class="hp-btn hp-btn-primary hp-btn-sm">HR Sign In</a>
        </div>
      </div>
    </nav>
    """
    st.markdown(nav_html, unsafe_allow_html=True)

    # Mobile sign-in button (hidden on desktop via CSS)
    st.markdown(
        """
        <div class="hp-navbar-actions" id="hp-mobile-actions" style="display:none;">
          <button class="hp-btn hp-btn-primary hp-btn-sm"
                  onclick="const ev = new Event('click'); document.getElementById('public_signin_btn').dispatchEvent(ev);">
            HR Sign In
          </button>
        </div>
        """,
        unsafe_allow_html=True,
    )
