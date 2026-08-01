import streamlit as st

def render_public_navbar(active_page: str = "home"):
    """Render the top navigation bar for the public website.

    Args:
        active_page: The current page identifier (e.g., "home", "about", "careers").
    """
    # Use simple HTML with query parameters for navigation. Streamlit will reload on link click.
    st.markdown(
        f"""
        <nav class="hp-navbar" id="hp-navbar">
          <div class="hp-navbar-inner">
            <a href="?public_page=home" class="hp-navbar-logo">
              <div class="logo-icon">HP</div>
              HIREPILOT
              <div class="logo-subtext">AI Recruitment Platform</div>
            </a>
            <div class="hp-navbar-links">
              <a href="?public_page=home" class="{'active' if active_page == 'home' else ''}">Home</a>
              <a href="?public_page=about" class="{'active' if active_page == 'about' else ''}">About Us</a>
              <a href="?public_page=careers" class="{'active' if active_page == 'careers' else ''}">Careers</a>
            </div>
            <div class="hp-navbar-actions">
              <a href="?public_page=hr_login" class="hp-btn hp-btn-primary">HR Sign In</a>
            </div>
          </div>
        </nav>
        """,
        unsafe_allow_html=True,
    )
