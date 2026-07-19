from __future__ import annotations

import asyncio
import logging
from datetime import datetime
from typing import Any

from fastapi import APIRouter, HTTPException

from backend.constants.email_mapping import STATUS_TO_EMAIL_TYPE, EMAIL_TYPE_OPTIONS, PENDING_DECISIONS
from backend.core.config import settings
from backend.database.data_store import data_store
from backend.schemas.entities import (
    CommunicationDraftRequest,
    CommunicationSendRequest,
    EmailRecord,
)
from backend.services.ai_email_service import draft_communication_email
from backend.services.emailer import send_custom_email

logger = logging.getLogger(__name__)
router = APIRouter()

_pending_queue_cache: dict[str, Any] = {
    "timestamp": None,
    "queue": []
}
_pending_cache_lock = asyncio.Lock()
_cache_ttl_seconds = 15


def clear_pending_cache() -> None:
    _pending_queue_cache["timestamp"] = None
    _pending_queue_cache["queue"] = []


def _has_sent_email_for_decision(candidate: dict, decision: str, interview_id: int | None = None) -> bool:
    email_history = candidate.get("email_history", [])
    sent_for_decision = [email for email in email_history if email.get("status") == "Sent"]
    for email in sent_for_decision:
        if email.get("decision") == decision:
            if interview_id is None or email.get("interview_id") == interview_id:
                return True
    return False


def _has_draft_for_decision(candidate: dict, decision: str, interview_id: int | None = None) -> bool:
    email_history = candidate.get("email_history", [])
    drafts = [email for email in email_history if email.get("status") == "Draft"]
    for email in drafts:
        if email.get("decision") == decision:
            if interview_id is None or email.get("interview_id") == interview_id:
                return True
    return False


def _build_pending_entry(candidate: dict, interview: dict | None = None) -> dict:
    decision = candidate.get("status")
    implied_email_type = STATUS_TO_EMAIL_TYPE.get(decision)
    if not implied_email_type:
        return {}

    job_title = "Unknown Role"
    job_id = None
    if candidate.get("applications"):
        application = candidate["applications"][0]
        job_id = application.get("job_id")
    if job_id:
        job = data_store._jobs_by_id.get(job_id)
        if job:
            job_title = job.get("title", job_title)

    round_name = ""
    if interview is not None:
        round_name = interview.get("round", "")
    elif candidate.get("status") == "Interview Scheduled":
        interviews = [iv for iv in data_store._interviews_by_id.values() if iv.get("candidate_id") == candidate.get("id")]
        if interviews:
            latest = sorted(interviews, key=lambda iv: iv.get("updated_at", ""), reverse=True)[0]
            round_name = latest.get("round", "")

    reference_time = candidate.get("updated_at") or candidate.get("created_at") or datetime.utcnow().isoformat()
    try:
        pending_dt = datetime.fromisoformat(reference_time)
    except Exception:
        pending_dt = datetime.utcnow()
    days_pending = (datetime.utcnow() - pending_dt).days

    return {
        "candidate_id": candidate.get("id"),
        "candidate_name": candidate.get("name"),
        "candidate_email": candidate.get("email"),
        "job_title": job_title,
        "round": round_name,
        "decision": decision,
        "implied_email_type": implied_email_type,
        "days_pending": days_pending,
        "draft_saved": _has_draft_for_decision(candidate, decision),
        "interview_id": interview.get("id") if interview else None,
    }


async def _compute_pending_queue() -> list[dict]:
    candidates = list(data_store._candidates_by_id.values())
    interviews = list(data_store._interviews_by_id.values())
    interviews_by_candidate: dict[int, list[dict]] = {}
    for iv in interviews:
        candidate_id = iv.get("candidate_id")
        if candidate_id is not None:
            interviews_by_candidate.setdefault(candidate_id, []).append(iv)

    pending: list[dict] = []
    for candidate in candidates:
        decision = candidate.get("status")
        if decision not in PENDING_DECISIONS:
            continue

        related_interviews = interviews_by_candidate.get(candidate.get("id"), [])
        interview_context = None
        if related_interviews:
            interview_context = sorted(related_interviews, key=lambda iv: iv.get("updated_at", ""), reverse=True)[0]

        if _has_sent_email_for_decision(candidate, decision, interview_context.get("id") if interview_context else None):
            continue

        pending.append(_build_pending_entry(candidate, interview_context))

    pending.sort(key=lambda item: item.get("days_pending", 0), reverse=True)
    return pending


@router.get("/pending")
async def get_pending_communications() -> list[dict]:
    async with _pending_cache_lock:
        now_ts = datetime.utcnow().timestamp()
        if _pending_queue_cache["timestamp"] and now_ts - _pending_queue_cache["timestamp"] < _cache_ttl_seconds:
            return _pending_queue_cache["queue"]
        queue = await _compute_pending_queue()
        _pending_queue_cache["queue"] = queue
        _pending_queue_cache["timestamp"] = now_ts
        return queue


