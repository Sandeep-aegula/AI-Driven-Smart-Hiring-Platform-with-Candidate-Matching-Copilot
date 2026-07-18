import time
import uuid
import streamlit as st
from frontend.components.api_client import chat_with_copilot, confirm_copilot_action, get_copilot_suggestions

def render_ai_copilot() -> None:
    if "copilot_session_id" not in st.session_state:
        st.session_state["copilot_session_id"] = str(uuid.uuid4())
        
    if "messages" not in st.session_state or not st.session_state["messages"]:
        st.session_state["messages"] = [{
            "role": "assistant",
            "content": ("Hello! I'm HirePilot's AI Copilot, running locally on "
                        "`qwen2.5-coder:7b`. Select a quick action or ask anything "
                        "about recruitment, resumes, or hiring strategy."),
            "action": None
        }]

    st.markdown("""
    <style>
        .ai-copilot-container {
            width: 100%;
            margin: 0;
            padding: 0;
        }
        .chat-header {
            margin-bottom: 20px;
        }
        .quick-prompts-section {
            margin-bottom: 24px;
        }
        .quick-prompts-section > div {
            gap: 8px;
        }
        .quick-prompt-btn {
            width: 100%;
            padding: 8px 12px;
            border-radius: 8px;
            background-color: #FFFFFF;
            border: 1px solid #E2E8F0;
            color: #0F172A;
            font-weight: 500;
            cursor: pointer;
            transition: all 0.2s ease;
        }
        .quick-prompt-btn:hover {
            background-color: #F1F5F9;
            border-color: #CBD5E1;
        }
        .chat-input-area {
            background-color: #FFFFFF;
            border-top: 1px solid #E2E8F0;
            padding: 16px;
            border-radius: 8px;
            margin-top: 20px;
        }
        .file-input-wrapper {
            display: flex;
            align-items: center;
            gap: 8px;
            margin-top: 12px;
        }
    </style>
    <div class="ai-copilot-container">
        <div class="chat-header">
            <h1 style="font-size:1.6rem;font-weight:800;color:#0F172A;margin:0 0 4px 0;">
                🤖 AI Copilot
            </h1>
            <p style="font-size:0.85rem;color:#64748B;margin:0 0 0 0;font-weight:500;">
                Context-aware recruitment assistant powered by local Ollama
            </p>
        </div>
        <hr style="margin:12px 0 20px 0;border:none;border-top:1px solid #F1F5F9;">
    </div>
    """, unsafe_allow_html=True)

    # ── Quick Prompts ─────────────────────────────────────────────────────
    st.markdown("<div class='quick-prompts-section'><p style='font-size: 0.9rem; font-weight: 600; color: #0F172A; margin: 0 0 12px 0;'>⚡ Quick Prompts:</p></div>", unsafe_allow_html=True)
    
    # Load dynamic suggestions
    suggestions = get_copilot_suggestions()
    if not suggestions:
        suggestions = [
            "How many open roles do we have?",
            "Who are the top candidates for the Data Scientist role?",
            "Draft a rejection email for candidate ID 1.",
            "What is our current hiring velocity?"
        ]
    
    prompt_trigger = None
    q_cols = st.columns([1, 1, 1, 1], gap="small")
    for i, label in enumerate(suggestions[:4]):
        with q_cols[i]:
            if st.button(label, use_container_width=True, key=f"qp_{i}"):
                prompt_trigger = label

    st.markdown("<div style='height: 16px;'></div>", unsafe_allow_html=True)

    # ── Chat History ──────────────────────────────────────────────────────
    for idx, message in enumerate(st.session_state["messages"]):
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
            
            # If the assistant proposed an action, show a confirmation card
            action = message.get("action")
            if action:
                if action.get("confirmed"):
                    st.success(f"Action '{action['type']}' executed successfully.")
                else:
                    with st.container(border=True):
                        st.markdown(f"**Confirm Action: {action['type']}**")
                        st.json(action["payload"])
                        if st.button("Confirm", key=f"confirm_{idx}"):
                            res = confirm_copilot_action(
                                st.session_state["copilot_session_id"],
                                action["type"],
                                action["payload"]
                            )
                            if res:
                                st.session_state["messages"][idx]["action"]["confirmed"] = True
                                st.rerun()

    # ── Input & File Upload (Combined) ─────────────────────────────────────
    st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)
    
    st.markdown("""
    <style>
        .unified-input-container {
            display: flex;
            align-items: center;
            gap: 8px;
            background-color: #FFFFFF;
            border: 1px solid #E2E8F0;
            border-radius: 8px;
            padding: 6px 8px;
            transition: all 0.2s ease;
        }
        
        .unified-input-container:focus-within {
            border-color: #6366F1;
            box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.1);
        }
        
        .input-text-section {
            flex: 1;
            display: flex;
            align-items: center;
        }
        
        .input-file-section {
            display: flex;
            align-items: center;
            gap: 4px;
        }
    </style>
    """, unsafe_allow_html=True)
    
    # Create a single row for combined input
    unified_col1, unified_col2 = st.columns([1, 12], gap="small")
    
    with unified_col1:
        # File upload button with "+" icon
        uploaded_file = st.file_uploader(
            "", 
            type=["pdf", "docx", "doc", "txt", "xlsx", "csv"],
            key="copilot_file_unified",
            label_visibility="collapsed",
            accept_multiple_files=False,
            help="Click to upload file (PDF, DOCX, TXT, XLSX, CSV)"
        )
    
    with unified_col2:
        # Text input
        user_input = st.chat_input("Message AI Copilot…", key="copilot_input_unified")
    
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
        
        st.session_state["messages"].append({"role":"user", "content":full_message, "action": None})
        with st.chat_message("user"):
            st.markdown(full_message)

        with st.chat_message("assistant"):
            with st.spinner("AI is thinking…"):
                response = chat_with_copilot(st.session_state["copilot_session_id"], user_input)
                
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

            response_container = st.empty()
            full_response = ""
            for chunk in _stream(reply_text):
                full_response += chunk
                response_container.markdown(full_response)
                
            if action_data:
                st.info("Please confirm the action above to proceed.")

        st.session_state["messages"].append({
            "role":"assistant",
            "content":reply_text,
            "action": action_data
        })
        st.rerun()

    # ── Clear Chat ────────────────────────────────────────────────────────
    st.markdown("<div style='height:10px;'></div>", unsafe_allow_html=True)
    if len(st.session_state["messages"]) > 1:
        if st.button("🗑️ Clear Chat History", type="secondary"):
            st.session_state["messages"] = [st.session_state["messages"][0]]
            # Generate new session ID
            st.session_state["copilot_session_id"] = str(uuid.uuid4())
            st.rerun()


def _stream(text: str):
    for word in text.split(" "):
        yield word + " "
        time.sleep(0.012)
