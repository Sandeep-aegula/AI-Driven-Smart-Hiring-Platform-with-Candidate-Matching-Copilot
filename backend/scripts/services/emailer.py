from __future__ import annotations

import imaplib
import logging
import smtplib
import ssl
import time
from email.message import EmailMessage
from typing import Any

from backend.core.config import settings

logger = logging.getLogger(__name__)

SAFE_AUTH_FAILURE_MESSAGE = "Email service authentication failed. Check the configured SMTP credentials."
SAFE_SEND_FAILURE_MESSAGE = "Email service failed to send the message."
SAFE_CONFIGURATION_FAILURE_MESSAGE = "Email service configuration is incomplete. Check the SMTP settings."


def validate_smtp_configuration() -> list[str]:
    """Return missing or invalid SMTP settings without exposing secrets."""
    return settings.validate_smtp_configuration()


def _normalize_smtp_password() -> str:
    return settings.smtp_password.replace(" ", "") if settings.smtp_password else ""


def _failure_result(message: str, status_code: int, error_type: str) -> dict[str, Any]:
    return {
        "success": False,
        "status_code": status_code,
        "error_type": error_type,
        "error_message": message,
    }


def _success_result() -> dict[str, Any]:
    return {
        "success": True,
        "status_code": 200,
        "error_type": "",
        "error_message": "",
    }


def _send_via_smtp(email: EmailMessage, recipient: str) -> dict[str, Any]:
    issues = validate_smtp_configuration()
    if issues:
        logger.warning("Email was not sent because SMTP configuration is incomplete: %s", "; ".join(issues))
        return _failure_result(SAFE_CONFIGURATION_FAILURE_MESSAGE, 500, "configuration")

    smtp_password = _normalize_smtp_password()

    try:
        logger.info("Connecting to SMTP server for recipient %s", recipient)
        with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=30) as server:
            server.ehlo()
            if settings.smtp_use_tls:
                server.starttls(context=ssl.create_default_context())
                server.ehlo()

            server.login(settings.smtp_username, smtp_password)
            server.send_message(email)

        return _success_result()
    except smtplib.SMTPAuthenticationError:
        logger.error("SMTP authentication failed for recipient %s", recipient)
        return _failure_result(SAFE_AUTH_FAILURE_MESSAGE, 502, "authentication")
    except smtplib.SMTPException:
        logger.exception("SMTP error occurred while sending to %s", recipient)
        return _failure_result(SAFE_SEND_FAILURE_MESSAGE, 502, "smtp")
    except Exception:
        logger.exception("Unexpected error sending email to %s", recipient)
        return _failure_result(SAFE_SEND_FAILURE_MESSAGE, 500, "unexpected")

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


def _save_to_sent_folder(email: EmailMessage) -> bool:
    """Save the sent email to Gmail's Sent folder using IMAP APPEND."""
    try:
        # Connect to Gmail IMAP
        imap = imaplib.IMAP4_SSL("imap.gmail.com", 993)
        imap.login(settings.smtp_username, _normalize_smtp_password())
        
        # Select the Sent folder (Gmail uses [Gmail]/Sent Mail)
        imap.select('[Gmail]/Sent Mail')
        
        # Prepare the email for appending
        # Add Sent date header
        email["Date"] = time.strftime("%a, %d %b %Y %H:%M:%S %z")
        
        # Convert to bytes
        email_bytes = email.as_bytes()
        
        # Append to Sent folder
        imap.append('[Gmail]/Sent Mail', '', imaplib.Time2Internaldate(time.time()), email_bytes)
        
        imap.close()
        imap.logout()
        logger.info("Email saved to Sent folder successfully")
        return True
    except Exception as e:
        logger.warning(f"Failed to save email to Sent folder: {e}")
        return False


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

    result = _send_via_smtp(email, recipient)
    if result["success"]:
        # Save to Sent folder
        _save_to_sent_folder(email)
        return True
    return False


def send_custom_email(
    subject: str, 
    body: str, 
    recipient: str, 
    sender: str | None = None,
    attachment_filename: str | None = None,
    attachment_bytes: bytes | None = None
) -> dict[str, Any]:
    """Send a custom email and save to Sent folder, optionally with an attachment."""
    issues = validate_smtp_configuration()
    if issues:
        logger.warning("Custom email was not sent because SMTP configuration is incomplete: %s", "; ".join(issues))
        return _failure_result(SAFE_CONFIGURATION_FAILURE_MESSAGE, 500, "configuration")

    email = EmailMessage()
    email["Subject"] = subject
    email["From"] = sender or settings.smtp_from_email
    email["To"] = recipient
    email.set_content(body)

    if attachment_filename and attachment_bytes:
        import mimetypes
        mime_type, _ = mimetypes.guess_type(attachment_filename)
        mime_type = mime_type or 'application/octet-stream'
        maintype, subtype = mime_type.split('/', 1)
        email.add_attachment(
            attachment_bytes, 
            maintype=maintype, 
            subtype=subtype, 
            filename=attachment_filename
        )

    result = _send_via_smtp(email, recipient)
    if result["success"]:
        # Save to Sent folder
        _save_to_sent_folder(email)
    return result
