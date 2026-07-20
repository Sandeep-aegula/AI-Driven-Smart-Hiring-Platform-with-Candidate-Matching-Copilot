import streamlit as st

def render_recommendation():
    """Renders Section 9: AI Recommendation Card."""
    # st.markdown("<!-- SECTION 9: AI RECOMMENDATION -->")
    st.markdown("""
    <div class="custom-card-wrapper" style="margin-bottom: 0px; border-bottom-left-radius: 0px; border-bottom-right-radius: 0px;">
        <div class="section-title" style="margin-bottom: 0px;">
            <span><i class="fa-solid fa-lightbulb"></i></span> AI Hiring Recommendation
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    cand_active = st.session_state.selected_candidate
    
    with st.container(border=True):
        st.markdown(f"#### Fit Assessment Summary - {cand_active['name']}")
        st.markdown(f"""
        <p style='color: #475569; font-size: 0.92rem; line-height: 1.5; margin-bottom: 18px;'>
            Based on the job criteria for <b>{st.session_state.job_details['title']}</b>, the AI model generates the following structured assessment findings:
        </p>
        """, unsafe_allow_html=True)
        
        rec_col1, rec_col2 = st.columns(2)
        
        with rec_col1:
            st.markdown("<h5 style='color: #065F46; font-size: 0.95rem; font-weight: 700; margin-bottom: 12px;'><i class=\"fa-solid fa-circle-check\" style=\"margin-right:5px;\"></i> Identified Strengths</h5>", unsafe_allow_html=True)
            for strength in cand_active["strengths"]:
                st.markdown(f"""
                <div style="display: flex; gap: 8px; align-items: flex-start; margin-bottom: 8px;">
                    <span style="color: #10B981; font-size: 12px; padding-top: 2px;"><i class="fa-solid fa-check"></i></span>
                    <span style="font-size: 0.85rem; color: #334155;">{strength}</span>
                </div>
                """, unsafe_allow_html=True)
                
        with rec_col2:
            st.markdown("<h5 style='color: #991B1B; font-size: 0.95rem; font-weight: 700; margin-bottom: 12px;'><i class=\"fa-solid fa-triangle-exclamation\" style=\"margin-right:5px;\"></i> Dev Areas / Gaps</h5>", unsafe_allow_html=True)
            for weakness in cand_active["weaknesses"]:
                st.markdown(f"""
                <div style="display: flex; gap: 8px; align-items: flex-start; margin-bottom: 8px;">
                    <span style="color: #EF4444; font-size: 12px; padding-top: 2px;"><i class="fa-solid fa-triangle-exclamation"></i></span>
                    <span style="font-size: 0.85rem; color: #334155;">{weakness}</span>
                </div>
                """, unsafe_allow_html=True)
                
        st.markdown("<div style='height: 16px;'></div>", unsafe_allow_html=True)
        st.markdown("##### Suggested Next Interview Questions")
        for q in cand_active["interview_suggestions"]:
            st.markdown(f"""
            <div style="background-color: #F8FAFC; border-left: 3px solid #2563EB; padding: 10px 14px; border-radius: 0 8px 8px 0; margin-bottom: 8px; font-size: 0.85rem; color: #334155; font-weight: 500;">
                {q}
            </div>
            """, unsafe_allow_html=True)
