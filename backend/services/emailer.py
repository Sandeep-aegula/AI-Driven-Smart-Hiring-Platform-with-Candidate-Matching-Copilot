from __future__ import annotations

import logging
import smtplib
import ssl
from email.message import EmailMessage
from typing import Any

from backend.core.config import settings

logger = logging.getLogger(__name__)

_DECISION_MESSAGES = {
    "Approved": (
        "Your application is moving forward",
        "We are pleased to let you know that your application has been approved. "
        "Our recruitment team will contact you with the next steps.",
    ),
    "Shortlisted": (
        "You have been shortlisted",
        "We are pleased to let you know that you have been shortlisted. "
        "Our recruitment team will contact you with the next steps.",
    ),
    "Rejected": (
        "Update on your application",
        "Thank you for the time you invested in the process. We have decided not "
        "to move forward with your application at this time. We wish you every success.",
    ),
}


def send_recruiter_decision_email(candidate: dict[str, Any], decision: str) -> bool:
    """Send a candidate notification for a final recruiter decision."""
    template = _DECISION_MESSAGES.get(decision)
    recipient = candidate.get("email", "").strip()
    if not template or not recipient:
        return False
    if not settings.smtp_host or not settings.smtp_from_email:
        logger.warning("Decision email was not sent: SMTP_HOST and SMTP_FROM_EMAIL are required.")
        return False

    subject, message = template
    email = EmailMessage()
    email["Subject"] = subject
    email["From"] = settings.smtp_from_email
    email["To"] = recipient
    email.set_content(f"Hello {candidate.get('name', 'Candidate')},\n\n{message}\n\nBest regards,\nRecruitment Team")

    try:
        with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=15) as server:
            if settings.smtp_use_tls:
                server.starttls(context=ssl.create_default_context())
            if settings.smtp_username:
                server.login(settings.smtp_username, settings.smtp_password)
            server.send_message(email)
        return True
    except (OSError, smtplib.SMTPException):
        logger.exception("Failed to send recruiter decision email to %s", recipient)
        return False
