"""components/ai_sidebar.py - HirePilot AI Chat Sidebar.

Sidebar component for quick prompts and suggestions.
"""

import streamlit as st
from frontend.services.assistant_service import (
    get_suggestions,
    append_assistant_message,
    process_user_input,
)


def render_ai_sidebar() -> None:
    """Render the AI Assistant sidebar with quick prompts."""
    st.markdown("""
    <style>
    .ai-sidebar {
        padding: 16px;
        border-bottom: 1px solid #F1F5F9;
        background: #FAFAFA;
    }
    .ai-sidebar-label {
        font-size: 0.75rem;
        font-weight: 600;
        color: #64748B;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        margin-bottom: 10px;
    }
    .ai-suggestions-grid {
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 8px;
    }
    .ai-suggestion-btn {
        display: flex;
        align-items: center;
        gap: 8px;
        padding: 10px 12px;
        border-radius: 12px;
        background: #FFFFFF;
        border: 1px solid #E2E8F0;
        color: #334155;
        font-size: 0.8rem;
        font-weight: 500;
        cursor: pointer;
        transition: all 0.2s;
        text-align: left;
    }
    .ai-suggestion-btn:hover {
        background: #EEF4FF;
        border-color: #6366F1;
        color: #6366F1;
    }
    </style>
    """, unsafe_allow_html=True)

    st.markdown('<div class="ai-sidebar">', unsafe_allow_html=True)
    st.markdown('<div class="ai-sidebar-label">Quick Actions</div>', unsafe_allow_html=True)
    st.markdown('<div class="ai-suggestions-grid">', unsafe_allow_html=True)

    suggestions = get_suggestions()
    for suggestion in suggestions:
        if st.button(
            suggestion,
            key=f"suggest_{hash(suggestion)}",
            use_container_width=True,
        ):
            process_user_input(suggestion)
            st.rerun()

    st.markdown('</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)
