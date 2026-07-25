"""AI Copilot page.

Single-file version — the SQLite session-history persistence that would
normally live in frontend/services/chat_store.py is inlined below (see
the "TEMP CHAT PERSISTENCE" section) so this whole feature is one file.
"""
import os
import sqlite3
import tempfile
import time
import uuid
from contextlib import contextmanager

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
from backend.services.resume_parser_service import extract_text_from_document


# Typewriter tuning — small enough to feel snappy, not a slog on long responses.
_TYPE_DELAY_SECONDS = 0.008
_CURSOR = "▌"
_RESUME_TAG = "📎 Uploaded resume:"


# ============================================================================
# TEMP CHAT PERSISTENCE
#
# Keeps the AI Copilot chat alive across Streamlit reruns / page refreshes
# by writing every message to a local SQLite file in the OS temp directory.
# Each browser session gets its own randomly-generated session_id (stored
# in st.session_state), so this is scoped to "that chat only" — no session
# can read another session's history, and nothing is meant to be permanent
# (it lives in tempfile.gettempdir(), same lifetime guarantee as any other
# temp file on the box).
#
# This section only ever talks to st.session_state / SQLite directly — it
# does not know about copilot_service's internal message list, so it sits
# alongside that service's existing behavior without changing it.
# ============================================================================

_DB_PATH = os.path.join(tempfile.gettempdir(), "ai_copilot_chat_sessions.db")


