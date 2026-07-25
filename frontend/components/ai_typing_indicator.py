"""components/ai_typing_indicator.py - HirePilot AI Typing Indicator.

Typing indicator component for the AI Assistant.
"""

import streamlit as st


def render_typing_indicator() -> None:
    """Render the typing indicator."""
    st.markdown("""
    <style>
    .ai-typing-indicator {
        display: flex;
        gap: 4px;
        padding: 12px 16px;
        align-items: center;
    }
    .ai-typing-dot {
        width: 8px;
        height: 8px;
        border-radius: 50%;
        background: #6366F1;
        animation: aiTypingBounce 1.4s infinite ease-in-out;
    }
    .ai-typing-dot:nth-child(1) {
        animation-delay: 0s;
    }
    .ai-typing-dot:nth-child(2) {
        animation-delay: 0.2s;
    }
    .ai-typing-dot:nth-child(3) {
        animation-delay: 0.4s;
    }
    @keyframes aiTypingBounce {
        0%, 60%, 100% {
            transform: translateY(0);
            opacity: 0.4;
        }
        30% {
            transform: translateY(-6px);
            opacity: 1;
        }
    }
    </style>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div class="ai-msg-row ai-msg-assistant">
        <div class="ai-msg-avatar ai-avatar-assistant">🤖</div>
        <div class="ai-msg-bubble ai-bubble-assistant">
            <div class="ai-typing-indicator">
                <div class="ai-typing-dot"></div>
                <div class="ai-typing-dot"></div>
                <div class="ai-typing-dot"></div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
