import streamlit as st
import datetime

def render_header():
    """Renders Section 1: Dashboard Header Component."""
    st.markdown("<!-- SECTION 1: HEADER -->", unsafe_allow_html=True)
    header_col1, header_col2, header_col3 = st.columns([1, 4, 3])

    with header_col1:
        # Load the generated logo image dynamically
        import os
        current_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        logo_path = os.path.join(current_dir, "assets", "images", "logo.png")
        if os.path.exists(logo_path):
            st.image(logo_path, width=54)
        else:
            pass
            # st.markdown("""
            # <div style="display: flex; align-items: center; justify-content: center; height: 75px;">
            #     <div style="background-color: #2563EB; width: 50px; height: 50px; border-radius: 12px; display: flex; align-items: center; justify-content: center; font-size: 24px; font-weight: 800; color: white;">
            #         RC
            #     </div>
            # </div>
            # """, unsafe_allow_html=True)

    with header_col2:
        st.markdown("""
        <div style="padding-top: 5px;">
            <h1 style="font-size: 1.8rem; font-weight: 800; color: #0F172A; margin: 0; line-height: 1.2;">AI Recruitment & Talent Management Copilot</h1>
            <p style="font-size: 0.9rem; color: #64748B; margin: 2px 0 0 0; font-weight: 500;">Smart Resume Screening and Candidate Ranking System</p>
        </div>
        """, unsafe_allow_html=True)

    with header_col3:
        st.markdown("<div style='height: 5px;'></div>", unsafe_allow_html=True)
        head_c1, head_c2 = st.columns([7, 3])
        
        with head_c1:
            st.session_state.search_query = st.text_input(
                label="Search Box", 
                placeholder="Search candidate name, skills...", 
                value=st.session_state.search_query,
                label_visibility="collapsed",
                key="header_search_input"
            )
            
        with head_c2:
            today_str = datetime.date.today().strftime("%b %d, %Y")
            # Read profile picture if available
            profile_path = os.path.join(current_dir, "assets", "images", "profile.png")
            avatar_html = f'<div style="width: 32px; height: 32px; border-radius: 50%; background-color: #E2E8F0; display: flex; align-items: center; justify-content: center; font-weight: 700; font-size: 13px; color: #475569; border: 1px solid #CBD5E1;">AD</div>'
            
            # Since HTML img doesn't easily resolve local files unless served, we check and fallback to text avatar or base64. Let's keep it simple with text avatar or Font Awesome user icon:
            avatar_html = '<div style="width: 34px; height: 34px; border-radius: 50%; background-color: #EFF6FF; border: 1px solid #DBEAFE; display: flex; align-items: center; justify-content: center; color: #2563EB; font-size: 15px;"><i class="fa-solid fa-user"></i></div>'
            
            st.markdown(f"""
            <div style="display: flex; align-items: center; justify-content: flex-end; gap: 14px; height: 42px;">
                <div style="font-size: 18px; cursor: pointer; color: #64748B;" title="Notifications"><i class="fa-regular fa-bell"></i></div>
                <div style="cursor: pointer;" title="User Profile">
                    {avatar_html}
                </div>
            </div>
            <div style="text-align: right; font-size: 11px; color: #64748B; font-weight: 600; margin-top: 2px;">
                {today_str}
            </div>
            """, unsafe_allow_html=True)

    st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)
