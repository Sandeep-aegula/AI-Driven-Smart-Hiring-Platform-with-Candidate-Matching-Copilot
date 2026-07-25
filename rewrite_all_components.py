import os

BASE = r"c:\Users\Naveen\Downloads\Ai_Recruitment_Talent_copilot"

# ai_header.py
ai_header = '''"""components/ai_header.py - HirePilot AI Chat Header.

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

    st.markdown("""
    <div class="ai-chat-header">
        <div class="ai-chat-header-left">
            <div class="status-dot"></div>
            <div>
                <h3>AI Assistant</h3>
                <div class="ai-page-context">{}</div>
            </div>
        </div>
        <div class="ai-header-actions">
            <button class="ai-header-btn" onclick="minimizeAssistant()" title="Minimize">−</button>
            <button class="ai-header-btn" onclick="closeAssistant()" title="Close">×</button>
        </div>
    </div>
    """.format(current_page), unsafe_allow_html=True)

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
'''

# ai_message.py
ai_message = '''"""components/ai_message.py - HirePilot AI Message Renderer.

Message rendering component for the AI Assistant.
"""

import json
import time
from typing import Dict, Optional
import streamlit as st
from frontend.utils.markdown_utils import render_markdown
from frontend.utils.copy_utils import copy_button
from frontend.utils.chat_utils import get_timestamp, generate_message_id


def render_message(message: Dict, index: int) -> None:
    """Render a single chat message."""
    role = message.get("role", "assistant")
    content = message.get("content", "")
    timestamp = message.get("timestamp", get_timestamp())
    message_id = message.get("id", generate_message_id())
    action = message.get("action")

    if role == "assistant":
        _render_assistant_message(content, timestamp, message_id, action, index)
    else:
        _render_user_message(content, timestamp, message_id)


def _render_assistant_message(
    content: str,
    timestamp: str,
    message_id: str,
    action: Optional[Dict],
    index: int,
) -> None:
    """Render an assistant message with avatar and bubble."""
    st.markdown(f"""
    <div class="ai-msg-row ai-msg-assistant">
        <div class="ai-msg-avatar ai-avatar-assistant">🤖</div>
        <div class="ai-msg-content">
            <div class="ai-msg-header">
                <span>AI Assistant</span>
                <span>•</span>
                <span>{timestamp}</span>
            </div>
            <div class="ai-msg-bubble ai-bubble-assistant">
                {render_markdown(content)}
            </div>
            {_render_action_card(action) if action else ""}
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Copy button
    col1, col2 = st.columns([1, 10])
    with col1:
        copy_button(content, message_id)


def _render_user_message(content: str, timestamp: str, message_id: str) -> None:
    """Render a user message with avatar and bubble."""
    st.markdown(f"""
    <div class="ai-msg-row ai-msg-user">
        <div class="ai-msg-content">
            <div class="ai-msg-header ai-msg-header-user">
                <span>{timestamp}</span>
                <span>•</span>
                <span>You</span>
            </div>
            <div class="ai-msg-bubble ai-bubble-user">
                {render_markdown(content)}
            </div>
        </div>
        <div class="ai-msg-avatar ai-avatar-user">👤</div>
    </div>
    """, unsafe_allow_html=True)


def _render_action_card(action: Optional[Dict]) -> str:
    """Render an action card if action data is provided."""
    if not action:
        return ""

    action_type = action.get("type", "")
    action_data = action.get("data", {})

    if action_type == "navigation":
        return f"""
        <div class="ai-action-card">
            <div class="ai-action-header">
                📍 Navigate to: {action_data.get("page", "")}
            </div>
            <pre>{json.dumps(action_data, indent=2)}</pre>
        </div>
        """

    return ""
'''

# ai_input.py
ai_input = '''"""components/ai_input.py - HirePilot AI Chat Input.

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
'''

# ai_sidebar.py
ai_sidebar = '''"""components/ai_sidebar.py - HirePilot AI Chat Sidebar.

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
'''

# ai_typing_indicator.py
ai_typing_indicator = '''"""components/ai_typing_indicator.py - HirePilot AI Typing Indicator.

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
'''

# Write all files
files = {
    r"frontend\components\ai_header.py": ai_header,
    r"frontend\components\ai_message.py": ai_message,
    r"frontend\components\ai_input.py": ai_input,
    r"frontend\components\ai_sidebar.py": ai_sidebar,
    r"frontend\components\ai_typing_indicator.py": ai_typing_indicator,
}

for rel_path, content in files.items():
    filepath = os.path.join(BASE, rel_path)
    with open(filepath, "w", encoding="utf-8", newline="\n") as f:
        f.write(content)
    print(f"Written: {rel_path} ({len(content)} chars)")

print("\nDone!")
