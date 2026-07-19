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
        imap.login(settings.smtp_username, settings.smtp_password)
        
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

    # Clean the password (remove spaces if any)
    smtp_password = settings.smtp_password.replace(" ", "") if settings.smtp_password else ""
    
    logger.info(f"Attempting to send decision email via SMTP")
    logger.info(f"SMTP Host: {settings.smtp_host}")
    logger.info(f"SMTP Port: {settings.smtp_port}")
    logger.info(f"SMTP Username: {settings.smtp_username}")
    logger.info(f"SMTP From: {settings.smtp_from_email}")
    logger.info(f"SMTP To: {recipient}")
    logger.info(f"SMTP Use TLS: {settings.smtp_use_tls}")
    logger.info(f"Subject: {subject}")

    try:
        logger.info("Connecting to SMTP server...")
        with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=30) as server:
            server.set_debuglevel(1)  # Enable SMTP debug output
            
            if settings.smtp_use_tls:
                logger.info("Starting TLS...")
                server.starttls(context=ssl.create_default_context())
            
            logger.info("Attempting SMTP login...")
            server.login(settings.smtp_username, smtp_password)
            logger.info("SMTP login successful!")
            
            logger.info("Sending email...")
            server.send_message(email)
            logger.info("Email sent successfully via SMTP!")
        
        # Save to Sent folder
        logger.info("Attempting to save to Sent folder...")
        _save_to_sent_folder(email)
        logger.info("Email processing completed successfully")
        return True
    except smtplib.SMTPAuthenticationError as e:
        logger.error(f"SMTP Authentication failed: {e}")
        logger.error(f"Error code: {e.smtp_code}, Error message: {e.smtp_error}")
        return False
    except smtplib.SMTPConnectError as e:
        logger.error(f"SMTP Connection failed: {e}")
        return False
    except smtplib.SMTPException as e:
        logger.error(f"SMTP error occurred: {e}")
        return False
    except Exception as e:
        logger.exception(f"Unexpected error sending decision email to {recipient}: {e}")
        return False


def send_custom_email(subject: str, body: str, recipient: str, sender: str | None = None) -> bool:
    """Send a custom email and save to Sent folder."""
    if not settings.smtp_host or not settings.smtp_from_email:
        logger.warning("Custom email was not sent: SMTP_HOST and SMTP_FROM_EMAIL are required.")
        return False

    # Clean the password (remove spaces if any)
    smtp_password = settings.smtp_password.replace(" ", "") if settings.smtp_password else ""
    
    logger.info(f"Attempting to send email via SMTP")
    logger.info(f"SMTP Host: {settings.smtp_host}")
    logger.info(f"SMTP Port: {settings.smtp_port}")
    logger.info(f"SMTP Username: {settings.smtp_username}")
    logger.info(f"SMTP From: {sender or settings.smtp_from_email}")
    logger.info(f"SMTP To: {recipient}")
    logger.info(f"SMTP Use TLS: {settings.smtp_use_tls}")
    logger.info(f"Subject: {subject}")

    email = EmailMessage()
    email["Subject"] = subject
    email["From"] = sender or settings.smtp_from_email
    email["To"] = recipient
    email.set_content(body)

    try:
        logger.info("Connecting to SMTP server...")
        with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=30) as server:
            server.set_debuglevel(1)  # Enable SMTP debug output
            
            if settings.smtp_use_tls:
                logger.info("Starting TLS...")
                server.starttls(context=ssl.create_default_context())
            
            logger.info("Attempting SMTP login...")
            server.login(settings.smtp_username, smtp_password)
            logger.info("SMTP login successful!")
            
            logger.info("Sending email...")
            server.send_message(email)
            logger.info("Email sent successfully via SMTP!")
        
        # Save to Sent folder
        logger.info("Attempting to save to Sent folder...")
        _save_to_sent_folder(email)
        logger.info("Email processing completed successfully")
        return True
    except smtplib.SMTPAuthenticationError as e:
        logger.error(f"SMTP Authentication failed: {e}")
        logger.error(f"Error code: {e.smtp_code}, Error message: {e.smtp_error}")
        return False
    except smtplib.SMTPConnectError as e:
        logger.error(f"SMTP Connection failed: {e}")
        return False
    except smtplib.SMTPException as e:
        logger.error(f"SMTP error occurred: {e}")
        return False
    except Exception as e:
        logger.exception(f"Unexpected error sending email to {recipient}: {e}")
        return False
