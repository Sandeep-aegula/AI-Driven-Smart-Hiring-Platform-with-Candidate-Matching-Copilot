import os

# Fix 1: assistant_service.py - rewrite with clean content
assistant_service_content = '''""" services/assistant_service.py — HirePilot AI Assistant Service """
import json
import time
import uuid
from typing import Optional, List, Dict, Any
import streamlit as st
import httpx
from frontend.services.cache import inject_css_once
from frontend.prompts.system_prompt import get_system_prompt
from frontend.services.copilot_service import (
    _get_client as _get_copilot_client,
    CHAT_ENDPOINT,
)
from frontend.utils.chat_utils import (
    generate_message_id,
    get_timestamp,
    render_markdown,
    auto_scroll_to_bottom,
)

BACKEND_URL = "http://localhost:8000"
ASSISTANT_CHAT_ENDPOINT = f"{BACKEND_URL}/copilot/chat"
ASSISTANT_HISTORY_ENDPOINT = f"{BACKEND_URL}/copilot/session"


def init_assistant_state() -> None:
    """Initialize AI Assistant session state."""
    defaults = {
        "ai_assistant_open": False,
        "ai_assistant_messages": [
            {
                "id": generate_message_id(),
                "role": "assistant",
                "content": (
                    "Hello! I'm **HirePilot AI Assistant**. I can help you with:\\n\\n"
                    "- Understanding application features\\n"
                    "- Navigating through modules\\n"
                    "- Recruitment workflow guidance\\n"
                    "- Answering project questions\\n"
                    "- Providing contextual suggestions\\n\\n"
                    "How can I assist you today?"
                ),
                "timestamp": get_timestamp(),
                "action": None,
            }
        ],
        "ai_assistant_session_id": str(uuid.uuid4()),
        "ai_assistant_typing": False,
        "ai_assistant_minimized": False,
        "ai_assistant_current_page": "Dashboard",
        "ai_assistant_context": {},
        "ai_assistant_suggestions": [
            "How do I upload resumes?",
            "What can I do on this page?",
            "Explain the recruitment workflow",
            "Show me top candidates",
        ],
        "ai_assistant_uploaded_files": [],
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def get_assistant_messages() -> List[Dict[str, Any]]:
    """Get assistant chat messages."""
    return st.session_state.get("ai_assistant_messages", [])


def append_assistant_message(role: str, content: str, action: Optional[Dict] = None) -> None:
    """Append a message to assistant chat history."""
    messages = get_assistant_messages()
    messages.append(
        {
            "id": generate_message_id(),
            "role": role,
            "content": content,
            "timestamp": get_timestamp(),
            "action": action,
        }
    )
    st.session_state.ai_assistant_messages = messages


def clear_assistant_chat() -> None:
    """Clear assistant chat history."""
    st.session_state.ai_assistant_messages = [
        {
            "id": generate_message_id(),
            "role": "assistant",
            "content": "Hello! I'm **HirePilot AI Assistant**. How can I assist you today?",
            "timestamp": get_timestamp(),
            "action": None,
        }
    ]
    st.session_state.ai_assistant_session_id = str(int(time.time() * 1000))


def get_current_page_context() -> str:
    """Get the current page context for the assistant."""
    try:
        from frontend.services.app_state import AppState
        app_state = AppState()
        return app_state.get_current_page()
    except Exception:
        return st.session_state.get("ai_assistant_current_page", "Dashboard")


def build_context_prompt(user_message: str) -> str:
    """Build the full prompt with system context and user message."""
    current_page = get_current_page_context()
    st.session_state.ai_assistant_current_page = current_page
    # Update system context from backend
    try:
        import httpx
        resp = httpx.get(f"{BACKEND_URL}/copilot/context", timeout=5.0)
        if resp.status_code == 200:
            context_data = resp.json()
            st.session_state.ai_assistant_context = context_data
    except Exception:
        st.session_state.ai_assistant_context = {}
    system_context = json.dumps(st.session_state.ai_assistant_context) if st.session_state.ai_assistant_context else "No additional context available."
    system_prompt = get_system_prompt(current_page=current_page, system_context=system_context)
    return f"""{system_prompt} User: {user_message} Assistant: """


def send_message_to_backend(message: str) -> Optional[str]:
    """Send message to backend AI service."""
    session_id = st.session_state.get("ai_assistant_session_id", str(uuid.uuid4()))
    payload = {
        "message": message.strip(),
        "session_id": session_id,
    }
    try:
        client = _get_copilot_client()
        resp = client.post(ASSISTANT_CHAT_ENDPOINT, json=payload, timeout=120.0)
        if resp.status_code == 200:
            data = resp.json()
            return data.get("response", "")
    except Exception as e:
        st.error(f"Failed to get response: {e}")
    return None


def process_user_input(user_input: str) -> None:
    """Process user input and generate AI response."""
    if not user_input or not user_input.strip():
        return
    # Add user message
    append_assistant_message("user", user_input.strip())
    # Show typing indicator
    st.session_state.ai_assistant_typing = True
    st.rerun()


def generate_ai_response() -> None:
    """Generate AI response when typing indicator is shown."""
    if not st.session_state.get("ai_assistant_typing", False):
        return
    st.session_state.ai_assistant_typing = False
    messages = get_assistant_messages()
    if not messages or messages[-1]["role"] != "user":
        return
    last_user_message = messages[-1]["content"]
    # Build context prompt
    full_prompt = build_context_prompt(last_user_message)
    # Get response from backend
    with st.spinner("Thinking..."):
        response = send_message_to_backend(full_prompt)
    if response:
        append_assistant_message("assistant", response)
    else:
        append_assistant_message(
            "assistant",
            "I apologize, but I'm having trouble connecting to the AI service. Please try again.",
        )
    auto_scroll_to_bottom()
    st.rerun()


def get_suggestions() -> List[str]:
    """Get contextual suggestions for the current page."""
    current_page = get_current_page_context()
    page_suggestions = {
        "Dashboard": [
            "What are the current hiring metrics?",
            "How many open roles do we have?",
            "What is our hiring velocity?",
            "Show me recent activity",
        ],
        "Jobs": [
            "How do I create a new job?",
            "How to generate a job description?",
            "How to publish a job?",
            "How to close a job posting?",
        ],
        "Candidates": [
            "How do I search for candidates?",
            "How are candidates scored?",
            "How to compare candidates?",
            "How to filter by skills?",
        ],
        "Resume Parser": [
            "How do I upload resumes?",
            "What file formats are supported?",
            "How does resume parsing work?",
            "How to create candidates from resumes?",
        ],
        "Interviews": [
            "How do I schedule an interview?",
            "How to collect feedback?",
            "How to manage interview slots?",
        ],
        "Analytics": [
            "What reports are available?",
            "How to export data?",
            "What do the KPIs mean?",
        ],
        "Employees": [
            "How to onboard a new employee?",
            "How to convert candidate to employee?",
        ],
    }
    return page_suggestions.get(current_page, [
        "How can I help you?",
        "What would you like to know?",
        "Ask me anything about recruitment",
    ])


def toggle_assistant() -> None:
    """Toggle assistant open/closed."""
    st.session_state.ai_assistant_open = not st.session_state.get("ai_assistant_open", False)


def minimize_assistant() -> None:
    """Minimize assistant."""
    st.session_state.ai_assistant_minimized = True


def close_assistant() -> None:
    """Close assistant."""
    st.session_state.ai_assistant_open = False
    st.session_state.ai_assistant_minimized = False


def is_assistant_open() -> bool:
    """Check if assistant is open."""
    return st.session_state.get("ai_assistant_open", False)


def is_assistant_minimized() -> bool:
    """Check if assistant is minimized."""
    return st.session_state.get("ai_assistant_minimized", False)
'''

