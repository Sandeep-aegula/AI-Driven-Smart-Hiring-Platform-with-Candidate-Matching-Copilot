import os

path = r"c:\Users\Naveen\Downloads\Ai_Recruitment_Talent_copilot\frontend\components\ai_chat_window.py"

content = '''"""components/ai_chat_window.py - HirePilot AI Chat Window.

Main chat window component for the AI Assistant.
"""

import streamlit as st
from frontend.components.ai_header import render_ai_header
from frontend.components.ai_sidebar import render_ai_sidebar
from frontend.components.ai_message import render_message, render_typing_indicator
from frontend.components.ai_input import render_ai_input
from frontend.services.assistant_service import (
    get_assistant_messages,
    clear_assistant_chat,
    get_suggestions,
)
from frontend.utils.chat_utils import auto_scroll_to_bottom


def render_ai_chat_window() -> None:
    """Render the complete AI Assistant chat window."""
    # Chat panel container
    st.markdown("""
    <style>
    .ai-chat-panel {
        position: fixed;
        bottom: 90px;
        right: 24px;
        width: 400px;
        height: 90vh;
        max-height: 700px;
        background: rgba(255, 255, 255, 0.95);
        backdrop-filter: blur(20px);
        border-radius: 20px;
        border: 1px solid rgba(226, 232, 240, 0.8);
        box-shadow: 0 20px 60px rgba(0, 0, 0, 0.15), 0 8px 24px rgba(0, 0, 0, 0.1);
        z-index: 9998;
        display: flex;
        flex-direction: column;
        overflow: hidden;
        animation: aiSlideIn 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    }
    @keyframes aiSlideIn {
        from { opacity: 0; transform: translateX(30px); }
        to { opacity: 1; transform: translateX(0); }
    }
    .ai-messages-area {
        flex: 1;
        overflow-y: auto;
        padding: 20px;
        display: flex;
        flex-direction: column;
        gap: 16px;
        background: #FFFFFF;
    }
    .ai-messages-area::-webkit-scrollbar {
        width: 6px;
    }
    .ai-messages-area::-webkit-scrollbar-track {
        background: transparent;
    }
    .ai-messages-area::-webkit-scrollbar-thumb {
        background: #CBD5E1;
        border-radius: 3px;
    }
    .ai-messages-area::-webkit-scrollbar-thumb:hover {
        background: #94A3B8;
    }
    .ai-msg-row {
        display: flex;
        gap: 10px;
        max-width: 85%;
        animation: aiFadeInUp 0.3s ease;
    }
    @keyframes aiFadeInUp {
        from { opacity: 0; transform: translateY(10px); }
        to { opacity: 1; transform: translateY(0); }
    }
    .ai-msg-assistant {
        align-self: flex-start;
    }
    .ai-msg-user {
        align-self: flex-end;
        flex-direction: row-reverse;
    }
    .ai-msg-avatar {
        width: 32px;
        height: 32px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        flex-shrink: 0;
        font-size: 14px;
    }
    .ai-avatar-assistant {
        background: linear-gradient(135deg, #6366F1 0%, #8B5CF6 100%);
        color: white;
    }
    .ai-avatar-user {
        background: linear-gradient(135deg, #3B82F6 0%, #06B6D4 100%);
        color: white;
    }
    .ai-msg-content {
        max-width: 100%;
    }
    .ai-msg-header {
        display: flex;
        align-items: center;
        gap: 8px;
        margin-bottom: 6px;
        font-size: 0.7rem;
        color: #64748B;
        font-weight: 500;
    }
    .ai-msg-header-user {
        justify-content: flex-end;
        text-align: right;
    }
    .ai-msg-bubble {
        max-width: 100%;
        padding: 12px 16px;
        border-radius: 18px;
        font-size: 0.9rem;
        line-height: 1.6;
        color: #1E293B;
        word-wrap: break-word;
    }
    .ai-bubble-assistant {
        background: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-radius: 18px 18px 18px 4px;
        box-shadow: 0 1px 2px rgba(0,0,0,0.03);
    }
    .ai-bubble-user {
        background: #EEF4FF;
        border: 1px solid #DBEAFE;
        border-radius: 18px 18px 4px 18px;
        box-shadow: 0 1px 2px rgba(59, 130, 246, 0.08);
    }
    .ai-action-card {
        background: #FEF3F0;
        border: 1px solid #FED7CC;
        border-radius: 12px;
        padding: 16px;
        margin-top: 12px;
    }
    .ai-action-header {
        display: flex;
        align-items: center;
        gap: 8px;
        font-weight: 600;
        color: #EA580C;
        margin-bottom: 8px;
        font-size: 0.85rem;
    }
    .ai-action-card pre {
        background: #FFF7ED;
        border: 1px solid #FED7CC;
        border-radius: 8px;
        padding: 12px;
        font-size: 0.75rem;
        overflow-x: auto;
        color: #9A3412;
    }
    .ai-clear-btn-container {
        padding: 10px 20px;
        border-top: 1px solid #F1F5F9;
        background: #FAFAFA;
        text-align: center;
    }
    </style>
    """, unsafe_allow_html=True)

    st.markdown('<div class="ai-chat-panel">', unsafe_allow_html=True)

    # Header
    render_ai_header()

    # Sidebar with suggestions
    with st.sidebar:
        render_ai_sidebar()

    # Messages area
    st.markdown('<div class="ai-messages-area" id="ai-chat-messages">', unsafe_allow_html=True)
    messages = get_assistant_messages()

    for idx, message in enumerate(messages):
        render_message(message, idx)

    # Typing indicator
    if st.session_state.get("ai_assistant_typing", False):
        render_typing_indicator()

    st.markdown("</div>", unsafe_allow_html=True)

    # Input area
    render_ai_input()

    # Clear chat button
    st.markdown('<div class="ai-clear-btn-container">', unsafe_allow_html=True)
    if len(messages) > 1:
        if st.button("Clear Chat History", key="ai_clear_chat_btn", width="stretch"):
            clear_assistant_chat()
            st.rerun()

    st.markdown("</div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

    # Auto-scroll to bottom
    auto_scroll_to_bottom()
'''

with open(path, "w", encoding="utf-8", newline="\n") as f:
    f.write(content)

print("Written:", len(content), "chars")