def _get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(_DB_PATH, check_same_thread=False)
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS chat_messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL,
            role TEXT NOT NULL,
            content TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_chat_session "
        "ON chat_messages (session_id, id)"
    )
    # Parsed resume text, one row per session, so the recruiter can keep
    # chatting about a resume even if copilot_service's own in-memory
    # state gets reset (rerun, server restart, etc).
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS resume_context (
            session_id TEXT PRIMARY KEY,
            file_name TEXT NOT NULL,
            file_text TEXT NOT NULL,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    return conn


@contextmanager
def _db_connection():
    conn = _get_conn()
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def _get_session_id() -> str:
    """Return this browser session's chat id, creating one if needed."""
    if "chat_session_id" not in st.session_state:
        st.session_state["chat_session_id"] = str(uuid.uuid4())
    return st.session_state["chat_session_id"]


def _load_persisted_messages(session_id: str) -> list[dict]:
    """Return all persisted messages for this session, oldest first."""
    with _db_connection() as conn:
        rows = conn.execute(
            "SELECT role, content FROM chat_messages "
            "WHERE session_id = ? ORDER BY id ASC",
            (session_id,),
        ).fetchall()
    return [{"role": role, "content": content} for role, content in rows]


def _save_persisted_message(session_id: str, role: str, content: str) -> None:
    """Append one message to this session's persisted history."""
    with _db_connection() as conn:
        conn.execute(
            "INSERT INTO chat_messages (session_id, role, content) "
            "VALUES (?, ?, ?)",
            (session_id, role, content),
        )


def _clear_persisted_session(session_id: str) -> None:
    """Wipe this session's persisted history (used by 'Clear Chat')."""
    with _db_connection() as conn:
        conn.execute(
            "DELETE FROM chat_messages WHERE session_id = ?", (session_id,)
        )


def _save_persisted_resume(session_id: str, file_name: str, file_text: str) -> None:
    """Store (or replace) this session's parsed resume text."""
    with _db_connection() as conn:
        conn.execute(
            "INSERT INTO resume_context (session_id, file_name, file_text, updated_at) "
            "VALUES (?, ?, ?, CURRENT_TIMESTAMP) "
            "ON CONFLICT(session_id) DO UPDATE SET "
            "file_name = excluded.file_name, "
            "file_text = excluded.file_text, "
            "updated_at = excluded.updated_at",
            (session_id, file_name, file_text),
        )


def _load_persisted_resume(session_id: str) -> dict | None:
    """Return {'file_name': ..., 'file_text': ...} for this session, or None."""
    with _db_connection() as conn:
        row = conn.execute(
            "SELECT file_name, file_text FROM resume_context WHERE session_id = ?",
            (session_id,),
        ).fetchone()
    if row is None:
        return None
    return {"file_name": row[0], "file_text": row[1]}


def _clear_persisted_resume(session_id: str) -> None:
    """Drop this session's persisted resume (used by 'Remove' / 'Clear Chat')."""
    with _db_connection() as conn:
        conn.execute(
            "DELETE FROM resume_context WHERE session_id = ?", (session_id,)
        )


def _append_and_persist(role: str, content: str) -> None:
    """Append to the live in-memory chat (existing copilot_service API)
    and mirror it into the temp DB so this session's history survives a
    refresh / rerun. Wraps append_message() rather than changing it."""
    append_message(role, content)
    _save_persisted_message(_get_session_id(), role, content)


def _restore_persisted_history(session_id: str) -> None:
    """On this session's first run, replay any previously saved messages
    back into the live chat via the existing append_message() API, so a
    page refresh doesn't lose the conversation."""
    if st.session_state.get("_history_restored"):
        return
    if not get_messages():
        for msg in _load_persisted_messages(session_id):
            append_message(msg["role"], msg["content"])
    st.session_state["_history_restored"] = True


# ============================================================================
# CHAT RENDERING / RESUME HANDLING
# ============================================================================


def _stream_response(placeholder, response: str) -> None:
    """Render `response` into `placeholder` with a typewriter effect."""
    displayed = ""
    for char in response:
        displayed += char
        placeholder.markdown(displayed + _CURSOR)
        time.sleep(_TYPE_DELAY_SECONDS)
    placeholder.markdown(displayed)


def _handle_resume_upload(uploaded_file) -> bool:
    """Extract text from an uploaded resume and wire it into the copilot's
    resume context. Returns True on success.

    This is the piece that was previously missing: attach_resume_context()
    pushes the parsed text into the copilot service so get_resume_context()
    (used both for auto-analysis and for injecting context into regular
    questions) actually has something to return. Without this call, the
    resume looked "Loaded" in the UI but the AI had nothing to read.
    """
    file_bytes = uploaded_file.read()
    file_text = extract_text_from_document(file_bytes, uploaded_file.name)
    if not file_text.strip():
        st.error(
            f"Could not extract text from '{uploaded_file.name}'. "
            "Please try a different file or format."
        )
        return False

    attach_resume_context(uploaded_file.name, file_text)
    st.session_state["resume_uploaded"] = True
    st.session_state["resume_name"] = uploaded_file.name
    st.session_state["resume_text"] = file_text
    return True


def _build_resume_prompt(resume_context: str, user_note: str) -> str:
    """Build the LLM prompt for a resume upload.

    If the user typed a question alongside the attachment (same composer
    submit, Claude-style), answer that question using the resume as
    context. Otherwise fall back to the default full structured report.
    """
    if user_note:
        return (
            "The user attached the resume below in the same message as "
            "the question that follows. Use the resume as context to "
            "answer the question.\n\n"
            f"Resume:\n{resume_context[:6000]}\n\n"
            f"User's question: {user_note}"
        )
    return (
        "Analyze this resume and provide a structured report with:\n"
        "1. Candidate Summary\n"
        "2. Professional Summary\n"
        "3. Key Skills\n"
        "4. Work Experience\n"
        "5. Education\n"
        "6. Notable Projects\n"
        "7. Strengths\n"
        "8. Weaknesses / Gaps\n"
        "9. ATS Score (1-10)\n"
        "10. Hiring Recommendation\n"
        "11. Suggested Interview Questions\n\n"
        f"Resume:\n{resume_context[:6000]}"
    )


def render_ai_copilot() -> None:
    """Render the AI Copilot chat page using native Streamlit layout."""

    _init_session_state()
    session_id = _get_session_id()
    _restore_persisted_history(session_id)
    is_thinking = st.session_state.get("is_thinking", False)

    # ---------- Header ----------
    st.title("AI Copilot")
    st.caption("Your intelligent recruitment assistant")

    # ---------- Main layout ----------
    left_col, right_col = st.columns([7, 3], gap="medium")

    with left_col:
        chat_container = st.container(height=600)
        with chat_container:
            for msg in get_messages():
                with st.chat_message(
                    msg["role"],
                    avatar="🤖" if msg["role"] == "assistant" else "👤",
                ):
                    st.markdown(msg["content"])

            # Insert thinking indicator as part of the chat flow (inside the message list)
            if is_thinking:
                # Create a placeholder assistant message that will be updated with streamed content
                with st.chat_message("assistant", avatar="🤖"):
                    with st.spinner("Thinking..."):
                        placeholder = messages = get_messages()
                    last_user_msg = next(
                        (
                            m["content"]
                            for m in reversed(messages)
                            if m["role"] == "user"
                        ),
                        "",
                        )
                    # Initialize response to empty to avoid UnboundLocalError
                    response = ""

                    if last_user_msg:
                        if last_user_msg.startswith(_RESUME_TAG):
                            resume_context = get_resume_context()
                            user_note = st.session_state.pop(
                                "_pending_resume_note", ""
                            )
                            if resume_context:
                                prompt = _build_resume_prompt(
                                    resume_context, user_note
                                )
                                response = send_message(prompt)
                                placeholder = st.empty()
                                _stream_response(placeholder, response)
                                _append_and_persist("assistant", response)
                        else:
                            full_message = last_user_msg
                            resume_context = get_resume_context()
                            if resume_context:
                                full_message = (
                                    f"{resume_context}\n\nUser: {last_user_msg}"
                                )
                            response = send_message(full_message)
                            placeholder = st.empty()
                            _stream_response(placeholder, response)
                            _append_and_persist("assistant", response)
                    set_thinking(False)
                    st.rerun()

        # Combined text + file composer — attach icon, text field, send
        # arrow only, all in one control (Claude-style: no separate
        # uploader widget). Attaching a file AND typing a question in the
        # same submit sends both together, in one turn.
        # NOTE: accept_file requires Streamlit >= 1.36. On older versions
        # this argument doesn't exist and would need a fallback uploader.
        composer = st.chat_input(
            "Ask anything about candidates, jobs, interviews...",
            key="copilot_chat_input",
            accept_file=True,
            file_type=["pdf", "docx", "txt", "csv"],
            disabled=is_thinking,
        )

        if composer:
            if composer.files:
                uploaded_file = composer.files[0]
                user_note = (composer.text or "").strip()
                if _handle_resume_upload(uploaded_file):
                    display_msg = f"{_RESUME_TAG} {uploaded_file.name}"
                    if user_note:
                        display_msg += f"\n\n{user_note}"
                    # Stash the free-text question (if any) so the response
                    # step below can answer it directly instead of always
                    # running the full structured analysis.
                    st.session_state["_pending_resume_note"] = user_note
                    _append_and_persist("user", display_msg)
                    set_thinking(True)
                    st.rerun()
            elif composer.text and composer.text.strip():
                _append_and_persist("user", composer.text)
                set_thinking(True)
                st.rerun()

        # Handle response after the user sends a message (or attaches a
        # resume — same "is_thinking" pipeline handles both).
        if is_thinking:
            with st.chat_message("assistant", avatar="🤖"):
                placeholder = st.empty()

                try:
                    messages = get_messages()

                    last_user_msg = next(
                        (
                            m["content"]
                            for m in reversed(messages)
                            if m["role"] == "user"
                        ),
                        "",
                    )

                    response = None

                    if last_user_msg.startswith(_RESUME_TAG):
                        resume_context = get_resume_context()
                        user_note = st.session_state.pop("_pending_resume_note", "")

                        if resume_context:
                            prompt = _build_resume_prompt(
                                resume_context,
                                user_note,
                            )

                            response = send_message(prompt)

                    else:
                        resume_context = get_resume_context()

                        full_message = last_user_msg

                        if resume_context:
                            full_message = (
                                f"{resume_context}\n\nUser: {last_user_msg}"
                            )

                        response = send_message(full_message)

                    if response:
                        _stream_response(placeholder, response)
                        _append_and_persist("assistant", response)
                    else:
                        placeholder.error("No response generated.")

                except Exception as e:
                    placeholder.error(f"AI Error: {e}")

                finally:
                    set_thinking(False)
                    st.rerun()

    with right_col:
        # Resume status card — attaching now happens via the chat composer;
        # this just shows what's attached and lets you clear it.
        with st.container(border=True):
            st.subheader("Resume")
            resume_uploaded = st.session_state.get("resume_uploaded", False)
            resume_name = st.session_state.get("resume_name", "")

            if resume_uploaded and resume_name:
                st.markdown(f"**{resume_name}**")
                st.caption("Ready for AI analysis")
                if st.button(
                    "Remove",
                    use_container_width=True,
                    key="remove_resume",
                    disabled=is_thinking,
                ):
                    for key in [
                        "resume_uploaded",
                        "resume_name",
                        "resume_text",
                        "resume_analysis",
                    ]:
                        st.session_state.pop(key, None)
                    clear_resume_context()
                    st.rerun()
            else:
                st.caption("Attach a resume using the 📎 icon in the chat box.")

        # Suggested Prompts card.
        with st.container(border=True):
            st.subheader("Suggested Prompts")
            for suggestion in get_suggestions():
                if st.button(
                    suggestion,
                    key=f"suggest_{hash(suggestion)}",
                    use_container_width=True,
                    disabled=is_thinking,
                ):
                    _append_and_persist("user", suggestion)
                    set_thinking(True)
                    st.rerun()

        # Clear Chat button.
        if st.button("Clear Chat", use_container_width=True, disabled=is_thinking):
            clear_chat()
            _clear_persisted_session(session_id)
            st.session_state["_history_restored"] = False
            st.rerun()