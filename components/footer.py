import streamlit as st

def render_footer():
    """Renders Section 11: Dashboard Footer Component."""
    st.markdown("<!-- SECTION 11: FOOTER -->", unsafe_allow_html=True)
    st.markdown("<div style='border-top: 1px solid #E2E8F0; margin-top: 20px; margin-bottom: 16px;'></div>", unsafe_allow_html=True)

    f_col1, f_col2, f_col3 = st.columns(3)
    with f_col1:
        st.markdown("""
        <p style="font-size: 0.8rem; color: #64748B; margin: 0; font-weight: 500;">
            <b>AI Recruitment Copilot</b> • Version 1.0.0
        </p>
        """, unsafe_allow_html=True)
    with f_col2:
        st.markdown("""
        <p style="font-size: 0.8rem; color: #64748B; text-align: center; margin: 0; font-weight: 500;">
            Developed by <b>Sandeep Aegula</b>
        </p>
        """, unsafe_allow_html=True)
    with f_col3:
        st.markdown("""
        <p style="font-size: 0.8rem; color: #64748B; text-align: right; margin: 0; font-weight: 500;">
            Contact: <a href="mailto:support@copilot.example.com" style="color: #2563EB; text-decoration: none; font-weight: 600;">support@copilot.example.com</a>
        </p>
        <p style="font-size: 0.75rem; color: #94A3B8; text-align: right; margin: 2px 0 0 0;">
            &copy; 2026 AI Talent Copilot Inc. All rights reserved.
        </p>
        """, unsafe_allow_html=True)
