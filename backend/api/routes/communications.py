from __future__ import annotations

import asyncio
import logging
from datetime import datetime
from typing import Any

from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload

from backend.constants.email_mapping import STATUS_TO_EMAIL_TYPE, EMAIL_TYPE_OPTIONS, PENDING_DECISIONS
from backend.core.config import settings
from backend.database.data_store import data_store
from backend.database.session import get_db_session
from backend.models.entities import Communication, Candidate, Application, Job
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


async def _build_pending_entry(candidate: dict, interview: dict | None = None) -> dict:
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
            job = await data_store.get_job(job_id)
            job_title = job.get("title", job_title)

    round_name = ""
    if interview is not None:
        round_name = interview.get("round", "")
    elif candidate.get("status") == "Interview Scheduled":
        interviews = [iv for iv in (await data_store.list_interviews()) if iv.get("candidate_id") == candidate.get("id")]
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
    candidates = list((await data_store.list_candidates()))
    interviews = list((await data_store.list_interviews()))
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
    """
    Get pending communications from the database.
    Returns candidates who have been shortlisted and are pending email communication.
    """
    async with get_db_session() as session:
        # Query communications with status 'pending'
        stmt = select(Communication).options(
            selectinload(Communication.candidate),
            selectinload(Communication.job)
        ).where(
            Communication.status == "pending"
        ).order_by(Communication.queued_at.desc())

        result = await session.execute(stmt)
        communications = result.scalars().all()

        pending_queue = []
        for comm in communications:
            pending_queue.append({
                "id": comm.id,
                "candidate_id": comm.candidate_id,
                "application_id": comm.application_id,
                "job_id": comm.job_id,
                "candidate_name": comm.candidate.name if comm.candidate else "",
                "candidate_email": comm.email,
                "job_title": comm.job.title if comm.job else "",
                "department": comm.job.department if comm.job else "",
                "round": comm.recruitment_round,
                "status": comm.status,
                "subject": comm.subject,
                "message": comm.message,
                "queued_at": comm.queued_at.isoformat() if comm.queued_at else None,
                "days_pending": (datetime.utcnow() - comm.queued_at).days if comm.queued_at else 0,
            })

        return pending_queue


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
    all_candidates = list((await data_store.list_candidates()))
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


