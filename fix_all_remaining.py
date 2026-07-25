import os

BASE = r"c:\Users\Naveen\Downloads\Ai_Recruitment_Talent_copilot"

files = {}

# prompts/system_prompt.py
files[r"frontend\prompts\system_prompt.py"] = '''"""prompts/system_prompt.py - HirePilot AI Copilot System Prompts.

Contains system prompts and prompt templates for the AI Assistant.
"""


def get_system_prompt(current_page: str = "Dashboard", system_context: str = "") -> str:
    """Get the system prompt for the AI Assistant."""
    return f"""You are HirePilot AI, an intelligent recruitment assistant for the HirePilot AI Recruitment and Talent Management Copilot application.

You are helpful, professional, and knowledgeable about recruitment, HR, and this specific application.

Current page context: {current_page}

System context: {system_context}

Your capabilities include:
1. Answering questions about the application's features and how to use them
2. Guiding users through recruitment workflows
3. Explaining modules: Dashboard, Jobs, Candidates, Resume Parser, Interviews, Analytics, Reports, Employees
4. Providing navigation assistance
5. Explaining the recruitment workflow end-to-end
6. Answering project-related questions
7. Giving contextual suggestions based on the current page
8. Helping with candidate search, screening, and evaluation
9. Assisting with job description creation
10. Helping with interview scheduling and feedback

Guidelines:
- Be concise and professional
- Use markdown formatting for better readability
- Provide step-by-step instructions when appropriate
- If you don't know something, clearly state that
- Never make up features or information
- Always be helpful and friendly
- Focus on the current page context when answering
"""


def get_welcome_message() -> str:
    """Get the welcome message for new conversations."""
    return """Hello! I'm **HirePilot AI Assistant**. I can help you with:

- Understanding application features
- Navigating through modules
- Recruitment workflow guidance
- Answering project questions
- Providing contextual suggestions

How can I assist you today?"""
'''

# utils/chat_utils.py
files[r"frontend\utils\chat_utils.py"] = '''"""utils/chat_utils.py - Chat utility functions.

Utility functions for the AI Assistant chat.
"""

import time
import uuid
from typing import Optional


def generate_message_id() -> str:
    """Generate a unique message ID."""
    return f"msg_{int(time.time() * 1000)}_{uuid.uuid4().hex[:8]}"


def get_timestamp() -> str:
    """Get current timestamp as string."""
    return time.strftime("%I:%M %p")


def render_markdown(text: str) -> str:
    """Render markdown text (placeholder for Streamlit's markdown)."""
    return text


def auto_scroll_to_bottom() -> None:
    """Auto-scroll chat to bottom (handled by Streamlit)."""
    pass
'''

# utils/copy_utils.py
files[r"frontend\utils\copy_utils.py"] = '''"""utils/copy_utils.py - Copy utility functions.

Utility functions for copying content.
"""

import streamlit as st


def copy_button(content: str, button_id: str) -> None:
    """Render a copy button for content."""
    if st.button("📋", key=f"copy_{button_id}", help="Copy to clipboard"):
        st.code(content, language=None)
        st.success("Copied!")
'''

# utils/markdown_utils.py
files[r"frontend\utils\markdown_utils.py"] = '''"""utils/markdown_utils.py - Markdown utility functions.

Utility functions for markdown rendering.
"""

import re


def render_markdown(text: str) -> str:
    """Render markdown text with basic formatting."""
    # Escape HTML
    text = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

    # Bold
    text = re.sub(r"\\*\\*(.+?)\\*\\*", r"<strong>\\1</strong>", text)

    # Italic
    text = re.sub(r"\\*(.+?)\\*", r"<em>\\1</em>", text)

    # Code blocks
    text = re.sub(r"```(.*?)```", r"<pre><code>\\1</code></pre>", text, flags=re.DOTALL)

    # Inline code
    text = re.sub(r"`(.+?)`", r"<code>\\1</code>", text)

    # Line breaks
    text = text.replace("\\n", "<br>")

    return text
'''

