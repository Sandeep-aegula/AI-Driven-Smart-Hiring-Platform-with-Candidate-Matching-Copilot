"""
Shared constants for HirePilot frontend.
This file contains constants that are shared between frontend and backend
to ensure consistency and avoid duplication.
"""

# Valid candidate statuses that can be shortlisted
# These are the candidate statuses that can be shortlisted
# Must match the backend's SHORTLISTABLE_CANDIDATE_STATUSES exactly
SHORTLISTABLE_CANDIDATE_STATUSES = [
    "New",
    "Applied",
    "Under Review",
    "submitted",
    "parsed",
    "under_review",
    "applied",
    "new",
]

# Application statuses that are considered "final" (cannot be shortlisted)
FINAL_CANDIDATE_STATUSES = [
    "Shortlisted",
    "Hired",
    "Rejected",
    "Interview Scheduled",
    "Interviewed",
]

# All possible candidate statuses
ALL_CANDIDATE_STATUSES = [
    "New",
    "Applied",
    "Under Review",
    "Shortlisted",
    "Interview Scheduled",
    "Interviewed",
    "Hired",
    "Rejected",
]

# Status display names for UI
CANDIDATE_STATUS_DISPLAY = {
    "New": "New",
    "Applied": "Applied",
    "Under Review": "Under Review",
    "Shortlisted": "Shortlisted",
    "Interview Scheduled": "Interview Scheduled",
    "Interviewed": "Interviewed",
    "Hired": "Hired",
    "Rejected": "Rejected",
}

# Status colors for UI
STATUS_COLORS = {
    "Applied": "#3B82F6",
    "Under Review": "#F59E0B",
    "Shortlisted": "#10B981",
    "Interview Scheduled": "#8B5CF6",
    "Interviewed": "#8B5CF6",
    "Hired": "#10B981",
    "Rejected": "#EF4444",
    "New": "#6B7280",
}

def is_shortlistable_candidate_status(status: str) -> bool:
    """Check if a candidate status is eligible for shortlisting."""
    return status in SHORTLISTABLE_CANDIDATE_STATUSES

def is_final_candidate_status(status: str) -> bool:
    """Check if a candidate status is final (cannot be shortlisted)."""
    return status in FINAL_CANDIDATE_STATUSES