@router.get("/history")
async def get_communications_history(
    page: int = 1,
    page_size: int = 25,
    email_type: str | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
    candidate_name: str | None = None,
    recruiter_name: str | None = None,
    status: str | None = None,
) -> dict[str, Any]:
    if page < 1:
        page = 1
    if page_size < 1:
        page_size = 25

    def _matches_filters(email: dict, cand: dict) -> bool:
        if email_type and email.get("email_type") != email_type:
            return False
        if status and email.get("status") != status:
            return False
        if candidate_name and candidate_name.lower() not in cand.get("name", "").lower():
            return False
        if recruiter_name and recruiter_name.lower() not in (email.get("sender_name", "") or "").lower():
            return False
        if start_date:
            try:
                cutoff = datetime.fromisoformat(start_date)
                if datetime.fromisoformat(email.get("sent_at")) < cutoff:
                    return False
            except Exception:
                pass
        if end_date:
            try:
                cutoff = datetime.fromisoformat(end_date)
                if datetime.fromisoformat(email.get("sent_at")) > cutoff:
                    return False
            except Exception:
                pass
        return True

    offset = (page - 1) * page_size
    matched: list[dict] = []
    total = 0
    all_candidates = list(data_store._candidates_by_id.values())
    for candidate in all_candidates:
        for email in candidate.get("email_history", []):
            if _matches_filters(email, candidate):
                total += 1
                if total > offset and len(matched) < page_size:
                    matched.append({
                        "candidate_id": candidate.get("id"),
                        "candidate_name": candidate.get("name"),
                        "candidate_email": candidate.get("email"),
                        "job_title": email.get("job_title", ""),
                        "round": email.get("round_name", ""),
                        "decision": email.get("decision", ""),
                        "email_type": email.get("email_type", ""),
                        "status": email.get("status"),
                        "sent_at": email.get("sent_at"),
                        "sender_name": email.get("sender_name", ""),
                        "subject": email.get("subject"),
                    })

    return {
        "items": matched,
        "page": page,
        "page_size": page_size,
        "total": total,
    }


@router.post("/generate")
async def generate_communication_email(payload: CommunicationDraftRequest):
    candidate = await data_store.get_candidate(payload.candidate_id)
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found")

    interview = None
    if payload.interview_id is not None:
        interview = await data_store.get_interview(payload.interview_id)
        if not interview or interview.get("candidate_id") != payload.candidate_id:
            raise HTTPException(status_code=404, detail="Interview not found for candidate")

    job_context = {}
    if interview:
        job_context = await data_store.get_job(interview.get("job_id")) or {}
    else:
        apps = candidate.get("applications", [])
        if apps:
            job_context = await data_store.get_job(apps[0].get("job_id")) or {}

    try:
        draft = await draft_communication_email(
            candidate,
            job_context,
            interview,
            payload.email_type,
            payload.sender_name,
            payload.reply_to_email,
        )
        if isinstance(draft, dict):
            return draft
        return {"subject": "", "body": str(draft)}
    except Exception as exc:
        logger.error(f"Communication draft error: {exc}")
        raise HTTPException(status_code=500, detail="Failed to generate draft")


@router.post("/send")
async def send_communication_email(payload: CommunicationSendRequest) -> EmailRecord:
    candidate = await data_store.get_candidate(payload.candidate_id)
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found")

    interview_context = None
    if payload.interview_id is not None:
        interview_context = await data_store.get_interview(payload.interview_id)

    job_title = ""
    job_id = None
    if interview_context:
        job_id = interview_context.get("job_id")
        job = await data_store.get_job(job_id)
        job_title = job.get("title", "") if job else ""
    else:
        if candidate.get("applications"):
            app = candidate["applications"][0]
            job_id = app.get("job_id")
            job = await data_store.get_job(job_id)
            job_title = job.get("title", "") if job else ""

    # Actually send the email via SMTP
    email_sent = False
    recipient_email = candidate.get("email", "").strip()
    sender_name = payload.sender_name or "Recruitment Team"
    
    if recipient_email:
        try:
            # Build email body with sender info
            body = payload.body
            if payload.reply_to_email:
                body += f"\n\nReply-To: {payload.reply_to_email}"
            body += f"\n\nBest regards,\n{sender_name}"
            
            email_sent = send_custom_email(
                subject=payload.subject,
                body=body,
                recipient=recipient_email,
                sender=settings.smtp_from_email
            )
        except Exception as e:
            logger.error(f"Failed to send communication email to {recipient_email}: {e}")
            email_sent = False
    
    # Save to history regardless
    status = "Sent" if email_sent else "Failed"
    result = await data_store.add_email_history(
        payload.candidate_id,
        payload.subject,
        payload.body,
        status=status,
        email_type=payload.email_type,
        decision=payload.decision,
        interview_id=payload.interview_id,
        job_id=job_id,
        job_title=job_title,
        round_name=interview_context.get("round") or "" if interview_context else "",
        sender_name=payload.sender_name,
        reply_to_email=payload.reply_to_email,
        draft_saved=False,
    )
    clear_pending_cache()
    return result


@router.post("/save-draft")
async def save_communication_draft(payload: CommunicationSendRequest) -> EmailRecord:
    candidate = await data_store.get_candidate(payload.candidate_id)
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found")

    interview_context = None
    if payload.interview_id is not None:
        interview_context = await data_store.get_interview(payload.interview_id)

    job_title = ""
    job_id = None
    if interview_context:
        job_id = interview_context.get("job_id")
        job = await data_store.get_job(job_id)
        job_title = job.get("title", "") if job else ""
    else:
        if candidate.get("applications"):
            app = candidate["applications"][0]
            job_id = app.get("job_id")
            job = await data_store.get_job(job_id)
            job_title = job.get("title", "") if job else ""

    result = await data_store.add_email_history(
        payload.candidate_id,
        payload.subject,
        payload.body,
        status="Draft",
        email_type=payload.email_type,
        decision=payload.decision,
        interview_id=payload.interview_id,
        job_id=job_id,
        job_title=job_title,
        round_name=interview_context.get("round") or "" if interview_context else "",
        sender_name=payload.sender_name,
        reply_to_email=payload.reply_to_email,
        draft_saved=True,
    )
    clear_pending_cache()
    return result
