"""components/ai_header.py - HirePilot AI Chat Header.

Header component for the AI Assistant chat window.
"""

import streamlit as st
from frontend.services.assistant_service import (
    get_current_page_context,
    minimize_assistant,
    close_assistant,
)


def render_ai_header() -> None:
    """Render the AI Assistant chat header."""
    current_page = get_current_page_context()

    st.markdown("""
    <style>
    .ai-chat-header {
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 16px 20px;
        background: linear-gradient(135deg, #6366F1 0%, #8B5CF6 100%);
        color: white;
        border-radius: 20px 20px 0 0;
    }
    .ai-chat-header-left {
        display: flex;
        align-items: center;
        gap: 12px;
    }
    .ai-chat-header h3 {
        margin: 0;
        font-size: 1.1rem;
        font-weight: 700;
        display: flex;
        align-items: center;
        gap: 8px;
    }
    .status-dot {
        width: 8px;
        height: 8px;
        border-radius: 50%;
        background: #10B981;
        animation: aiStatusPulse 2s infinite;
    }
    @keyframes aiStatusPulse {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.5; }
    }
    .ai-page-context {
        font-size: 0.75rem;
        opacity: 0.9;
        background: rgba(255,255,255,0.15);
        padding: 4px 10px;
        border-radius: 12px;
    }
    .ai-header-actions {
        display: flex;
        gap: 8px;
    }
    .ai-header-btn {
        background: rgba(255,255,255,0.15);
        border: none;
        color: white;
        width: 32px;
        height: 32px;
        border-radius: 8px;
        cursor: pointer;
        display: flex;
        align-items: center;
        justify-content: center;
        transition: all 0.2s;
    }
    .ai-header-btn:hover {
        background: rgba(255,255,255,0.25);
    }
    </style>
    """, unsafe_allow_html=True)

    st.markdown(f"""
    <div class="ai-chat-header">
        <div class="ai-chat-header-left">
            <div class="status-dot"></div>
            <div>
                <h3>AI Assistant</h3>
                <div class="ai-page-context">{current_page}</div>
            </div>
        </div>
        <div class="ai-header-actions">
            <button class="ai-header-btn" title="Minimize">−</button>
            <button class="ai-header-btn" title="Close">×</button>
        </div>
    </div>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 1, 1])
    with col1:
        if st.button("−", key="ai_minimize_btn", help="Minimize"):
            minimize_assistant()
            st.rerun()
    with col2:
        if st.button("×", key="ai_close_btn", help="Close"):
            close_assistant()
            st.rerun()
    with col3:
        if st.button("🔄", key="ai_refresh_btn", help="New Conversation"):
            from frontend.services.assistant_service import clear_assistant_chat
            clear_assistant_chat()
            st.rerun()
