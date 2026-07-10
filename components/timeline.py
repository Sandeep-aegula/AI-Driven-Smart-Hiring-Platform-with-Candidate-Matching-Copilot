import streamlit as st

def render_timeline():
    """Renders Section 10: Recent Activity Timeline Component."""
    # st.markdown("<!-- SECTION 10: RECENT ACTIVITY -->")
    st.markdown("""
    <div class="custom-card-wrapper" style="margin-bottom: 0px; border-bottom-left-radius: 0px; border-bottom-right-radius: 0px;">
        <div class="section-title" style="margin-bottom: 0px;">
            <span><i class="fa-solid fa-clock-rotate-left"></i></span> Recent Recruitment Activities
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    with st.container(border=True):
        st.markdown('<div class="timeline">', unsafe_allow_html=True)
        
        for item in st.session_state.activities[:5]:
            st.markdown(f"""
            <div class="timeline-item">
                <div class="timeline-dot"><i class="fa-solid {item['icon']}"></i></div>
                <div class="timeline-content-card">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 4px;">
                        <span style="font-weight: 700; color: #0F172A; font-size: 0.88rem;">{item['title']}</span>
                        <span class="timeline-time">{item['time']}</span>
                    </div>
                    <p style="margin: 0; font-size: 0.8rem; color: #475569; font-weight: 500;">{item['description']}</p>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
        st.markdown('</div>', unsafe_allow_html=True)
