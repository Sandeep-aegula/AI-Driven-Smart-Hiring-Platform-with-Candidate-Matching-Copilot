import streamlit as st
from frontend.components.file_uploader import file_uploader_simple

def _render_candidate_table():
    """Render mock candidate recommendation table."""
    import pandas as pd
    data = {
        "Candidate": ["Alice Johnson", "Bob Smith", "Carol Davis"],
        "Match Score": ["95%", "88%", "82%"],
        "Experience": ["5 yrs", "4 yrs", "6 yrs"],
        "Skills": ["Python, ML, NLP", "React, TS, Node", "Java, Spring, SQL"]
    }
    df = pd.DataFrame(data)
    st.dataframe(df, width="stretch", hide_index=True)

def _render_quick_actions():
    """Render quick action cards in right column."""
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

def _render_recent_conversations():
    """Render recent conversations list."""
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

def render_ai_copilot():
    # Initialize session state with mock data
    if 'messages' not in st.session_state:
        st.session_state.messages = [
            {
                "role": "assistant",
                "content": "Hello HR Manager! I'm your AI Copilot. I can help you with candidate search, resume screening, interview preparation, hiring insights, and job analytics."
            }
        ]

    # Minimal custom CSS for layout and styling
    st.markdown("""
    <style>
    .ai-copilot-layout {
        display: flex;
        gap: 24px;
        height: calc(100vh - 180px);
        min-height: 600px;
    }
    .ai-copilot-left {
        flex: 72;
        display: flex;
        flex-direction: column;
        background: #fff;
        border: 1px solid #E5E7EB;
        border-radius: 16px;
        padding: 24px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
    }
    .ai-copilot-right {
        flex: 28;
        display: flex;
        flex-direction: column;
        gap: 24px;
    }
    .ai-copilot-conversation {
        flex: 1;
        overflow-y: auto;
        padding-right: 8px;
    }
    .ai-copilot-input-wrapper {
        flex-shrink: 0;
        padding-top: 16px;
        border-top: 1px solid #E5E7EB;
        background: #fff;
    }
    .user-bubble {
        background: #E0E7FF !important;
        border-radius: 16px !important;
        padding: 12px 16px !important;
        margin-left: 20% !important;
    }
    .assistant-bubble {
        background: #fff !important;
        border: 1px solid #E5E7EB !important;
        border-radius: 16px !important;
        padding: 16px !important;
        margin-right: 20% !important;
    }
    .stChatInput [data-testid="stChatInputSubmitButton"] {
        background-color: #6366F1 !important;
        color: white !important;
    }
    </style>
    """, unsafe_allow_html=True)

    # Main two-column layout
    left_col, right_col = st.columns([0.72, 0.28], gap="medium")

    with left_col:
        st.markdown('<div class="ai-copilot-left">', unsafe_allow_html=True)
        st.title("AI Copilot")
        st.caption("Your intelligent recruitment assistant")

        # Conversation area (scrollable)
        st.markdown('<div class="ai-copilot-conversation">', unsafe_allow_html=True)
        for msg in st.session_state.messages:
            with st.chat_message(msg["role"], avatar="🤖" if msg["role"] == "assistant" else "👤"):
                st.markdown(msg["content"])
                if msg["role"] == "assistant" and msg.get("show_table"):
                    _render_candidate_table()
                if msg["role"] == "assistant":
                    c1, c2, c3 = st.columns(3)
                    c1.button("📋 Copy", key=f"copy_{id(msg)}")
                    c2.button("👍 Like", key=f"like_{id(msg)}")
                    c3.button("👎 Dislike", key=f"dislike_{id(msg)}")
        st.markdown('</div>', unsafe_allow_html=True)

        # Chat input area (sticky at bottom of left column)
        st.markdown('<div class="ai-copilot-input-wrapper">', unsafe_allow_html=True)
        col_attach, col_input = st.columns([0.08, 0.92])
        with col_attach:
            file_uploader_simple(
                label="Drag and drop file here",
                accepted_types=["pdf", "docx", "doc", "txt", "xlsx", "csv"],
                max_size_mb=200,
                key="ai_copilot_upload"
            )
        user_input = col_input.chat_input("Ask anything about candidates, jobs, interviews...", key="ai_copilot_input")
        st.markdown('</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    with right_col:
        st.markdown('<div class="ai-copilot-right">', unsafe_allow_html=True)
        with st.container(border=True):
            st.subheader("What can I help you with?")
            _render_quick_actions()

        with st.container(border=True):
            st.subheader("Recent Conversations")
            st.button("View All", key="view_all_conv")
            _render_recent_conversations()
        st.markdown('</div>', unsafe_allow_html=True)

    # Handle user input
    if user_input:
        st.session_state.messages.append({"role": "user", "content": user_input})
        # Mock assistant response with table
        st.session_state.messages.append({
            "role": "assistant",
            "content": "Here are the top candidates matching your criteria:",
            "show_table": True
        })
        st.rerun()
