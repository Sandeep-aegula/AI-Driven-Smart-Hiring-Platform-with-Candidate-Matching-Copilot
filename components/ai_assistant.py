"""
components/ai_assistant.py - HirePilot AI Assistant (Infosys Springboard Style)
A modern, enterprise-grade AI Assistant chatbot with glassmorphism design.
"""

import time
import uuid
import json
import streamlit as st
from frontend.components import api_client
from frontend.services.cache import get_candidates_cached, get_jobs_cached


def render_ai_assistant() -> None:
    """Render the AI Assistant floating chat widget."""
    
    # Initialize session state for AI Assistant
    if "ai_assistant_open" not in st.session_state:
        st.session_state["ai_assistant_open"] = False
    if "ai_assistant_messages" not in st.session_state:
        st.session_state["ai_assistant_messages"] = []
    if "ai_assistant_session_id" not in st.session_state:
        st.session_state["ai_assistant_session_id"] = str(uuid.uuid4())
    if "ai_assistant_typing" not in st.session_state:
        st.session_state["ai_assistant_typing"] = False
    if "ai_assistant_minimized" not in st.session_state:
        st.session_state["ai_assistant_minimized"] = False

    # ── Custom CSS for AI Assistant ────────────────────────────────────────
    st.markdown("""
    <style>
        /* Floating AI Assistant Button */
        .ai-assistant-float-btn {
            position: fixed;
            bottom: 24px;
            right: 24px;
            width: 56px;
            height: 56px;
            border-radius: 50%;
            background: linear-gradient(135deg, #6366F1 0%, #8B5CF6 100%);
            border: none;
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
            box-shadow: 0 4px 20px rgba(99, 102, 241, 0.4), 0 2px 8px rgba(0,0,0,0.1);
            z-index: 9999;
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
            animation: pulse 2s infinite;
        }
        
        .ai-assistant-float-btn:hover {
            transform: scale(1.1);
            box-shadow: 0 8px 30px rgba(99, 102, 241, 0.5), 0 4px 12px rgba(0,0,0,0.15);
        }
        
        .ai-assistant-float-btn:active {
            transform: scale(0.95);
        }
        
        @keyframes pulse {
            0%, 100% { box-shadow: 0 4px 20px rgba(99, 102, 241, 0.4), 0 2px 8px rgba(0,0,0,0.1); }
            50% { box-shadow: 0 6px 25px rgba(99, 102, 241, 0.5), 0 4px 12px rgba(0,0,0,0.15); }
        }
        
        .ai-assistant-float-btn svg {
            width: 24px;
            height: 24px;
            color: white;
        }
        
        /* Chat Panel */
        .ai-assistant-panel {
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
            animation: slideInRight 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        }
        
        @keyframes slideInRight {
            from { opacity: 0; transform: translateX(30px); }
            to { opacity: 1; transform: translateX(0); }
        }
        
        /* Header */
        .ai-assistant-header {
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 16px 20px;
            background: linear-gradient(135deg, #6366F1 0%, #8B5CF6 100%);
            color: white;
            position: relative;
        }
        
        .ai-assistant-header h3 {
            margin: 0;
            font-size: 1.1rem;
            font-weight: 700;
            display: flex;
            align-items: center;
            gap: 10px;
        }
        
        .ai-assistant-header .status-indicator {
            width: 8px;
            height: 8px;
            border-radius: 50%;
            background: #10B981;
            animation: pulse-green 2s infinite;
        }
        
        @keyframes pulse-green {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.5; }
        }
        
        .header-actions {
            display: flex;
            gap: 8px;
        }
        
        .header-btn {
            width: 32px;
            height: 32px;
            border-radius: 8px;
            background: rgba(255, 255, 255, 0.2);
            border: none;
            color: white;
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
            transition: all 0.2s ease;
        }
        
        .header-btn:hover {
            background: rgba(255, 255, 255, 0.3);
            transform: scale(1.1);
        }
        
        .header-btn svg {
            width: 18px;
            height: 18px;
        }
        
        /* Quick Prompts */
        .quick-prompts {
            padding: 16px;
            border-bottom: 1px solid #F1F5F9;
            background: #FAFAFA;
        }
        
        .quick-prompts-label {
            font-size: 0.75rem;
            font-weight: 600;
            color: #64748B;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            margin-bottom: 10px;
        }
        
        .quick-prompts-grid {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 8px;
        }
        
        .quick-prompt-btn {
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
            transition: all 0.15s ease;
            text-align: left;
            height: 44px;
        }
        
        .quick-prompt-btn:hover {
            background: #F1F5F9;
            border-color: #CBD5E1;
            transform: translateY(-1px);
            box-shadow: 0 2px 8px rgba(0,0,0,0.05);
        }
        
        .quick-prompt-btn svg {
            width: 16px;
            height: 16px;
            color: #6366F1;
            flex-shrink: 0;
        }
        
        /* Messages Area */
        .messages-area {
            flex: 1;
            overflow-y: auto;
            padding: 20px;
            display: flex;
            flex-direction: column;
            gap: 16px;
            background: #FFFFFF;
        }
        
        /* Message Bubbles */
        .message-row {
            display: flex;
            gap: 10px;
            max-width: 85%;
            animation: fadeInUp 0.3s ease;
        }
        
        @keyframes fadeInUp {
            from { opacity: 0; transform: translateY(10px); }
            to { opacity: 1; transform: translateY(0); }
        }
        
        .message-row.assistant {
            align-self: flex-start;
        }
        
        .message-row.user {
            align-self: flex-end;
            flex-direction: row-reverse;
        }
        
        .message-avatar {
            width: 32px;
            height: 32px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            flex-shrink: 0;
            font-size: 14px;
        }
        
        .assistant-avatar {
            background: linear-gradient(135deg, #6366F1 0%, #8B5CF6 100%);
            color: white;
        }
        
        .user-avatar {
            background: linear-gradient(135deg, #3B82F6 0%, #06B6D4 100%);
            color: white;
        }
        
        .message-bubble {
            max-width: 100%;
            padding: 12px 16px;
            border-radius: 18px;
            font-size: 0.9rem;
            line-height: 1.6;
            color: #1E293B;
            word-wrap: break-word;
            position: relative;
        }
        
        .assistant-bubble {
            background: #FFFFFF;
            border: 1px solid #E2E8F0;
            border-radius: 18px 18px 18px 4px;
            box-shadow: 0 1px 2px rgba(0,0,0,0.03), 0 1px 1px rgba(0,0,0,0.02);
        }
        
        .user-bubble {
            background: #EEF4FF;
            border: 1px solid #DBEAFE;
            border-radius: 18px 18px 4px 18px;
            box-shadow: 0 1px 2px rgba(59, 130, 246, 0.08);
        }
        
        .message-header {
            display: flex;
            align-items: center;
            gap: 8px;
            margin-bottom: 6px;
            font-size: 0.7rem;
            color: #64748B;
            font-weight: 500;
        }
        
        .user-header {
            justify-content: flex-end;
            text-align: right;
        }
        
        /* Typing Indicator */
        .typing-indicator {
            display: flex;
            gap: 4px;
            padding: 12px 16px;
        }
        
        .typing-dot {
            width: 8px;
            height: 8px;
            border-radius: 50%;
            background: #6366F1;
            animation: typingBounce 1.4s infinite ease-in-out;
        }
        
        .typing-dot:nth-child(2) { animation-delay: 0.2s; }
        .typing-dot:nth-child(3) { animation-delay: 0.4s; }
        
        @keyframes typingBounce {
            0%, 60%, 100% { transform: translateY(0); }
            30% { transform: translateY(-6px); }
        }
        
        /* Action Card */
        .action-card {
            background: #FEF3F0;
            border: 1px solid #FED7CC;
            border-radius: 12px;
            padding: 16px;
            margin-top: 12px;
        }
        
        .action-card-header {
            display: flex;
            align-items: center;
            gap: 8px;
            font-weight: 600;
            color: #EA580C;
            margin-bottom: 8px;
            font-size: 0.85rem;
        }
        
        .action-card pre {
            background: #FFF7ED;
            border: 1px solid #FED7CC;
            border-radius: 8px;
            padding: 12px;
            font-size: 0.75rem;
            overflow-x: auto;
            color: #9A3412;
        }
        
        /* Input Area */
        .input-area {
            padding: 16px 20px;
            border-top: 1px solid #F1F5F9;
            background: #FAFAFA;
        }
        
        .input-container {
            display: flex;
            align-items: flex-end;
            gap: 10px;
            background: #FFFFFF;
            border: 1px solid #E2E8F0;
            border-radius: 20px;
            padding: 8px 16px;
            transition: all 0.2s ease;
        }
        
        .input-container:focus-within {
            border-color: #6366F1;
            box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.1);
        }
        
        .attachment-btn {
            width: 36px;
            height: 36px;
            border-radius: 50%;
            background: #F1F5F9;
            border: none;
            display: flex;
            align-items: center;
            justify-content: center;
            cursor: pointer;
            color: #64748B;
            transition: all 0.15s ease;
        }
        
        .attachment-btn:hover {
            background: #E2E8F0;
            color: #334155;
        }
        
        .attachment-btn svg {
            width: 18px;
            height: 18px;
        }
        
        .chat-input {
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
            padding: 8px 0;
        }
        
        .chat-input::placeholder {
            color: #94A3B8;
        }
        
        .send-btn {
            width: 36px;
            height: 36px;
            border-radius: 50%;
            background: linear-gradient(135deg, #6366F1 0%, #8B5CF6 100%);
            border: none;
            display: flex;
            align-items: center;
            justify-content: center;
            cursor: pointer;
            color: white;
            transition: all 0.15s ease;
            flex-shrink: 0;
        }
        
        .send-btn:hover {
            transform: scale(1.05);
            box-shadow: 0 4px 12px rgba(99, 102, 241, 0.3);
        }
        
        .send-btn:active {
            transform: scale(0.98);
        }
        
        .send-btn svg {
            width: 18px;
            height: 18px;
        }
        
        /* File Upload Preview */
        .file-preview {
            display: flex;
            align-items: center;
            gap: 8px;
            background: #EEF2FF;
            border: 1px solid #DBEAFE;
            border-radius: 8px;
            padding: 8px 12px;
            margin-bottom: 12px;
            font-size: 0.8rem;
            color: #1E40AF;
        }
        
        .file-preview button {
            background: none;
            border: none;
            color: #3B82F6;
            cursor: pointer;
            font-size: 1rem;
            padding: 0 4px;
        }
        
        /* Clear Chat Button */
        .clear-chat-btn {
            display: inline-flex;
            align-items: center;
            gap: 6px;
            padding: 8px 16px;
            background: #FEF2F2;
            border: 1px solid #FECACA;
            border-radius: 8px;
            color: #DC2626;
            font-size: 0.8rem;
            font-weight: 500;
            cursor: pointer;
            transition: all 0.15s ease;
        }
        
        .clear-chat-btn:hover {
            background: #FEF2F2;
            border-color: #FCA5A5;
        }
        
        /* Scrollbar */
        .messages-area::-webkit-scrollbar {
            width: 6px;
        }
        .messages-area::-webkit-scrollbar-track {
            background: transparent;
        }
        .messages-area::-webkit-scrollbar-thumb {
            background: #CBD5E1;
            border-radius: 3px;
        }
        .messages-area::-webkit-scrollbar-thumb:hover {
            background: #94A3B8;
        }
        
        /* Hide Streamlit default chat elements */
        .stChatMessage {
            display: none !important;
        }
        .stChatInputContainer {
            display: none !important;
        }
    </style>
    """, unsafe_allow_html=True)

    # ── Floating Button ────────────────────────────────────────────────────
    if not st.session_state["ai_assistant_open"]:
        if st.button("🤖", key="ai_assistant_toggle", help="Open AI Assistant", 
                     use_container_width=False):
            st.session_state["ai_assistant_open"] = True
            st.rerun()
        return

    # ── Main Chat Panel ────────────────────────────────────────────────────
    st.markdown('<div class="ai-assistant-panel">', unsafe_allow_html=True)
    
    # Header
    st.markdown("""
    <div class="ai-assistant-header">
        <h3>🤖 HirePilot</h3>
        <div class="status-indicator"></div>
        <div class="header-actions">
            <button class="header-btn" title="Minimize" onclick="minimizeChat()">
                <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="5" y1="12" x2="19" y2="12"></line></svg>
            </button>
            <button class="header-btn" title="Close" onclick="closeChat()">
                <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line></svg>
            </button>
        </div>
    """, unsafe_allow_html=True)
    
    # Quick Prompts
    suggestions = [
        "How many open roles do we have?",
        "Who are the top candidates for the Data Scientist role?",
        "Draft a rejection email for candidate ID 1.",
        "What is our current hiring velocity?"
    ]
    
    prompt_icons = {
        "How many open roles do we have?": "📋",
        "Who are the top candidates for the Data Scientist role?": "👥",
        "Draft a rejection email for candidate ID 1.": "✉️",
        "What is our current hiring velocity?": "📈"
    }
    
    st.markdown('<div class="quick-prompts">', unsafe_allow_html=True)
    st.markdown('<div class="quick-prompts-label">Quick Actions</div>', unsafe_allow_html=True)
    st.markdown('<div class="quick-prompts-grid">', unsafe_allow_html=True)
    
    prompt_cols = st.columns(2, gap="small")
    prompt_trigger = None
    for i, label in enumerate(suggestions[:4]):
        with prompt_cols[i % 2]:
            icon = prompt_icons.get(label, "💡")
            if st.button(f"{icon} {label}", key=f"qp_{i}", use_container_width=True):
                prompt_trigger = label
    st.markdown('</div></div>', unsafe_allow_html=True)
    
    # ── Chat Messages Area ───────────────────────────────────────────────
    st.markdown('<div class="messages-area" id="chat-messages">', unsafe_allow_html=True)
    
    for idx, message in enumerate(st.session_state["ai_assistant_messages"]):
        role = message["role"]
        content = message["content"]
        action = message.get("action")
        
        if role == "assistant":
            st.markdown(f'''
            <div class="message-row assistant">
                <div class="message-avatar assistant-avatar">🤖</div>
                <div class="message-bubble assistant-bubble">
                    <div class="message-header">
                        <span>HirePilot</span>
                        <span>•</span>
                        <span>Just now</span>
                    </div>
                    {content}
                </div>
            </div>
            ''', unsafe_allow_html=True)
            
            # Action card
            action = message.get("action")
            if action:
                if action.get("confirmed"):
                    st.success(f"Action '{action['type']}' executed successfully.")
                else:
                    st.markdown(f'''
                    <div class="action-card">
                        <div class="action-card-header">⚡ Confirm Action: {action["type"]}</div>
                        <pre>{json.dumps(action["payload"], indent=2)}</pre>
                    </div>
                    ''', unsafe_allow_html=True)
                    if st.button("Confirm", key=f"confirm_{idx}"):
                        res = confirm_copilot_action(
                            st.session_state["copilot_session_id"],
                            action["type"],
                            action["payload"]
                        )
                        if res:
                            st.session_state["messages"][idx]["action"]["confirmed"] = True
                            st.rerun()
        
        else:  # user
            st.markdown(f'''
            <div class="message-row user">
                <div class="message-bubble user-bubble">
                    <div class="message-header user-header">
                        <span>You</span>
                        <span>•</span>
                        <span>Just now</span>
                    </div>
                    {content}
                </div>
                <div class="message-avatar user-avatar">👤</div>
            </div>
            ''', unsafe_allow_html=True)
    
    # Typing indicator
    if st.session_state.get("show_typing", False):
        st.markdown('''
        <div class="message-row assistant">
            <div class="message-avatar assistant-avatar">🤖</div>
            <div class="message-bubble assistant-bubble">
                <div class="typing-indicator">
                    <div class="typing-dot"></div>
                    <div class="typing-dot"></div>
                    <div class="typing-dot"></div>
                </div>
            </div>
        </div>
        ''', unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # ── Input Area ───────────────────────────────────────────────────────
    st.markdown('<div class="input-area">', unsafe_allow_html=True)
    
    # File upload preview
    if "uploaded_files" in st.session_state and st.session_state["uploaded_files"]:
        for i, f in enumerate(st.session_state["uploaded_files"]):
            st.markdown(f'''
            <div class="file-preview">
                📎 {f["name"]}
                <button onclick="this.parentElement.remove()">×</button>
            </div>
            ''', unsafe_allow_html=True)
    
    # Input container
    st.markdown('<div class="input-container">', unsafe_allow_html=True)
    
    # Attachment button
    uploaded_file = st.file_uploader(
        "", 
        type=["pdf", "docx", "doc", "txt", "xlsx", "csv"],
        key="ai_assistant_file_upload",
        label_visibility="collapsed",
        accept_multiple_files=False,
        help="Upload Resume"
    )
    
    # Text input
    user_input = st.chat_input("Ask HirePilot anything about candidates, jobs, interviews, resumes...", key="ai_assistant_input")
    
    st.markdown('</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Handle file upload
    file_message = None
    if uploaded_file is not None:
        file_message = f"📎 **File uploaded**: {uploaded_file.name}"
        if "uploaded_files" not in st.session_state:
            st.session_state["uploaded_files"] = []
        st.session_state["uploaded_files"].append({
            "name": uploaded_file.name,
            "content": uploaded_file.getvalue(),
            "type": uploaded_file.type
        })
        st.success(f"✅ File '{uploaded_file.name}' uploaded successfully!")
        uploaded_file = None
    
    if prompt_trigger:
        user_input = prompt_trigger
    
    if user_input:
        # Include file message if file was uploaded
        full_message = user_input
        if file_message:
            full_message = f"{file_message}\n\n{user_input}"
        
        st.session_state["ai_assistant_messages"].append({"role": "user", "content": full_message, "action": None})
        
        # Show typing indicator
        st.session_state["show_typing"] = True
        st.rerun()
    
    # Handle AI response generation (when typing indicator is shown)
    if st.session_state.get("show_typing", False) and st.session_state["ai_assistant_messages"][-1]["role"] == "user":
        st.session_state["show_typing"] = False
        
        last_user_message = st.session_state["ai_assistant_messages"][-1]["content"]
        
        with st.spinner("AI is thinking…"):
            response = chat_with_copilot(st.session_state["copilot_session_id"], last_user_message)
            
            if response:
                reply_text = response.get("reply", "I processed your request.")
                action_req = response.get("action_required", False)
                action_data = None
                if action_req:
                    action_data = {
                        "type": response.get("action_type"),
                        "payload": response.get("action_payload", {}),
                        "confirmed": False
                    }
            else:
                reply_text = "⚠️ Connection to the Copilot API failed."
                action_data = None
            
            # Stream the response
            response_container = st.empty()
            full_response = ""
            for chunk in _stream(reply_text):
                full_response += chunk
                response_container.markdown(full_response)
            
            if action_data:
                st.info("Please confirm the action above to proceed.")
            
            st.session_state["ai_assistant_messages"].append({
                "role": "assistant",
                "content": reply_text,
                "action": action_data
            })
            st.rerun()

    # ── Clear Chat ───────────────────────────────────────────────────────
    st.markdown("<div style='height:10px;'></div>", unsafe_allow_html=True)
    if len(st.session_state["ai_assistant_messages"]) > 1:
        if st.button("🗑️ Clear Chat History", type="secondary", key="clear_chat"):
            st.session_state["ai_assistant_messages"] = [st.session_state["ai_assistant_messages"][0]]
            st.session_state["ai_assistant_session_id"] = str(uuid.uuid4())
            st.rerun()

    st.markdown('</div>', unsafe_allow_html=True)  # Close ai-assistant-panel


def _stream(text: str):
    for word in text.split(" "):
        yield word + " "
        time.sleep(0.012)