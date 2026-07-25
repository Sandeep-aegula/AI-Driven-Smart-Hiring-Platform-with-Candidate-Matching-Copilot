"""components/ai_copilot_panel.py - HirePilot AI Copilot Panel

Unified, self-contained AI Assistant panel that fixes all layout issues.
Renders as a single floating overlay with no interference to the main app.
"""
import streamlit as st
from frontend.services.assistant_service import (
    get_assistant_messages,
    clear_assistant_chat,
    get_suggestions,
    process_user_input,
    get_current_page_context,
    minimize_assistant,
    close_assistant,
)
from frontend.utils.chat_utils import auto_scroll_to_bottom


def render_ai_copilot_panel() -> None:
    """Render the complete AI Assistant as a single floating panel."""
    current_page = get_current_page_context()
    
    # Inject all CSS for the copilot panel
    _inject_copilot_css()
    
    # Main panel container
    st.markdown('<div class="hp-copilot-panel" id="hp-copilot-panel">', unsafe_allow_html=True)
    
    # Header
    _render_header(current_page)
    
    # Messages area
    _render_messages()
    
    # Input area
    _render_input()
    
    # Clear chat button
    _render_clear_button()
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Auto-scroll
    auto_scroll_to_bottom()


def _inject_copilot_css() -> None:
    """Inject all CSS for the copilot panel."""
    st.markdown("""
    <style>
    /* Main Panel */
    .hp-copilot-panel {
        position: fixed;
        top: 5vh;
        right: 20px;
        width: 400px;
        height: 90vh;
        max-height: 90vh;
        background: rgba(255, 255, 255, 0.98);
        backdrop-filter: blur(20px);
        -webkit-backdrop-filter: blur(20px);
        border-radius: 20px;
        border: 1px solid rgba(226, 232, 240, 0.8);
        box-shadow: 
            0 20px 60px rgba(0, 0, 0, 0.15),
            0 8px 24px rgba(0, 0, 0, 0.1),
            0 0 0 1px rgba(255, 255, 255, 0.5) inset;
        z-index: 99999;
        display: flex;
        flex-direction: column;
        overflow: hidden;
        animation: hpCopilotSlideIn 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
    }
    
    @keyframes hpCopilotSlideIn {
        from {
            opacity: 0;
            transform: translateX(30px) scale(0.95);
        }
        to {
            opacity: 1;
            transform: translateX(0) scale(1);
        }
    }
    
    @keyframes hpCopilotSlideOut {
        from {
            opacity: 1;
            transform: translateX(0) scale(1);
        }
        to {
            opacity: 0;
            transform: translateX(30px) scale(0.95);
        }
    }
    
    /* Header */
    .hp-copilot-header {
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 16px 20px;
        background: linear-gradient(135deg, #6366F1 0%, #8B5CF6 100%);
        color: white;
        border-radius: 20px 20px 0 0;
        flex-shrink: 0;
    }
    
    .hp-copilot-header-left {
        display: flex;
        align-items: center;
        gap: 12px;
    }
    
    .hp-copilot-header h3 {
        margin: 0;
        font-size: 1.1rem;
        font-weight: 700;
        display: flex;
        align-items: center;
        gap: 8px;
    }
    
    .hp-status-dot {
        width: 8px;
        height: 8px;
        border-radius: 50%;
        background: #10B981;
        animation: hpStatusPulse 2s infinite;
    }
    
    @keyframes hpStatusPulse {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.5; }
    }
    
    .hp-page-context {
        font-size: 0.75rem;
        opacity: 0.9;
        background: rgba(255,255,255,0.15);
        padding: 4px 10px;
        border-radius: 12px;
        margin-top: 2px;
    }
    
    .hp-header-actions {
        display: flex;
        gap: 6px;
    }
    
    .hp-header-btn {
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
        font-size: 16px;
        font-weight: 500;
    }
    
    .hp-header-btn:hover {
        background: rgba(255,255,255,0.25);
        transform: scale(1.05);
    }
    
    /* Messages Area */
    .hp-copilot-messages {
        flex: 1;
        overflow-y: auto;
        padding: 20px;
        display: flex;
        flex-direction: column;
        gap: 16px;
        background: #FFFFFF;
        min-height: 0;
    }
    
    .hp-copilot-messages::-webkit-scrollbar {
        width: 6px;
    }
    
    .hp-copilot-messages::-webkit-scrollbar-track {
        background: transparent;
    }
    
    .hp-copilot-messages::-webkit-scrollbar-thumb {
        background: #CBD5E1;
        border-radius: 3px;
    }
    
    .hp-copilot-messages::-webkit-scrollbar-thumb:hover {
        background: #94A3B8;
    }
    
    .hp-msg-row {
        display: flex;
        gap: 10px;
        max-width: 85%;
        animation: hpFadeInUp 0.3s ease;
    }
    
    @keyframes hpFadeInUp {
        from {
            opacity: 0;
            transform: translateY(10px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }
    
    .hp-msg-assistant {
        align-self: flex-start;
    }
    
    .hp-msg-user {
        align-self: flex-end;
        flex-direction: row-reverse;
    }
    
    .hp-msg-avatar {
        width: 32px;
        height: 32px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        flex-shrink: 0;
        font-size: 14px;
    }
    
    .hp-avatar-assistant {
        background: linear-gradient(135deg, #6366F1 0%, #8B5CF6 100%);
        color: white;
    }
    
    .hp-avatar-user {
        background: linear-gradient(135deg, #3B82F6 0%, #06B6D4 100%);
        color: white;
    }
    
    .hp-msg-content {
        max-width: 100%;
    }
    
    .hp-msg-header {
        display: flex;
        align-items: center;
        gap: 8px;
        margin-bottom: 6px;
        font-size: 0.7rem;
        color: #64748B;
        font-weight: 500;
    }
    
    .hp-msg-header-user {
        justify-content: flex-end;
        text-align: right;
    }
    
    .hp-msg-bubble {
        max-width: 100%;
        padding: 12px 16px;
        border-radius: 18px;
        font-size: 0.9rem;
        line-height: 1.6;
        color: #1E293B;
        word-wrap: break-word;
    }
    
    .hp-bubble-assistant {
        background: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-radius: 18px 18px 18px 4px;
        box-shadow: 0 1px 2px rgba(0,0,0,0.03);
    }
    
    .hp-bubble-user {
        background: #EEF4FF;
        border: 1px solid #DBEAFE;
        border-radius: 18px 18px 4px 18px;
        box-shadow: 0 1px 2px rgba(59, 130, 246, 0.08);
    }
    
    /* Typing Indicator */
    .hp-typing-indicator {
        display: flex;
        gap: 4px;
        padding: 12px 16px;
        align-items: center;
    }
    
    .hp-typing-dot {
        width: 8px;
        height: 8px;
        border-radius: 50%;
        background: #6366F1;
        animation: hpTypingBounce 1.4s infinite ease-in-out;
    }
    
    .hp-typing-dot:nth-child(1) { animation-delay: 0s; }
    .hp-typing-dot:nth-child(2) { animation-delay: 0.2s; }
    .hp-typing-dot:nth-child(3) { animation-delay: 0.4s; }
    
    @keyframes hpTypingBounce {
        0%, 60%, 100% { transform: translateY(0); opacity: 0.4; }
        30% { transform: translateY(-6px); opacity: 1; }
    }
    
    /* Input Area */
    .hp-copilot-input-area {
        padding: 16px 20px;
        border-top: 1px solid #F1F5F9;
        background: #FAFAFA;
        flex-shrink: 0;
    }
    
    .hp-input-container {
        display: flex;
        align-items: flex-end;
        gap: 10px;
        background: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-radius: 20px;
        padding: 8px 16px;
        transition: all 0.2s ease;
    }
    
    .hp-input-container:focus-within {
        border-color: #6366F1;
        box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.1);
    }
    
    .hp-input-textarea {
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
    
    .hp-send-btn {
        background: linear-gradient(135deg, #6366F1 0%, #8B5CF6 100%);
        color: white;
        border: none;
        border-radius: 12px;
        padding: 8px 16px;
        cursor: pointer;
        font-weight: 600;
        transition: all 0.2s;
        font-size: 0.9rem;
    }
    
    .hp-send-btn:hover:not(:disabled) {
        transform: translateY(-1px);
        box-shadow: 0 4px 12px rgba(99, 102, 241, 0.3);
    }
    
    .hp-send-btn:disabled {
        opacity: 0.5;
        cursor: not-allowed;
    }
    
    /* Clear button */
    .hp-clear-btn-container {
        padding: 10px 20px;
        border-top: 1px solid #F1F5F9;
        background: #FAFAFA;
        text-align: center;
        flex-shrink: 0;
    }
    
    /* Responsive */
    @media (max-width: 768px) {
        .hp-copilot-panel {
            width: calc(100vw - 40px);
            right: 20px;
            max-width: 400px;
        }
    }
    
    @media (prefers-color-scheme: dark) {
        .hp-copilot-panel {
            background: rgba(15, 23, 42, 0.98);
            border-color: rgba(51, 65, 85, 0.8);
        }
        .hp-copilot-messages {
            background: #0F172A;
        }
        .hp-msg-bubble {
            color: #F1F5F9;
        }
        .hp-bubble-assistant {
            background: #1E293B;
            border-color: #334155;
            color: #F1F5F9;
        }
        .hp-bubble-user {
            background: #1E3A8A;
            border-color: #1E40AF;
            color: #F1F5F9;
        }
        .hp-copilot-input-area {
            background: #1E293B;
            border-top-color: #334155;
        }
        .hp-input-container {
            background: #0F172A;
            border-color: #334155;
        }
        .hp-input-textarea {
            color: #F1F5F9;
        }
        .hp-clear-btn-container {
            background: #1E293B;
            border-top-color: #334155;
        }
        .hp-msg-header {
            color: #94A3B8;
        }
    }
    </style>
    """, unsafe_allow_html=True)


