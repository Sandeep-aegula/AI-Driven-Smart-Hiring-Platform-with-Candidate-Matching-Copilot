"""services/knowledge_service.py - Knowledge service for AI Assistant. Service for managing knowledge base and documentation. """
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


class KnowledgeService:
    """Service class for managing knowledge base and documentation."""

    @staticmethod
    def search_knowledge_base(query: str) -> List[str]:
        """Search the knowledge base for relevant information."""
        return search_knowledge(query)

    @staticmethod
    def get_knowledge_base() -> Dict[str, str]:
        """Get the full knowledge base."""
        return get_knowledge_base()