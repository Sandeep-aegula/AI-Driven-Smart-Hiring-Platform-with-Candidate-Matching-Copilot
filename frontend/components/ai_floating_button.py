"""components/ai_floating_button.py - HirePilot AI Floating Button. Floating AI Assistant launcher button. """
import streamlit as st

def render_floating_button() -> None:
    """Render the floating AI Assistant button."""
    if st.session_state.get("ai_assistant_open", False):
        return
    
    st.markdown("""
    <style>
    .hp-float-btn {
        position: fixed;
        bottom: 24px;
        right: 24px;
        width: 60px;
        height: 60px;
        border-radius: 50%;
        background: linear-gradient(135deg, #6366F1 0%, #8B5CF6 100%);
        border: none;
        cursor: pointer;
        display: flex;
        align-items: center;
        justify-content: center;
        box-shadow: 0 4px 20px rgba(99, 102, 241, 0.4), 0 2px 8px rgba(0,0,0,0.1);
        z-index: 99999;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        animation: hpPulse 2s infinite;
    }
    .hp-float-btn:hover {
        transform: scale(1.1);
        box-shadow: 0 8px 30px rgba(99, 102, 241, 0.5), 0 4px 12px rgba(0,0,0,0.15);
    }
    .hp-float-btn:active {
        transform: scale(0.95);
    }
    @keyframes hpPulse {
        0%, 100% { box-shadow: 0 4px 20px rgba(99, 102, 241, 0.4), 0 2px 8px rgba(0,0,0,0.1); }
        50% { box-shadow: 0 6px 25px rgba(99, 102, 241, 0.5), 0 4px 12px rgba(0,0,0,0.15); }
    }
    .hp-float-btn svg {
        width: 28px;
        height: 28px;
        color: white;
    }
    @media (prefers-color-scheme: dark) {
        .hp-float-btn {
            background: linear-gradient(135deg, #818CF8 0%, #A78BFA 100%);
        }
    }
    </style>
    """, unsafe_allow_html=True)
    
    st.markdown("""
    <button class="hp-float-btn" id="hp-float-btn" aria-label="Open AI Assistant" title="Open AI Assistant">
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M12 14C15.3137 14 18 11.3137 18 8C18 4.68629 15.3137 2 12 2C8.68629 2 6 4.68629 6 8C6 11.3137 8.68629 14 12 14Z" fill="white"/>
            <circle cx="12" cy="10" r="3" fill="white"/>
            <path d="M12 17v4" stroke="white" stroke-width="2"/>
            <path d="M8 21h8" stroke="white" stroke-width="2"/>
        </svg>
    </button>
    """, unsafe_allow_html=True)
    
    # Hidden Streamlit button for functionality (no visible UI impact)
    st.markdown('<div style="position:fixed;bottom:24px;right:24px;width:60px;height:60px;z-index:99999;opacity:0;pointer-events:none;"></div>', unsafe_allow_html=True)
    if st.button("AI", key="hp_assistant_toggle", help="Open AI Assistant"):
        from frontend.services.assistant_service import toggle_assistant
        toggle_assistant()
        st.rerun()
