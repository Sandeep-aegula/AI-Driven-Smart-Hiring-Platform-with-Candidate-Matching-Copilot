import streamlit as st
from frontend.public.utils import inject_public_css
from frontend.public.components.public_navbar import render_public_navbar
from frontend.public.components.public_footer import render_public_footer

def render_page():
    """Render the About Us page for the public website."""
    # Load CSS
    inject_public_css()
    # Show navbar with active page
    render_public_navbar(active_page="about")
    
    st.markdown(
        """
        <section class="hp-section" style="padding: 4rem 1rem; text-align: center; background: linear-gradient(135deg, #F8FAFC 0%, #E2E8F0 100%);">
          <div class="hp-container">
            <h1 style="font-size: 3rem; color: #0F172A; margin-bottom: 1rem;">About HirePilot</h1>
            <p style="font-size: 1.25rem; color: #475569; max-width: 800px; margin: 0 auto;">
              HirePilot is an AI-powered recruitment and talent management platform designed to improve hiring efficiency and support better workforce decisions.
            </p>
          </div>
        </section>
        """,
        unsafe_allow_html=True,
    )
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown(
            """
            <div style="background: white; padding: 2rem; border-radius: 8px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); height: 100%;">
                <h2 style="color: #0F172A; margin-bottom: 1rem;">Our Mission</h2>
                <p style="color: #475569; font-size: 1.1rem; line-height: 1.6;">
                    To simplify recruitment, improve candidate evaluation, and help organizations build strong and capable teams.
                </p>
            </div>
            """,
            unsafe_allow_html=True
        )
        
    with col2:
        st.markdown(
            """
            <div style="background: white; padding: 2rem; border-radius: 8px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); height: 100%;">
                <h2 style="color: #0F172A; margin-bottom: 1rem;">Our Vision</h2>
                <p style="color: #475569; font-size: 1.1rem; line-height: 1.6;">
                    To create intelligent, efficient, and people-focused recruitment experiences using modern technology and Artificial Intelligence.
                </p>
            </div>
            """,
            unsafe_allow_html=True
        )
        
    st.markdown(
        """
        <section class="hp-section" style="padding: 4rem 1rem;">
          <div class="hp-container">
            <h2 style="font-size: 2rem; color: #0F172A; text-align: center; margin-bottom: 3rem;">Our Values</h2>
          </div>
        </section>
        """,
        unsafe_allow_html=True,
    )
    
    val_cols = st.columns(5)
    values_data = [
        ("Innovation", "💡"),
        ("Integrity", "🛡️"),
        ("Collaboration", "🤝"),
        ("Growth", "📈"),
        ("People First", "❤️")
    ]
    
    for i, (title, icon) in enumerate(values_data):
        with val_cols[i]:
            st.markdown(
                f"""
                <div style="background: white; padding: 1.5rem 1rem; border-radius: 8px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); text-align: center; height: 100%;">
                    <div style="font-size: 2.5rem; margin-bottom: 1rem;">{icon}</div>
                    <h3 style="color: #0F172A; font-size: 1.1rem; margin: 0;">{title}</h3>
                </div>
                """,
                unsafe_allow_html=True
            )
            
    st.markdown(
        """
        <section class="hp-section" style="padding: 4rem 1rem; background-color: #F8FAFC; margin-top: 4rem;">
          <div class="hp-container">
            <h2 style="font-size: 2rem; color: #0F172A; text-align: center; margin-bottom: 1.5rem;">The Perfect Synergy</h2>
            <p style="font-size: 1.125rem; color: #475569; max-width: 800px; margin: 0 auto; text-align: center; line-height: 1.8;">
              HirePilot successfully combines <strong>Artificial Intelligence</strong> with state-of-the-art <strong>Recruitment technology</strong> to enhance <strong>Candidate evaluation</strong> and streamline <strong>Talent management</strong>. 
              By doing so, we empower recruiters to focus on what matters most: informed, empathetic <strong>Human decision-making</strong>.
            </p>
          </div>
        </section>
        """,
        unsafe_allow_html=True,
    )
    
    render_public_footer()
