"""components/ai_message.py - HirePilot AI Message Renderer.

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
