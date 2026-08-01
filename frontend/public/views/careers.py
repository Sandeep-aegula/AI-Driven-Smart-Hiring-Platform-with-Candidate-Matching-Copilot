import streamlit as st
from frontend.public.utils import inject_public_css
from frontend.public.components.public_navbar import render_public_navbar
from frontend.public.components.public_footer import render_public_footer
from frontend.public.components.job_card import render_job_card
from frontend.components.api_client import get_public_jobs

def render_page():
    """Render the Careers page for the public website."""
    # Load CSS
    inject_public_css()
    # Show navbar with active page
    render_public_navbar(active_page="careers")
    
    st.markdown(
        """
        <section class="hp-section" style="padding: 4rem 1rem; text-align: center; background: linear-gradient(135deg, #F8FAFC 0%, #E2E8F0 100%);">
          <div class="hp-container">
            <h1 style="font-size: 3rem; color: #0F172A; margin-bottom: 1rem;">Explore Career Opportunities</h1>
            <p style="font-size: 1.25rem; color: #475569; max-width: 800px; margin: 0 auto;">
              Find opportunities that match your skills, experience, and career goals.
            </p>
          </div>
        </section>
        """,
        unsafe_allow_html=True,
    )
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Filtering interface
    col_search, col_dept, col_loc, col_type = st.columns([3, 1, 1, 1])
    
    with col_search:
        search_query = st.text_input("Search", placeholder="Search jobs, skills, departments, or keywords")
        
    with col_dept:
        department_filter = st.selectbox("Department", ["All", "Engineering", "Technology", "Analytics"])
        
    with col_loc:
        location_filter = st.selectbox("Location", ["All", "Hyderabad", "Bengaluru", "Remote"])
        
    with col_type:
        type_filter = st.selectbox("Employment Type", ["All", "Full-Time", "Part-Time", "Contract"])
        
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Search logic via real backend API
    filtered_jobs = get_public_jobs(
        search=search_query,
        department=department_filter,
        location=location_filter,
        employment_type=type_filter
    )
    
    # Display Results
    if filtered_jobs:
        st.markdown(f"<h3 style='color: #0F172A; margin-bottom: 2rem;'>{len(filtered_jobs)} Open Positions</h3>", unsafe_allow_html=True)
        
        # Grid layout for job cards
        for i in range(0, len(filtered_jobs), 2):
            cols = st.columns(2)
            with cols[0]:
                render_job_card(filtered_jobs[i])
            with cols[1]:
                if i + 1 < len(filtered_jobs):
                    render_job_card(filtered_jobs[i+1])
    else:
        st.warning("No jobs found matching your criteria. Please try adjusting your filters.")
        
    st.markdown("<br><br>", unsafe_allow_html=True)
    render_public_footer()