# Fix 2: ai_assistant.py - rewrite with clean content
ai_assistant_content = '''""" components/ai_assistant.py - HirePilot AI Assistant (Infosys Springboard Style) """
from frontend.components.ai_floating_button import render_floating_button
from frontend.components.ai_chat_window import render_ai_chat_window
from frontend.services.assistant_service import is_assistant_open, init_assistant_state


def render_ai_assistant() -> None:
    """Render the AI Assistant floating chat widget."""
    # Initialize assistant state if not already done
    init_assistant_state()

    # Render floating button if assistant is closed
    if not is_assistant_open():
        render_floating_button()
    else:
        # Render chat window
        render_ai_chat_window()
'''

# Fix 3: app.py - read, fix the indentation, and rewrite
app_path = r"c:\\Users\\Naveen\\Downloads\\Ai_Recruitment_Talent_copilot\\frontend\\app.py"
with open(app_path, "r", encoding="utf-8", errors="replace") as f:
    app_content = f.read()

# Fix: uncomment render_ai_assistant()
app_content = app_content.replace(
    "# render_ai_assistant()",
    "render_ai_assistant()"
)

# Write all fixed files
files = {
    r"c:\\Users\\Naveen\\Downloads\\Ai_Recruitment_Talent_copilot\\frontend\\services\\assistant_service.py": assistant_service_content,
    r"c:\\Users\\Naveen\\Downloads\\Ai_Recruitment_Talent_copilot\\frontend\\components\\ai_assistant.py": ai_assistant_content,
    r"c:\\Users\\Naveen\\Downloads\\Ai_Recruitment_Talent_copilot\\frontend\\app.py": app_content,
}

for filepath, content in files.items():
    with open(filepath, "w", encoding="utf-8", newline="\n") as f:
        f.write(content)
    print(f"Fixed: {filepath}")

print("All files fixed successfully!")