@router.post("/send-multipart")
async def send_communication_email_multipart(
    candidate_id: int = Form(...),
    subject: str = Form(...),
    body: str = Form(...),
    email_type: str = Form(""),
    decision: str = Form(""),
    interview_id: int | None = Form(None),
    sender_name: str = Form(""),
    reply_to_email: str = Form(""),
    file: UploadFile | None = File(None)
) -> dict:
    candidate = await data_store.get_candidate(candidate_id)
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found")

    interview_context = None
    if interview_id is not None:
        interview_context = await data_store.get_interview(interview_id)

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

    email_sent = False
    recipient_email = candidate.get("email", "").strip()
    sender_name = sender_name or "Recruitment Team"
    
    if recipient_email:
        try:
            full_body = body
            if reply_to_email:
                full_body += f"\n\nReply-To: {reply_to_email}"
            full_body += f"\n\nBest regards,\n{sender_name}"
            
            attachment_filename = None
            attachment_bytes = None
            if file:
                attachment_filename = file.filename
                attachment_bytes = await file.read()
            
            email_sent = send_custom_email(
                subject=subject,
                body=full_body,
                recipient=recipient_email,
                sender=settings.smtp_from_email,
                attachment_filename=attachment_filename,
                attachment_bytes=attachment_bytes
            )
        except Exception as e:
            logger.error(f"Failed to send communication email to {recipient_email}: {e}")
            email_sent = False
    
    status = "Sent" if email_sent else "Failed"
    result = await data_store.add_email_history(
        candidate_id,
        subject,
        body,
        status=status,
        email_type=email_type,
        decision=decision,
        interview_id=interview_id,
        job_id=job_id,
        job_title=job_title,
        round_name=interview_context.get("round") or "" if interview_context else "",
        sender_name=sender_name,
        reply_to_email=reply_to_email,
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


@router.post("/send-bulk")
async def send_bulk_communications(payload: dict) -> dict:
    """
    Send bulk emails to multiple pending candidates.
    Updates communication status from pending to sent.

    Request body:
    {
        "communication_ids": [1, 2, 3],
        "subject": "Email subject",
        "body": "Email body with {{candidate_name}} and {{job_title}} placeholders",
        "sender_name": "Recruitment Team"
    }
    """
    communication_ids = payload.get("communication_ids", [])
    subject = payload.get("subject", "")
    body = payload.get("body", "")
    sender_name = payload.get("sender_name", "Recruitment Team")

    if not communication_ids:
        raise HTTPException(status_code=400, detail="No communication IDs provided")

    if not subject or not body:
        raise HTTPException(status_code=422, detail="Subject and body are required")

    async with get_db_session() as session:
        results = {"successful": [], "failed": []}

        for comm_id in communication_ids:
            try:
                stmt = select(Communication).options(
                    selectinload(Communication.candidate),
                    selectinload(Communication.job)
                ).where(Communication.id == comm_id)

                result = await session.execute(stmt)
                communication = result.scalar_one_or_none()

                if not communication:
                    results["failed"].append({
                        "communication_id": comm_id,
                        "error": "Communication record not found"
                    })
                    continue

                if communication.status == "sent":
                    results["successful"].append({
                        "communication_id": comm_id,
                        "candidate_id": communication.candidate_id,
                        "candidate_name": communication.candidate.name if communication.candidate else "",
                        "status": "already_sent"
                    })
                    continue

                candidate_name = communication.candidate.name if communication.candidate else "Candidate"
                job_title = communication.job.title if communication.job else "the position"

                personalized_body = body.replace("{{candidate_name}}", candidate_name).replace("{{job_title}}", job_title)
                personalized_subject = subject.replace("{{candidate_name}}", candidate_name).replace("{{job_title}}", job_title)

                email_sent = False
                recipient_email = communication.email.strip()
                if recipient_email:
                    try:
                        full_body = personalized_body + f"\n\nBest regards,\n{sender_name}"
                        email_sent = send_custom_email(
                            subject=personalized_subject,
                            body=full_body,
                            recipient=recipient_email,
                            sender=settings.smtp_from_email
                        )
                    except Exception as e:
                        logger.error(f"Failed to send bulk email to {recipient_email}: {e}")
                        email_sent = False

                communication.status = "sent" if email_sent else "failed"
                communication.subject = personalized_subject
                communication.message = personalized_body
                communication.sent_at = datetime.utcnow() if email_sent else None

                results["successful" if email_sent else "failed"].append({
                    "communication_id": comm_id,
                    "candidate_id": communication.candidate_id,
                    "candidate_name": candidate_name,
                    "email": recipient_email,
                    "status": communication.status
                })

                logger.info(f"Bulk email sent to {recipient_email} for communication {comm_id}")

            except Exception as e:
                logger.error(f"Bulk email error for communication {comm_id}: {e}")
                results["failed"].append({
                    "communication_id": comm_id,
                    "error": str(e)
                })

        await session.commit()

    return {
        "success": True,
        "message": f"Sent {len(results['successful'])} emails, {len(results['failed'])} failed",
        "total_processed": len(communication_ids),
        "total_successful": len(results["successful"]),
        "total_failed": len(results["failed"]),
        "results": results
    }


@router.get("/history-db")
async def get_communications_history_db(
    page: int = 1,
    page_size: int = 25,
    status: str | None = None,
) -> dict:
    """
    Get communications history from the database (sent/failed records).
    This is separate from the legacy email_history stored in candidate records.
    """
    if page < 1:
        page = 1
    if page_size < 1:
        page_size = 25

    async with get_db_session() as session:
        stmt = select(Communication).options(
            selectinload(Communication.candidate),
            selectinload(Communication.job)
        )

        count_stmt = select(func.count(Communication.id))

        if status:
            stmt = stmt.where(Communication.status == status)
            count_stmt = count_stmt.where(Communication.status == status)

        # Total count
        total_result = await session.execute(count_stmt)
        total = total_result.scalar() or 0

        # Pagination
        offset = (page - 1) * page_size
        stmt = stmt.order_by(Communication.sent_at.desc() if status == "sent" else Communication.queued_at.desc()).offset(offset).limit(page_size)

        result = await session.execute(stmt)
        communications = result.scalars().all()

        items = []
        for comm in communications:
            items.append({
                "id": comm.id,
                "candidate_id": comm.candidate_id,
                "application_id": comm.application_id,
                "job_id": comm.job_id,
                "candidate_name": comm.candidate.name if comm.candidate else "",
                "candidate_email": comm.email,
                "job_title": comm.job.title if comm.job else "",
                "round": comm.recruitment_round,
                "status": comm.status,
                "subject": comm.subject,
                "message": comm.message,
                "queued_at": comm.queued_at.isoformat() if comm.queued_at else None,
                "sent_at": comm.sent_at.isoformat() if comm.sent_at else None,
            })

        return {
            "items": items,
            "page": page,
            "page_size": page_size,
            "total": total,
        }



