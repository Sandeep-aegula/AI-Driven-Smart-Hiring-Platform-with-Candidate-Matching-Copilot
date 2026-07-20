import json
import time
import uuid
import streamlit as st
from datetime import datetime

def _get_mock_ai_response(user_message: str) -> dict:
    """Generate a mock AI response based on user input keywords."""
    msg = user_message.lower()
    if "resume" in msg or "cv" in msg:
        return {
            "type": "resume_analysis",
            "content": "I've analyzed the resume. Here are the key findings:",
            "table": {
                "headers": ["Candidate", "Match Score", "Experience", "Skills"],
                "rows": [
                    ["Alice Johnson", "95%", "5 yrs", "Python, ML, NLP"],
                    ["Bob Smith", "88%", "4 yrs", "React, TS, Node"],
                    ["Carol Davis", "82%", "6 yrs", "Java, Spring, SQL"],
                ],
            },
        }
    if "candidate" in msg or "find" in msg or "search" in msg:
        return {
            "type": "candidate_table",
            "content": "Here are the top candidates matching your criteria:",
            "table": {
                "headers": ["Candidate", "Match Score", "Experience", "Skills"],
                "rows": [
                    ["Alice Johnson", "95%", "5 yrs", "Python, ML, NLP"],
                    ["Bob Smith", "88%", "4 yrs", "React, TS, Node"],
                    ["Carol Davis", "82%", "6 yrs", "Java, Spring, SQL"],
                ],
            },
        }
    if "interview" in msg or "question" in msg:
        return {
            "type": "interview_questions",
            "content": "Here are suggested interview questions based on the role:",
            "bullets": [
                "Tell me about a challenging project you led.",
                "How do you handle tight deadlines?",
                "Describe your experience with team collaboration.",
            ],
        }
    if "job" in msg or "insight" in msg or "analytics" in msg:
        return {
            "type": "job_insights",
            "content": "Here are the current job market insights:",
            "bullets": [
                "Data Scientist roles have 45% more applicants this month.",
                "Average time-to-hire decreased by 12%.",
                "Top skills in demand: Python, React, AWS.",
            ],
        }
    return {
        "type": "generic",
        "content": "I can help you with candidate search, resume screening, interview preparation, hiring insights, and job analytics. What would you like to explore?",
    }


