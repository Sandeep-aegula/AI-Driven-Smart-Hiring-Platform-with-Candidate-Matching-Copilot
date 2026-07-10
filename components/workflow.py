import streamlit as st

def render_workflow():
    """Renders candidate status workflow pipeline indicators."""
    active_cand = st.session_state.selected_candidate
    status = active_cand["status"]
    
    stages = ["Applied", "Shortlisted", "Interview Scheduled", "Offer Released", "Rejected"]
    
    # Generate progress steps indicator
    steps_html = "<div style='display: flex; align-items: center; justify-content: space-between; margin-bottom: 24px; background: white; border-radius: 12px; padding: 15px 24px; border: 1px solid #E2E8F0; box-shadow: 0 1px 2px rgba(0,0,0,0.02);'>"
    
    for idx, stage in enumerate(stages):
        is_active = (stage == status)
        is_past = False
        
        # Check sequencing
        if status in stages:
            act_idx = stages.index(status)
            if idx < act_idx:
                is_past = True
                
        # Handle Rejected case separately
        if status == "Rejected":
            if stage == "Rejected":
                bg = "#FEE2E2"
                color = "#991B1B"
                border = "#FCA5A5"
            else:
                bg = "#F1F5F9"
                color = "#94A3B8"
                border = "#E2E8F0"
        else:
            if stage == "Rejected":
                continue # Skip rejected step if candidate is not rejected
                
            if is_active:
                bg = "#EFF6FF"
                color = "#2563EB"
                border = "#93C5FD"
            elif is_past:
                bg = "#ECFDF5"
                color = "#059669"
                border = "#A7F3D0"
            else:
                bg = "#F8FAFC"
                color = "#64748B"
                border = "#E2E8F0"
                
        icon = '<i class="fa-solid fa-circle-check"></i>' if is_past else ( '<i class="fa-solid fa-hourglass-half"></i>' if is_active else '<i class="fa-regular fa-circle"></i>' )
        if stage == "Rejected" and is_active:
            icon = '<i class="fa-solid fa-circle-xmark"></i>'
            
        steps_html += f'<div style="flex: 1; text-align: center; border: 1px solid {border}; background-color: {bg}; color: {color}; border-radius: 8px; padding: 8px; margin: 0 5px; font-size: 0.8rem; font-weight: 700;"><div style="font-size: 10px; margin-bottom: 2px;">{icon}</div>{stage}</div>'
        
    steps_html += "</div>"
    st.markdown(steps_html, unsafe_allow_html=True)
