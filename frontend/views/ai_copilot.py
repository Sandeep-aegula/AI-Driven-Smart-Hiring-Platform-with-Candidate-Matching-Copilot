import os
import time

import streamlit as st

from frontend.services.copilot_service import (
    _init_session_state,
    append_message,
    attach_resume_context,
    clear_chat,
    clear_resume_context,
    get_messages,
    get_resume_context,
    get_suggestions,
    send_message,
    set_thinking,
)


def render_ai_copilot() -> None:
    """Render the AI Copilot chat page using native Streamlit layout.

    Layout matches other pages:
    - Title + caption
    - Two columns: conversation (left) and tools (right)
    - Conversation scrolls independently
    - Chat input stays fixed below conversation
    """
    _init_session_state()

    # ---------- Header ----------
    st.title("AI Copilot")
    st.caption("Your intelligent recruitment assistant")

    # ---------- Main layout ----------
    left_col, right_col = st.columns([7, 3], gap="medium")

    with left_col:
        # Scrollable conversation area.
        chat_container = st.container(height=600)
        with chat_container:
            messages = get_messages()
            for msg in messages:
                with st.chat_message(
                    msg["role"],
                    avatar="🤖" if msg["role"] == "assistant" else "👤",
                ):
                    st.markdown(msg["content"])

            # Thinking indicator rendered as the last assistant message.
            if st.session_state.get("is_thinking", False):
                with st.chat_message("assistant", avatar="🤖"):
                    with st.spinner("Thinking..."):
                        st.empty()

        # Streamlit's native chat input stays fixed below the conversation.
        if prompt := st.chat_input(
            "Ask anything about candidates, jobs, interviews...",
            key="copilot_chat_input",
        ):
            append_message("user", prompt)
            set_thinking(True)
            st.rerun()

        # Handle streaming response after the user sends a message.
        if st.session_state.get("is_thinking", False):
            with st.chat_message("assistant", avatar="🤖"):
                with st.spinner("Thinking..."):
                    messages = get_messages()
                    last_user_msg = next(
                        (
                            m["content"]
                            for m in reversed(messages)
                            if m["role"] == "user"
                        ),
                        "",
                    )
                    if last_user_msg:
                        full_message = last_user_msg
                        resume_context = get_resume_context()
                        if resume_context:
                            full_message = (
                                f"{resume_context}\n\nUser: {last_user_msg}"
                            )

                        response = send_message(full_message)

                        if resume_context:
                            clear_resume_context()

                        # Progressive streaming display.
                        placeholder = st.empty()
                        displayed = ""
                        for char in response:
                            displayed += char
                            placeholder.markdown(displayed)

                        append_message("assistant", response)
                        set_thinking(False)
                        st.rerun()

    with right_col:
        # Upload Resume card.
        with st.container(border=True):
            st.subheader("Upload Resume")
            uploaded_file = st.file_uploader(
                "Choose a file",
                type=["pdf", "docx", "txt", "csv"],
                label_visibility="collapsed",
            )
            if uploaded_file is not None:
                file_text = str(
                    uploaded_file.read(), "utf-8", errors="replace"
                )
                attach_resume_context(uploaded_file.name, file_text)
                st.success(f"Uploaded: {uploaded_file.name}")
                st.caption(
                    "You can now ask me to summarize, extract skills, or evaluate this resume."
                )

        # Suggested Prompts card.
        with st.container(border=True):
            st.subheader("Suggested Prompts")
            suggestions = get_suggestions()
            for suggestion in suggestions:
                if st.button(
                    suggestion,
                    key=f"suggest_{hash(suggestion)}",
                    use_container_width=True,
                ):
                    append_message("user", suggestion)
                    set_thinking(True)
                    st.rerun()

        # Clear Chat button.
        if st.button("Clear Chat", use_container_width=True):
            clear_chat()
            st.rerun()
