"""components/ai_input.py - HirePilot AI Chat Input.

Chat input component for the AI Assistant.
"""

import streamlit as st
from frontend.services.assistant_service import process_user_input, generate_ai_response
from frontend.utils.chat_utils import auto_scroll_to_bottom


def render_ai_input() -> None:
    """Render the AI Assistant chat input."""
    st.markdown("""
    <style>
    .ai-input-area {
        padding: 16px 20px;
        border-top: 1px solid #F1F5F9;
        background: #FAFAFA;
    }
    .ai-input-container {
        display: flex;
        align-items: flex-end;
        gap: 10px;
        background: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-radius: 20px;
        padding: 8px 16px;
        transition: all 0.2s ease;
    }
    .ai-input-container:focus-within {
        border-color: #6366F1;
        box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.1);
    }
    .ai-input-textarea {
        flex: 1;
        border: none;
        outline: none;
        background: transparent;
        font-size: 0.95rem;
        color: #0F172A;
        line-height: 1.5;
        min-height: 24px;
        max-height: 120px;
        resize: none;
        font-family: inherit;
    }
    .ai-send-btn {
        background: linear-gradient(135deg, #6366F1 0%, #8B5CF6 100%);
        color: white;
        border: none;
        border-radius: 12px;
        padding: 8px 16px;
        cursor: pointer;
        font-weight: 600;
        transition: all 0.2s;
    }
    .ai-send-btn:hover:not(:disabled) {
        transform: translateY(-1px);
        box-shadow: 0 4px 12px rgba(99, 102, 241, 0.3);
    }
    .ai-send-btn:disabled {
        opacity: 0.5;
        cursor: not-allowed;
    }
    </style>
    """, unsafe_allow_html=True)

    st.markdown('<div class="ai-input-area">', unsafe_allow_html=True)
    st.markdown('<div class="ai-input-container">', unsafe_allow_html=True)

    # Text input
    user_input = st.text_input(
        "Type your message...",
        key="ai_user_input",
        label_visibility="collapsed",
        placeholder="Ask anything about recruitment, jobs, candidates...",
    )

    # Send button
    send_disabled = not user_input or not user_input.strip()
    if st.button(
        "Send",
        key="ai_send_btn",
        disabled=send_disabled,
        type="primary",
    ):
        if user_input and user_input.strip():
            process_user_input(user_input.strip())
            st.rerun()

    st.markdown('</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    # Handle AI response generation
    if st.session_state.get("ai_assistant_typing", False):
        generate_ai_response()
