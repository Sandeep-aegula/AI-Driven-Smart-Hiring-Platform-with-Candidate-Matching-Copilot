""" services/assistant_service.py — HirePilot AI Assistant Service """
import json
import time
import uuid
from typing import Optional, List, Dict, Any
import streamlit as st
import httpx
from frontend.services.knowledge_service import KnowledgeService
from frontend.services.context_service import ContextService
from frontend.services.llm_service import llm_service
from frontend.utils.chat_utils import (
    generate_message_id,
    get_timestamp,
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
                    "Hello! I'm **HirePilot AI Assistant**. I can help you with:\n\n"
                    "- Understanding application features\n"
                    "- Navigating through modules\n"
                    "- Recruitment workflow guidance\n"
                    "- Answering project questions\n"
                    "- Providing contextual suggestions\n\n"
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
    current_page = ContextService.get_current_page()
    st.session_state.ai_assistant_current_page = current_page
    
    # Get page context
    page_context = ContextService.get_page_context(current_page)
    session_context = ContextService.get_session_context()
    
    # Search knowledge base for relevant information
    knowledge_snippets = KnowledgeService.search_knowledge_base(user_message)
    knowledge_context = "\n".join(knowledge_snippets) if knowledge_snippets else ""
    
    # Build system prompt
    system_prompt = f"""You are **HirePilot AI Assistant**, an intelligent recruitment copilot.

## Current Context
- Page: {current_page}
- Page Description: {page_context.get('description', '')}
- Available Actions: {', '.join(page_context.get('key_actions', []))}

## Session Context
- Selected Job: {session_context.get('selected_job_id', 'None')}
- Selected Candidate: {session_context.get('selected_candidate_id', 'None')}

## Knowledge Base
{knowledge_context if knowledge_context else "No specific knowledge base entries found for this query."}

## Response Guidelines
- Keep responses concise and scannable
- Use bullet points for lists
- Use numbered steps for procedures
- Use code blocks for technical content
- Never hallucinate features - if unsure, say so
- Provide step-by-step instructions for navigation and workflows
- Use emojis sparingly for visual clarity (📍, ✅, ❌, 💡, ⚠️)

## Recruitment Workflow
1. Create Job → 2. Generate JD → 3. Publish Job → 4. Receive Applications → 5. Upload Resume → 6. AI Screening → 7. Candidate Ranking → 8. Interview → 9. Feedback → 10. Offer Letter → 11. Employee Onboarding
"""
    
    return f"""{system_prompt}

User: {user_message}
Assistant: """


def send_message_to_backend(message: str) -> Optional[str]:
    """Send message to backend AI service using LLM service."""
    try:
        # Use LLM service which handles Ollama/Groq/OpenAI
        response = llm_service.chat(message, [])
        return response
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
