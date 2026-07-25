"""services/context_service.py - Context service for AI Assistant.

Service for managing page context and application state.
"""

from typing import Dict, Any, Optional
import streamlit as st


class ContextService:
    """Service class for managing page context and application state."""

    @staticmethod
    def get_current_page() -> str:
        """Get the current page name."""
        return get_current_page()

    @staticmethod
    def get_page_context(page_name: Optional[str] = None) -> Dict[str, Any]:
        """Get detailed context for a specific page."""
        if page_name:
            context = {"page": page_name, "module": page_name}
            if page_name == "Dashboard":
                context["actions"] = ["View metrics", "Check analytics", "See recent activity"]
            elif page_name == "Jobs":
                context["actions"] = ["Create job", "View jobs", "Generate JD"]
            elif page_name == "Candidates":
                context["actions"] = ["Search candidates", "Compare candidates", "View details"]
            elif page_name == "Resume Parser":
                context["actions"] = ["Upload resume", "Parse resume", "Create candidate"]
            elif page_name == "Interviews":
                context["actions"] = ["Schedule interview", "View interviews", "Add feedback"]
            elif page_name == "Analytics":
                context["actions"] = ["View reports", "Export data", "Check KPIs"]
            elif page_name == "Employees":
                context["actions"] = ["View employees", "Onboard employee", "Convert candidate"]
            return context
        return get_page_context()

    @staticmethod
    def get_session_context() -> Dict[str, Any]:
        """Get current session context."""
        try:
            return {
                "selected_job_id": st.session_state.get("selected_job_id"),
                "selected_candidate_id": st.session_state.get("selected_cand_id"),
                "selected_interview_id": st.session_state.get("selected_interview_id"),
                "selected_employee_id": st.session_state.get("selected_employee_id"),
                "search_query": st.session_state.get("search_query", ""),
            }
        except Exception:
            return {}


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
