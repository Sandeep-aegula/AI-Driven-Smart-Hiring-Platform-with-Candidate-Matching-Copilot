import streamlit as st

def _render_public_footer():
    """Render the shared footer for public pages."""
    st.markdown(
        """
        <footer class=\"hp-footer\">
          <div class=\"hp-container\">
            <div class=\"hp-footer-grid\">
              <div class=\"hp-footer-brand\">
                <h3>HIREPILOT</h3>
                <p>AI Recruitment and Talent Management Platform</p>
              </div>
              <div class=\"hp-footer-col\">
                <h4>Navigation</h4>
                <ul>
                  <li><a href=\"?public_page=home\">Home</a></li>
                  <li><a href=\"?public_page=about\">About Us</a></li>
                  <li><a href=\"?public_page=careers\">Careers</a></li>
                </ul>
              </div>
              <div class=\"hp-footer-col\">
                <h4>For Candidates</h4>
                <ul>
                  <li><a href=\"?public_page=careers\">Browse Jobs</a></li>
                  <li><a href=\"?public_page=about\">Platform Features</a></li>
                </ul>
              </div>
              <div class=\"hp-footer-col\">
                <h4>For Companies</h4>
                <ul>
                  <li><a href=\"?public_page=hr_login\">Recruiter Portal</a></li>
                </ul>
              </div>
            </div>
            <div class=\"hp-footer-bottom\">
              <span>&copy; 2026 HIREPILOT. All rights reserved.</span>
            </div>
          </div>
        </footer>
        """,
        unsafe_allow_html=True,
    )