def _render_header(current_page: str) -> None:
    """Render the copilot header."""
    st.markdown(f"""
    <div class="hp-copilot-header">
        <div class="hp-copilot-header-left">
            <div class="hp-status-dot"></div>
            <div>
                <h3>AI Assistant</h3>
                <div class="hp-page-context">{current_page}</div>
            </div>
        </div>
        <div class="hp-header-actions">
            <button class="hp-header-btn" title="Minimize">−</button>
            <button class="hp-header-btn" title="Close">×</button>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Streamlit buttons for interaction
    col1, col2, col3 = st.columns([1, 1, 1])
    with col1:
        if st.button("−", key="hp_minimize_btn", help="Minimize"):
            minimize_assistant()
            st.rerun()
    with col2:
        if st.button("×", key="hp_close_btn", help="Close"):
            close_assistant()
            st.rerun()
    with col3:
        if st.button("🔄", key="hp_refresh_btn", help="New Conversation"):
            clear_assistant_chat()
            st.rerun()


def _render_messages() -> None:
    """Render chat messages."""
    st.markdown('<div class="hp-copilot-messages" id="hp-copilot-messages">', unsafe_allow_html=True)
    
    messages = get_assistant_messages()
    for idx, message in enumerate(messages):
        _render_message(message, idx)
    
    # Typing indicator
    if st.session_state.get("ai_assistant_typing", False):
        st.markdown("""
        <div class="hp-msg-row hp-msg-assistant">
            <div class="hp-msg-avatar hp-avatar-assistant">🤖</div>
            <div class="hp-msg-bubble hp-bubble-assistant">
                <div class="hp-typing-indicator">
                    <div class="hp-typing-dot"></div>
                    <div class="hp-typing-dot"></div>
                    <div class="hp-typing-dot"></div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)