# services/context_service.py
files[r"frontend\services\context_service.py"] = '''"""services/context_service.py - Context service for AI Assistant.

Service for managing page context and application state.
"""

import streamlit as st


def get_current_page() -> str:
    """Get the current page name."""
    try:
        return st.session_state.get("current_page", "Dashboard")
    except Exception:
        return "Dashboard"


def get_page_context() -> dict:
    """Get detailed context for the current page."""
    current_page = get_current_page()

    context = {
        "page": current_page,
        "module": current_page,
    }

    # Add page-specific context
    if current_page == "Dashboard":
        context["actions"] = ["View metrics", "Check analytics", "See recent activity"]
    elif current_page == "Jobs":
        context["actions"] = ["Create job", "View jobs", "Generate JD"]
    elif current_page == "Candidates":
        context["actions"] = ["Search candidates", "Compare candidates", "View details"]
    elif current_page == "Resume Parser":
        context["actions"] = ["Upload resume", "Parse resume", "Create candidate"]
    elif current_page == "Interviews":
        context["actions"] = ["Schedule interview", "View interviews", "Add feedback"]
    elif current_page == "Analytics":
        context["actions"] = ["View reports", "Export data", "Check KPIs"]
    elif current_page == "Employees":
        context["actions"] = ["View employees", "Onboard employee", "Convert candidate"]

    return context
'''

# services/knowledge_service.py
files[r"frontend\services\knowledge_service.py"] = '''"""services/knowledge_service.py - Knowledge service for AI Assistant.

Service for managing knowledge base and documentation.
"""

from typing import Dict, List


def get_knowledge_base() -> Dict[str, str]:
    """Get the knowledge base for the AI Assistant."""
    return {
        "project_name": "HirePilot AI Recruitment and Talent Management Copilot",
        "project_description": "An AI-powered recruitment and talent management platform",
        "modules": [
            "Dashboard",
            "Jobs",
            "Candidates",
            "Resume Parser",
            "Interviews",
            "Analytics",
            "Reports",
            "Employees",
            "Settings",
        ],
        "workflow": [
            "Create Job",
            "Generate JD",
            "Publish Job",
            "Receive Applications",
            "Upload Resume",
            "AI Screening",
            "Candidate Ranking",
            "Interview Scheduling",
            "Interview Feedback",
            "Offer Letter",
            "Employee Onboarding",
        ],
    }


def search_knowledge(query: str) -> List[str]:
    """Search the knowledge base for relevant information."""
    kb = get_knowledge_base()
    results = []

    query_lower = query.lower()
    for key, value in kb.items():
        if isinstance(value, str):
            if query_lower in value.lower():
                results.append(f"{key}: {value}")
        elif isinstance(value, list):
            for item in value:
                if query_lower in str(item).lower():
                    results.append(f"{key}: {item}")

    return results
'''

# services/llm_service.py
files[r"frontend\services\llm_service.py"] = '''"""services/llm_service.py - LLM service for AI Assistant.

Service for communicating with LLM providers.
"""

from typing import Optional
import httpx


def send_message_to_llm(message: str, session_id: str) -> Optional[str]:
    """Send message to LLM and get response."""
    try:
        # Use the existing copilot service endpoint
        backend_url = "http://localhost:8000"
        response = httpx.post(
            f"{backend_url}/copilot/chat",
            json={"message": message, "session_id": session_id},
            timeout=120.0,
        )
        if response.status_code == 200:
            data = response.json()
            return data.get("response", "")
    except Exception as e:
        print(f"LLM error: {e}")
        return None

    return None
'''

# services/memory_service.py
files[r"frontend\services\memory_service.py"] = '''"""services/memory_service.py - Memory service for AI Assistant.

Service for managing conversation memory.
"""

from typing import List, Dict, Any


def get_conversation_history(session_id: str) -> List[Dict[str, Any]]:
    """Get conversation history for a session."""
    # Placeholder - would typically fetch from database or session state
    return []


def save_message(session_id: str, role: str, content: str) -> None:
    """Save a message to conversation history."""
    # Placeholder - would typically save to database or session state
    pass


def clear_conversation(session_id: str) -> None:
    """Clear conversation history for a session."""
    # Placeholder - would typically clear from database or session state
    pass
'''

# services/__init__.py
files[r"frontend\services\__init__.py"] = '''"""Services package for HirePilot AI."""

__all__ = [
    "assistant_service",
    "cache",
    "copilot_service",
    "context_service",
    "knowledge_service",
    "llm_service",
    "memory_service",
]
'''

# Write all files
for rel_path, content in files.items():
    filepath = os.path.join(BASE, rel_path)
    with open(filepath, "w", encoding="utf-8", newline="\n") as f:
        f.write(content)
    print(f"Written: {rel_path} ({len(content)} chars)")

print("\nDone!")
