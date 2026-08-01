import streamlit as st
from frontend.public.utils import inject_public_css
from frontend.public.components.public_navbar import render_public_navbar
from frontend.public.components.public_footer import render_public_footer
from frontend.public.components.job_card import render_job_card
from frontend.public.data.mock_jobs import get_all_jobs

def render_page():
    """Render the Home page for the public website."""
    # Load CSS
    inject_public_css()
    # Show navbar with active page
    render_public_navbar(active_page="home")
    
    # 1. Hero Section
    st.markdown(
        """
        <section class="hp-hero" style="padding: 4rem 1rem; background: linear-gradient(135deg, #F8FAFC 0%, #E2E8F0 100%); text-align: center;">
          <div class="hp-container">
            <h1 style="font-size: 3rem; color: #0F172A; margin-bottom: 1rem;">Build Your Career With Us</h1>
            <p style="font-size: 1.25rem; color: #475569; max-width: 800px; margin: 0 auto 2rem auto;">
              Explore meaningful opportunities, discover exciting roles, and join teams building innovative solutions.
            </p>
          </div>
        </section>
        """,
        unsafe_allow_html=True,
    )
    
    col1, col2, col3, col4 = st.columns([1, 1, 1, 1])
    with col2:
        if st.button("Explore Jobs", width="stretch", type="primary"):
            st.session_state.public_page = "careers"
            st.query_params["public_page"] = "careers"
            st.rerun()
    with col3:
        if st.button("Learn About Us", width="stretch"):
            st.session_state.public_page = "about"
            st.query_params["public_page"] = "about"
            st.rerun()
            
    st.markdown("<br><br>", unsafe_allow_html=True)
            
    # 2. Company Introduction
    st.markdown(
        """
        <section class="hp-section" style="padding: 4rem 1rem; text-align: center;">
          <div class="hp-container">
            <h2 style="font-size: 2.25rem; color: #0F172A; margin-bottom: 1rem;">Empowering People and Building Great Teams</h2>
            <p style="font-size: 1.125rem; color: #475569; max-width: 800px; margin: 0 auto 2rem auto;">
              HirePilot helps organizations build strong teams through intelligent recruitment, efficient talent management, and AI-powered decision support.
            </p>
            <p style="font-size: 1rem; color: #64748B; max-width: 800px; margin: 0 auto;">
              We focus on <strong>Innovation</strong>, <strong>People</strong>, <strong>Technology</strong>, and <strong>Career growth</strong> to deliver a better hiring experience for everyone.
            </p>
          </div>
        </section>
        """,
        unsafe_allow_html=True,
    )

    # 3. Why Join Us
    st.markdown(
        """
        <section class="hp-section" style="padding: 4rem 1rem; background-color: #F8FAFC;">
          <div class="hp-container">
            <h2 style="font-size: 2rem; color: #0F172A; text-align: center; margin-bottom: 3rem;">Why Join Us</h2>
          </div>
        </section>
        """,
        unsafe_allow_html=True,
    )
    
    why_cols = st.columns(4)
    why_data = [
        ("Career Growth", "Support employees in developing skills and advancing their careers.", "📈"),
        ("Collaborative Culture", "Build meaningful solutions with talented and supportive teams.", "🤝"),
        ("Innovation", "Work with modern technologies and solve real-world challenges.", "💡"),
        ("Learning Opportunities", "Develop professional and technical skills through continuous learning.", "📚")
    ]
    
    for i, (title, desc, icon) in enumerate(why_data):
        with why_cols[i]:
            st.markdown(
                f"""
                <div style="background: white; padding: 2rem; border-radius: 8px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); height: 100%; text-align: center;">
                    <div style="font-size: 3rem; margin-bottom: 1rem;">{icon}</div>
                    <h3 style="color: #0F172A; font-size: 1.25rem; margin-bottom: 1rem;">{title}</h3>
                    <p style="color: #475569; font-size: 0.95rem;">{desc}</p>
                </div>
                """,
                unsafe_allow_html=True
            )

    # 4. Featured Opportunities
    st.markdown(
        """
        <section class="hp-section" style="padding: 4rem 1rem;">
          <div class="hp-container">
            <h2 style="font-size: 2rem; color: #0F172A; text-align: center; margin-bottom: 3rem;">Featured Opportunities</h2>
          </div>
        </section>
        """,
        unsafe_allow_html=True,
    )
    
    jobs = get_all_jobs()[:3]
    for job in jobs:
        render_job_card(job)
        
    st.markdown("<br>", unsafe_allow_html=True)
    
    col_c1, col_c2, col_c3 = st.columns([1, 1, 1])
    with col_c2:
        if st.button("View All Jobs", width="stretch", type="primary"):
            st.session_state.public_page = "careers"
            st.query_params["public_page"] = "careers"
            st.rerun()

    render_public_footer()