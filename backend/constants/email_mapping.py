from datetime import timedelta

STATUS_TO_EMAIL_TYPE = {
    "Shortlisted": "Interview Invitation",
    "Rejected": "Rejection",
    "Interview Scheduled": "Interview Invitation",
    "Hold": "Hold Notification",
    "Next Round": "Next Round Invitation",
    "Selected": "Offer Letter",
    "Hired": "Offer Letter",
}

DEFAULT_EMAIL_TYPE = "Candidate Update"

STATUS_EMAIL_DECISION_MAP = {
    "Shortlisted": "Interview Invitation",
    "Rejected": "Rejection",
    "Interview Scheduled": "Interview Invitation",
    "Hold": "Hold Notification",
    "Next Round": "Next Round Invitation",
    "Selected": "Offer Letter",
    "Hired": "Offer Letter",
}

PENDING_DECISIONS = set(STATUS_TO_EMAIL_TYPE.keys())

STATUS_TO_EMAIL_LABEL = {
    "Shortlisted": "Shortlisted",
    "Rejected": "Rejected",
    "Interview Scheduled": "Interview Scheduled",
    "Hold": "Hold",
    "Next Round": "Next Round",
    "Selected": "Selected",
    "Hired": "Hired",
}

EMAIL_TYPE_OPTIONS = [
    "Interview Invitation",
    "Selection",
    "Rejection",
    "Hold Notification",
    "Next Round Invitation",
    "Offer Letter",
]

DEFAULT_PENDING_DAYS_THRESHOLD = timedelta(days=0)
