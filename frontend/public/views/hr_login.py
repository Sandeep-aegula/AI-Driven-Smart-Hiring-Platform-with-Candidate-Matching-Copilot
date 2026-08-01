import streamlit as st
from frontend.public.utils import inject_public_css

def render_page():
    """Render the HR Login page for the public website."""
    # Load CSS
    inject_public_css()
    
    st.markdown(
        """
        <div style="min-height: 100vh; display: flex; align-items: center; justify-content: center; background: linear-gradient(135deg, #F8FAFC 0%, #E2E8F0 100%); padding: 2rem;">
        """,
        unsafe_allow_html=True
    )
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown(
            """
            <div style="background: white; padding: 3rem; border-radius: 12px; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1), 0 2px 4px -1px rgba(0,0,0,0.06); text-align: center;">
                <div style="font-size: 3rem; margin-bottom: 1rem; color: #1E40AF;">HP</div>
                <h2 style="color: #0F172A; margin-bottom: 0.5rem; font-size: 2rem;">HirePilot HR Portal</h2>
                <p style="color: #64748B; margin-bottom: 2rem;">This portal is intended for authorized HR and recruitment personnel.</p>
            </div>
            """,
            unsafe_allow_html=True
        )
        
        with st.form("hr_login_form"):
            email = st.text_input("Email Address", placeholder="admin@hirepilot.com")
            password = st.text_input("Password", type="password", placeholder="••••••••")
            
            st.markdown("<br>", unsafe_allow_html=True)
            submit = st.form_submit_button("Sign In", type="primary", width="stretch")
            
            if submit:
                # Use the existing demo authentication logic
                try:
                    from frontend.components.api_client import login_user
                    token = login_user(email, password)
                    if token:
                        st.session_state.token = token
                        st.session_state.app_mode = "hr_portal"
                        # Clear public page routing state to let app.py show the HR dashboard
                        if "public_page" in st.session_state:
                            del st.session_state.public_page
                        st.query_params.clear()
                        st.rerun()
                    else:
                        st.error("Invalid email or password. Please try again.")
                except ImportError:
                    # Fallback if api_client is not yet fully available
                    if email == "admin@hirepilot.com" and password:
                        st.session_state.token = "demo-jwt-token-123"
                        st.session_state.app_mode = "hr_portal"
                        if "public_page" in st.session_state:
                            del st.session_state.public_page
                        st.query_params.clear()
                        st.rerun()
                    else:
                        st.error("Invalid email or password. Please try again.")

        if st.button("Back to Website", width="stretch"):
            st.session_state.public_page = "home"
            st.query_params["public_page"] = "home"
            st.rerun()

    st.markdown("</div>", unsafe_allow_html=True)
