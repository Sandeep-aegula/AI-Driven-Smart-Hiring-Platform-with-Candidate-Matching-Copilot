""" services/copilot_service.py — HirePilot AI Copilot Frontend Service ====================================================== Handles communication with the FastAPI backend for the AI Copilot chat. Maintains session state, sends messages, and processes responses. """
import io
import json
import os
import sys
import time
from typing import Optional

import streamlit as st
import httpx

ROOT = os.path.normpath(
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..")
)
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

BACKEND_URL = os.getenv("HIREPILOT_BACKEND_URL", "http://localhost:8000")
CHAT_ENDPOINT = f"{BACKEND_URL}/copilot/chat"
HISTORY_ENDPOINT = f"{BACKEND_URL}/copilot/session"
SUGGESTIONS_ENDPOINT = f"{BACKEND_URL}/copilot/suggestions"

_client: Optional[httpx.Client] = None


def _get_client() -> httpx.Client:
    """Reuse a single synchronous HTTP client across reruns."""
    global _client
    if _client is None or _client.is_closed:
        _client = httpx.Client(timeout=120.0, follow_redirects=True)
    return _client


def close_client() -> None:
    """Close the shared HTTP client. Call on app shutdown if needed."""
    global _client
    if _client and not _client.is_closed:
        _client.close()
    _client = None


def _init_session_state() -> None:
    """Ensure copilot session state keys exist."""
    defaults = {
        "chat_messages": [
            {
                "role": "assistant",
                "content": (
                    "Hello! I'm **HirePilot AI**. I can help you with candidate search, "
                    "resume screening, interview preparation, hiring insights, and job analytics. "
                    "How can I assist you today?"
                ),
            }
        ],
        "copilot_session_id": "session_" + str(abs(hash(str(time.time())))),
        "is_thinking": False,
        "suggested_prompt": "",
        "uploaded_resume_context": None,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def get_session_id() -> str:
    return st.session_state.get("copilot_session_id", "default")


def get_messages() -> list[dict]:
    return st.session_state.get("chat_messages", [])


def append_message(role: str, content: str) -> None:
    messages = get_messages()
    messages.append({"role": role, "content": content})
    st.session_state.chat_messages = messages


def set_thinking(thinking: bool) -> None:
    st.session_state.is_thinking = thinking


def get_suggestions() -> list[str]:
    """Fetch suggested prompts from the backend."""
    try:
        client = _get_client()
        resp = client.get(SUGGESTIONS_ENDPOINT, timeout=5.0)
        if resp.status_code == 200:
            data = resp.json()
            return data.get("suggestions", [])
    except Exception:
        pass
    return [
        "Show top candidates for the Data Scientist role",
        "Write a rejection email for candidate ID 1",
        "Summarize the hiring pipeline status",
        "What is our current hiring velocity?",
        "Extract key skills from the latest uploaded resume",
        "Schedule interview feedback for tomorrow",
    ]


def send_message(message: str) -> str:
    """
    Send a user message to the backend and return the assistant's reply.

    Handles errors gracefully and returns user-friendly error messages.
    """
    if not message.strip():
        return ""

    session_id = get_session_id()
    payload = {
        "message": message.strip(),
        "session_id": session_id,
    }

    try:
        client = _get_client()
        resp = client.post(
            CHAT_ENDPOINT,
            json=payload,
            timeout=120.0,
        )
        if resp.status_code == 200:
            data = resp.json()
            return data.get("response", "I received an empty response.")
        if resp.status_code == 404:
            return "The chat endpoint was not found. Please check backend configuration."
        if resp.status_code == 500:
            return "The AI service encountered an error. Please try again."
        return f"Unexpected response from server (status {resp.status_code})."
    except httpx.ConnectError:
        return "Ollama server is not running. Please start Ollama and try again."
    except httpx.TimeoutException:
        return "The request timed out. The model may be loading — please try again."
    except httpx.HTTPStatusError as exc:
        if exc.response.status_code == 404:
            return "Model qwen2.5-coder:7b not found. Please pull the model first."
        return f"Server error: {exc.response.status_code}"
    except Exception as exc:
        st.error(f"Unexpected error: {exc}")
        return "Sorry, something went wrong. Please try again."


def build_resume_context(file_name: str, file_text: str) -> str:
    return f"[Uploaded Resume: {file_name}]\n\n{file_text[:4000]}"


def attach_resume_context(file_name: str, file_text: str) -> None:
    st.session_state.uploaded_resume_context = build_resume_context(file_name, file_text)


def get_resume_context() -> Optional[str]:
    return st.session_state.get("uploaded_resume_context")


def clear_resume_context() -> None:
    st.session_state.uploaded_resume_context = None


def clear_chat() -> None:
    st.session_state.chat_messages = [
        {"role": "assistant", "content": "Chat cleared. How can I help you?"}
    ]
    st.session_state.is_thinking = False
    clear_resume_context()
