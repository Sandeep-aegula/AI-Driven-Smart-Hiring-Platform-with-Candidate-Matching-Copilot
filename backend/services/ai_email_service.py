import json
import logging
from backend.services.ai_candidate_service import _call_ollama

logger = logging.getLogger(__name__)

async def draft_candidate_email(candidate: dict, job_context: dict, email_type: str) -> dict:
    prompt = f"""You are an expert HR AI. Draft an email to a candidate.
Type of email: {email_type}

CANDIDATE: {candidate.get('name')}
JOB: {job_context.get('title')}

Respond EXACTLY in this JSON format:
{{
    "subject": "Email Subject",
    "body": "The full body of the email. Use professional tone. Address the candidate by name."
}}
"""
    return await _call_ollama(prompt, json_format=True)

async def draft_interview_email(candidate: dict, job_context: dict, interview_context: dict, email_mode: str) -> dict:
    prompt = f"""You are an expert HR AI. Draft an email to a candidate regarding their interview.
Mode: {email_mode}

CANDIDATE: {candidate.get('name')}
JOB: {job_context.get('title')}
INTERVIEW DETAILS:
- Date: {interview_context.get('date')}
- Time: {interview_context.get('time')} {interview_context.get('timezone', 'UTC')}
- Duration: {interview_context.get('duration')} mins
- Round: {interview_context.get('round')}
- Platform: {interview_context.get('meeting_platform')}
- Link: {interview_context.get('meeting_link')}
- Instructions: {interview_context.get('instructions')}
- Decision: {interview_context.get('decision')}

If Mode is 'Invitation', write an interview invitation email with the schedule details.
If Mode is 'Result', write an email based on the Decision (e.g. Selected, Rejected, Next Round).

Respond EXACTLY in this JSON format:
{{
    "subject": "Email Subject",
    "body": "The full body of the email. Use professional tone."
}}
"""
    res = await _call_ollama(prompt, json_format=True)
    if "error" in res:
        return {
            "subject": f"Interview {email_mode} - {job_context.get('title')}",
            "body": f"Dear {candidate.get('name')},\n\nRegarding your interview for {job_context.get('title')}: {email_mode}.\n\nPlease check your portal for more details."
        }
    return res


async def draft_communication_email(
    candidate: dict,
    job_context: dict,
    interview_context: dict | None,
    email_type: str,
    sender_name: str = "",
    reply_to_email: str = "",
) -> dict:
    round_label = interview_context.get("round") if interview_context else "N/A"
    match_score = candidate.get("match_score", 0)
    current_title = candidate.get("current_title") or candidate.get("summary", "Candidate")

    prompt = f"""You are an expert HR AI. Draft a professional email to a candidate.

Email type: {email_type}
Candidate: {candidate.get('name')}
Role: {job_context.get('title', 'Unknown role')}
Round: {round_label}
Current title: {current_title}
Match score: {match_score}%

Use a clear, engaging tone and keep the email concise. If reply-to email or sender name is provided, include them in the signature.

Respond EXACTLY in this JSON format:
{{
    "subject": "Email Subject",
    "body": "Full email body. Address the candidate by name."
}}
"""
    result = await _call_ollama(prompt, json_format=True)
    if "error" in result:
        body_prefix = f"Dear {candidate.get('name')},\n\n"
        if email_type == "Interview Invitation":
            body_suffix = f"We are excited to invite you to the next step for the {job_context.get('title')} role."
        elif email_type == "Offer Letter":
            body_suffix = f"We are pleased to offer you the {job_context.get('title')} position."
        elif email_type == "Rejection":
            body_suffix = "After careful consideration, we are unable to move forward with your application at this time."
        elif email_type == "Hold Notification":
            body_suffix = "We are still reviewing your application and will share an update soon."
        elif email_type == "Next Round Invitation":
            body_suffix = f"You have been selected for the next round for the {job_context.get('title')} role."
        else:
            body_suffix = f"This note is regarding your application for {job_context.get('title')}."

        body = f"{body_prefix}{body_suffix}\n\nBest regards,\n{sender_name or 'Recruitment Team'}"
        if reply_to_email:
            body += f"\nReply-To: {reply_to_email}"

        return {
            "subject": f"{email_type} - {job_context.get('title', '')}".strip(),
            "body": body,
        }
    return result