def _render_message(message, index: int) -> None:
    """Render a single message."""
    role = message.get("role", "assistant")
    content = message.get("content", "")
    timestamp = message.get("timestamp", "")
    
    if role == "assistant":
        st.markdown(f"""
        <div class="hp-msg-row hp-msg-assistant">
            <div class="hp-msg-avatar hp-avatar-assistant">🤖</div>
            <div class="hp-msg-content">
                <div class="hp-msg-header">
                    <span>AI Assistant</span>
                    <span>•</span>
                    <span>{timestamp}</span>
                </div>
                <div class="hp-msg-bubble hp-bubble-assistant">
                    {_render_markdown(content)}
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown(f"""
        <div class="hp-msg-row hp-msg-user">
            <div class="hp-msg-content">
                <div class="hp-msg-header hp-msg-header-user">
                    <span>{timestamp}</span>
                    <span>•</span>
                    <span>You</span>
                </div>
                <div class="hp-msg-bubble hp-bubble-user">
                    {_render_markdown(content)}
                </div>
            </div>
            <div class="hp-msg-avatar hp-avatar-user">👤</div>
        </div>
        """, unsafe_allow_html=True)


def _render_markdown(text: str) -> str:
    """Render markdown text with basic formatting."""
    import re
    # Escape HTML
    text = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    # Bold
    text = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", text)
    # Italic
    text = re.sub(r"\*(.+?)\*", r"<em>\1</em>", text)
    # Code blocks
    text = re.sub(r"```(.*?)```", r"<pre><code>\1</code></pre>", text, flags=re.DOTALL)
    # Inline code
    text = re.sub(r"`(.+?)`", r"<code>\1</code>", text)
    # Line breaks
    text = text.replace("\n", "<br>")
    return text


def _render_input() -> None:
    """Render the input area."""
    st.markdown('<div class="hp-copilot-input-area">', unsafe_allow_html=True)
    st.markdown('<div class="hp-input-container">', unsafe_allow_html=True)
    
    user_input = st.text_input(
        "Type your message...",
        key="hp_user_input",
        label_visibility="collapsed",
        placeholder="Ask anything about recruitment, candidates, jobs, interviews or this application...",
    )
    
    send_disabled = not user_input or not user_input.strip()
    if st.button(
        "Send",
        key="hp_send_btn",
        disabled=send_disabled,
        type="primary",
    ):
        if user_input and user_input.strip():
            process_user_input(user_input.strip())
            st.rerun()
    
    st.markdown('</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)


def _render_clear_button() -> None:
    """Render the clear chat button."""
    messages = get_assistant_messages()
    st.markdown('<div class="hp-clear-btn-container">', unsafe_allow_html=True)
    if len(messages) > 1:
        if st.button("Clear Chat History", key="hp_clear_chat_btn", width="stretch"):
            clear_assistant_chat()
            st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)