def render_ai_copilot() -> None:
    if "copilot_session_id" not in st.session_state:
        st.session_state["copilot_session_id"] = str(uuid.uuid4())
    if "messages" not in st.session_state or not st.session_state["messages"]:
        st.session_state["messages"] = [
            {
                "role": "assistant",
                "content": "Hello! I'm HirePilot's AI Copilot. I can help you with candidate search, resume screening, interview preparation, hiring insights, and job analytics.",
            }
        ]
    if "show_typing" not in st.session_state:
        st.session_state["show_typing"] = False
    if "uploaded_files" not in st.session_state:
        st.session_state["uploaded_files"] = []

    st.markdown(
        """
    <style>
    /* Page layout */
    .ai-copilot-page {
        display: flex;
        flex-direction: column;
        height: calc(100vh - 140px);
        min-height: 600px;
        background: #fff;
        border: 1px solid #E5E7EB;
        border-radius: 16px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        overflow: hidden;
    }
    .ai-copilot-header {
        padding: 20px 24px 12px;
        border-bottom: 1px solid #E5E7EB;
        background: #fff;
        flex-shrink: 0;
    }
    .ai-copilot-body {
        display: flex;
        flex: 1;
        overflow: hidden;
    }
    .ai-copilot-left {
        flex: 72;
        display: flex;
        flex-direction: column;
        overflow: hidden;
        border-right: 1px solid #E5E7EB;
    }
    .ai-copilot-right {
        flex: 28;
        display: flex;
        flex-direction: column;
        gap: 16px;
        padding: 16px;
        overflow-y: auto;
    }
    .ai-copilot-conversation {
        flex: 1;
        overflow-y: auto;
        padding: 20px 24px;
        display: flex;
        flex-direction: column;
        gap: 16px;
    }
    .ai-copilot-input-wrapper {
        flex-shrink: 0;
        padding: 12px 16px;
        border-top: 1px solid #E5E7EB;
        background: #fff;
    }
    /* Modern chat input bar */
    .modern-chat-input {
        background: #fff;
        border: 1px solid #E5E7EB;
        border-radius: 16px;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.08);
        padding: 8px 10px;
        display: flex;
        align-items: center;
        gap: 6px;
        min-height: 56px;
    }
    .modern-chat-input > div {
        flex: 1 1 auto;
        min-height: 40px;
        display: flex;
        align-items: center;
    }
    .modern-chat-input .stButton > button {
        width: 36px !important;
        height: 36px !important;
        padding: 0 !important;
        border-radius: 10px !important;
        background: transparent !important;
        border: 1px solid transparent !important;
        color: #374151 !important;
        font-size: 18px !important;
        min-height: unset !important;
        height: 36px !important;
        display: inline-flex !important;
        align-items: center !important;
        justify-content: center !important;
        flex-shrink: 0 !important;
    }
    .modern-chat-input .stButton > button:hover {
        background: #F3F4F6 !important;
        border-color: #E5E7EB !important;
    }
    .modern-chat-input .stTextInput {
        flex: 1 1 auto !important;
        min-width: 0 !important;
    }
    .modern-chat-input .stTextInput > div {
        border: none !important;
        outline: none !important;
        box-shadow: none !important;
        background: transparent !important;
        padding: 0 !important;
    }
    .modern-chat-input .stTextInput > div > div > input {
        border: none !important;
        outline: none !important;
        box-shadow: none !important;
        background: transparent !important;
        font-size: 15px !important;
        color: #111827 !important;
        padding: 10px 2px !important;
        min-height: 36px !important;
        height: 36px !important;
        line-height: 36px !important;
    }
    .modern-chat-input .stTextInput > div > div > input::placeholder {
        color: #6B7280 !important;
    }
    .modern-chat-input .stButton[kind="primary"] > button,
    .modern-chat-input button[aria-label="Send message"] {
        width: 40px !important;
        height: 40px !important;
        padding: 0 !important;
        border-radius: 50% !important;
        background: #6366F1 !important;
        color: #fff !important;
        border: none !important;
        font-size: 18px !important;
        min-height: unset !important;
        display: inline-flex !important;
        align-items: center !important;
        justify-content: center !important;
        box-shadow: 0 1px 2px rgba(99, 102, 241, 0.35) !important;
        flex-shrink: 0 !important;
    }
    .modern-chat-input .stButton[kind="primary"] > button:hover,
    .modern-chat-input button[aria-label="Send message"]:hover {
        background: #4F46E5 !important;
    }
    /* Message bubbles */
    .chat-message {
        display: flex;
        gap: 12px;
        max-width: 85%;
        animation: fadeIn 0.3s ease;
    }
    .chat-message.user {
        align-self: flex-end;
        flex-direction: row-reverse;
    }
    .chat-message.assistant {
        align-self: flex-start;
    }
    .chat-avatar {
        width: 32px;
        height: 32px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 16px;
        flex-shrink: 0;
    }
    .chat-avatar.ai {
        background: #EEF2FF;
        color: #6366F1;
    }
    .chat-avatar.user {
        background: #F3F4F6;
        color: #374151;
    }
    .chat-bubble {
        padding: 12px 16px;
        border-radius: 16px;
        font-size: 14px;
        line-height: 1.5;
        position: relative;
    }
    .chat-message.user .chat-bubble {
        background: #6366F1;
        color: #fff;
        border-bottom-right-radius: 4px;
    }
    .chat-message.assistant .chat-bubble {
        background: #fff;
        border: 1px solid #E5E7EB;
        color: #111827;
        border-bottom-left-radius: 4px;
        box-shadow: 0 1px 2px rgba(0,0,0,0.05);
    }
    .chat-timestamp {
        font-size: 11px;
        color: #9CA3AF;
        margin-top: 4px;
    }
    .chat-message.user .chat-timestamp {
        text-align: right;
    }
    /* Action buttons */
    .chat-actions {
        display: flex;
        gap: 8px;
        margin-top: 8px;
    }
    .chat-actions button {
        font-size: 12px !important;
        padding: 4px 10px !important;
        border-radius: 8px !important;
        border: 1px solid #E5E7EB !important;
        background: #fff !important;
        color: #374151 !important;
    }
    .chat-actions button:hover {
        background: #F9FAFB !important;
        border-color: #D1D5DB !important;
    }
    /* Rich response table */
    .rich-table {
        width: 100%;
        border-collapse: collapse;
        margin-top: 12px;
        font-size: 13px;
        border: 1px solid #E5E7EB;
        border-radius: 12px;
        overflow: hidden;
    }
    .rich-table th {
        background: #F9FAFB;
        padding: 10px 12px;
        text-align: left;
        font-weight: 600;
        color: #374151;
        border-bottom: 1px solid #E5E7EB;
    }
    .rich-table td {
        padding: 10px 12px;
        border-bottom: 1px solid #F3F4F6;
        color: #111827;
    }
    .rich-table tr:last-child td {
        border-bottom: none;
    }
    .skill-pill {
        display: inline-block;
        padding: 2px 8px;
        border-radius: 999px;
        background: #EEF2FF;
        color: #4338CA;
        font-size: 11px;
        font-weight: 500;
        margin: 2px;
    }
    .match-score {
        font-weight: 600;
    }
    .match-score.high { color: #059669; }
    .match-score.medium { color: #D97706; }
    .match-score.low { color: #DC2626; }
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(8px); }
        to { opacity: 1; transform: translateY(0); }
    }
    /* Scrollbar styling */
    .ai-copilot-conversation::-webkit-scrollbar {
        width: 6px;
    }
    .ai-copilot-conversation::-webkit-scrollbar-track {
        background: transparent;
    }
    .ai-copilot-conversation::-webkit-scrollbar-thumb {
        background: #D1D5DB;
        border-radius: 3px;
    }
    .ai-copilot-conversation::-webkit-scrollbar-thumb:hover {
        background: #9CA3AF;
    }
    </style>
    """,
        unsafe_allow_html=True,
    )

    # Main page container
    st.markdown('<div class="ai-copilot-page">', unsafe_allow_html=True)

    # Header
    st.markdown('<div class="ai-copilot-header">', unsafe_allow_html=True)
    st.title("AI Copilot")
    st.caption("Your intelligent recruitment assistant")
    st.markdown('</div>', unsafe_allow_html=True)

    # Body with two columns
    st.markdown('<div class="ai-copilot-body">', unsafe_allow_html=True)

    # Left column - Conversation
    st.markdown('<div class="ai-copilot-left">', unsafe_allow_html=True)
    st.markdown('<div class="ai-copilot-conversation" id="conversation">', unsafe_allow_html=True)

    for msg in st.session_state["messages"]:
        role = msg["role"]
        content = msg["content"]
        timestamp = msg.get("timestamp", datetime.now().strftime("%H:%M"))
        avatar = "🤖" if role == "assistant" else "👤"
        css_class = "assistant" if role == "assistant" else "user"

        st.markdown(
            f'<div class="chat-message {css_class}">'
            f'<div class="chat-avatar {css_class}">{avatar}</div>'
            f'<div>'
            f'<div class="chat-bubble">{content}</div>'
            f'<div class="chat-timestamp">{timestamp}</div>'
            f'</div>'
            f'</div>',
            unsafe_allow_html=True,
        )

        # Rich response rendering for assistant
        if role == "assistant" and msg.get("rich_type"):
            rich_type = msg["rich_type"]
            if rich_type == "table" and msg.get("table_data"):
                table = msg["table_data"]
                headers = table.get("headers", [])
                rows = table.get("rows", [])
                if headers and rows:
                    html = '<table class="rich-table"><thead><tr>'
                    for h in headers:
                        html += f"<th>{h}</th>"
                    html += "</tr></thead><tbody>"
                    for row in rows:
                        html += "<tr>"
                        for i, cell in enumerate(row):
                            if headers[i] == "Match Score":
                                score = cell.replace("%", "")
                                try:
                                    score_val = int(score)
                                    if score_val >= 90:
                                        css_score = "high"
                                    elif score_val >= 75:
                                        css_score = "medium"
                                    else:
                                        css_score = "low"
                                except ValueError:
                                    css_score = "medium"
                                html += f'<td><span class="match-score {css_score}">{cell}</span></td>'
                            elif headers[i] == "Skills":
                                skills = [s.strip() for s in cell.split(",")]
                                html += "<td>"
                                for skill in skills:
                                    html += f'<span class="skill-pill">{skill}</span>'
                                html += "</td>"
                            else:
                                html += f"<td>{cell}</td>"
                        html += "</tr>"
                    html += "</tbody></table>"
                    st.markdown(html, unsafe_allow_html=True)

            if rich_type == "bullets" and msg.get("bullets"):
                for bullet in msg["bullets"]:
                    st.markdown(f"- {bullet}")

        # Action buttons for assistant messages
        if role == "assistant":
            col1, col2, col3 = st.columns(3)
            col1.button("📋 Copy", key=f"copy_{msg.get('id', uuid.uuid4().hex)}", help="Copy response")
            col2.button("👍 Like", key=f"like_{msg.get('id', uuid.uuid4().hex)}", help="Like this response")
            col3.button("👎 Dislike", key=f"dislike_{msg.get('id', uuid.uuid4().hex)}", help="Dislike this response")

    # Typing indicator
    if st.session_state.get("show_typing", False):
        st.markdown(
            '<div class="chat-message assistant">'
            '<div class="chat-avatar ai">🤖</div>'
            '<div><div class="chat-bubble">Thinking…</div></div>'
            '</div>',
            unsafe_allow_html=True,
        )

    st.markdown('</div>', unsafe_allow_html=True)  # Close conversation

    # Fixed input area
    st.markdown('<div class="ai-copilot-input-wrapper">', unsafe_allow_html=True)
    st.markdown('<div class="modern-chat-input">', unsafe_allow_html=True)
    col_attach, col_input, col_send = st.columns([0.08, 0.84, 0.08], gap="small")
    with col_attach:
        st.button("📎", key="attach_btn", help="Attach file", use_container_width=True)
    with col_input:
        user_input = st.text_input(
            "Message",
            placeholder="Ask anything about candidates, jobs, interviews...",
            label_visibility="collapsed",
            key="modern_chat_input",
        )
    with col_send:
        send_clicked = st.button("➤", key="send_btn", help="Send message", type="primary", use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)  # Close left column

    # Right column - Quick actions & Recent conversations
    st.markdown('<div class="ai-copilot-right">', unsafe_allow_html=True)

    with st.container(border=True):
        st.subheader("What can I help you with?")
        actions = [
            {"icon": "🔍", "title": "Find best candidates", "subtitle": "Search talent pool"},
            {"icon": "📊", "title": "Job insights", "subtitle": "Market analytics"},
            {"icon": "📝", "title": "Screening summary", "subtitle": "Candidate evaluation"},
            {"icon": "🎯", "title": "Interview insights", "subtitle": "Feedback analysis"},
            {"icon": "📄", "title": "Resume analysis", "subtitle": "Skill extraction"},
        ]
        for action in actions:
            with st.container(border=True):
                c1, c2, c3 = st.columns([0.1, 0.8, 0.1])
                c1.write(action["icon"])
                c2.write(f"**{action['title']}**")
                c2.caption(action["subtitle"])

    with st.container(border=True):
        st.subheader("Recent Conversations")
        st.button("View All", key="view_all_conv")
        conversations = [
            {"title": "Top Python Developers", "time": "2 hours ago"},
            {"title": "Frontend Pipeline", "time": "5 hours ago"},
            {"title": "AI/ML Candidates", "time": "Yesterday"},
            {"title": "Interview Feedback", "time": "Yesterday"},
        ]
        for conv in conversations:
            with st.container(border=True):
                c1, c2, c3 = st.columns([0.1, 0.8, 0.1])
                c1.write("📄")
                c2.write(conv["title"])
                c3.caption(conv["time"])

    st.markdown('</div>', unsafe_allow_html=True)  # Close right column
    st.markdown('</div>', unsafe_allow_html=True)  # Close body
    st.markdown('</div>', unsafe_allow_html=True)  # Close page

    # Handle user input
    text_value = st.session_state.get("modern_chat_input", "").strip()
    send_clicked = st.session_state.get("ai_copilot_send_clicked", False)
    if text_value and (send_clicked or st.session_state.get("modern_chat_input_submitted", False)):
        # Add user message
        st.session_state["messages"].append({
            "role": "user",
            "content": text_value,
            "timestamp": datetime.now().strftime("%H:%M"),
        })

        # Generate mock AI response
        mock_response = _get_mock_ai_response(text_value)
        ai_msg = {
            "role": "assistant",
            "content": mock_response["content"],
            "timestamp": datetime.now().strftime("%H:%M"),
        }
        if mock_response["type"] == "table":
            ai_msg["rich_type"] = "table"
            ai_msg["table_data"] = mock_response["table"]
        elif mock_response["type"] == "bullets":
            ai_msg["rich_type"] = "bullets"
            ai_msg["bullets"] = mock_response["bullets"]

        st.session_state["messages"].append(ai_msg)
        st.session_state["modern_chat_input"] = ""
        st.session_state.modern_chat_input_submitted = False
        st.rerun()
