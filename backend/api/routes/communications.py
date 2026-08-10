from __future__ import annotations

import asyncio
import logging
from datetime import datetime
from typing import Any

from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from fastapi.responses import JSONResponse
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload

from backend.constants.email_mapping import STATUS_TO_EMAIL_TYPE, EMAIL_TYPE_OPTIONS, PENDING_DECISIONS
from backend.core.config import settings
from backend.database.data_store import data_store
from backend.database.session import get_db_session
from backend.models.entities import Communication, Candidate, Application, Job, Interview
from backend.schemas.entities import (
    CommunicationBulkDraftRequest,
    CommunicationDraftGenerateRequest,
    CommunicationDraftRequest,
    CommunicationDraftResponse,
    CommunicationDraftUpdateRequest,
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


def _iso_now() -> str:
    return datetime.utcnow().isoformat(timespec="seconds")


def _format_date_time(date_value: str, time_value: str) -> tuple[str, str]:
    formatted_date = date_value or ""
    formatted_time = time_value or ""

    try:
        parsed_date = datetime.fromisoformat(date_value).date()
        formatted_date = parsed_date.strftime("%B %d, %Y").replace(" 0", " ")
    except Exception:
        pass

    try:
        parsed_time = datetime.strptime(time_value, "%H:%M")
        formatted_time = parsed_time.strftime("%I:%M %p").lstrip("0")
    except Exception:
        pass

    return formatted_date, formatted_time


def _non_empty_lines(*values: str | None) -> list[str]:
    return [value for value in values if value]


def _build_interview_invitation_draft(
    communication: Communication,
    candidate: Candidate,
    job: Job | None,
    interview: Interview,
) -> tuple[str, str]:
    if not job:
        raise ValueError("Linked job not found for interview communication.")
    if not interview.date or not interview.time:
        raise ValueError("Interview date and time are required.")
    if not interview.type:
        raise ValueError("Interview type is required.")
    if not interview.recruiter_name:
        raise ValueError("Interviewer name is required.")

    job_title = job.title
    company_name = settings.app_name
    candidate_name = candidate.name
    round_name = interview.round or communication.recruitment_round or "Interview"
    round_number = interview.round_number or 1
    interview_type = interview.type or ""
    interview_mode = interview.meeting_platform or ""
    interview_date, interview_time = _format_date_time(interview.date or "", interview.time or "")
    timezone = interview.timezone or "UTC"
    interviewer_name = interview.recruiter_name or ""
    interviewer_designation = interview.interviewer_designation or ""
    interviewer_email = interview.interviewer_email or ""
    meeting_link = interview.meeting_link or ""
    location = interview.location or ""
    instructions = interview.instructions or ""

    subject = f"Interview Invitation — {job_title} — {round_name}"

    body_lines = [
        f"Dear {candidate_name},",
        "",
        f"Thank you for progressing to the next stage of the recruitment process for the {job_title} position.",
        "",
        "We are pleased to invite you to attend the following interview:",
        "",
    ]

    if getattr(job, "department", ""):
        body_lines.append(f"Job Department: {job.department}")

    body_lines.extend([
        f"Interview Round: {round_name}",
        f"Interview Round Number: {round_number}",
        f"Interview Type: {interview_type}",
        f"Date: {interview_date or interview.date}",
        f"Time: {interview_time or interview.time} {timezone}".rstrip(),
        f"Interview Mode: {interview_mode}",
    ])

    if interviewer_name:
        interviewer_line = f"Interviewer: {interviewer_name}"
        interviewer_context = ", ".join(_non_empty_lines(interviewer_designation, interviewer_email))
        if interviewer_context:
            interviewer_line += f" ({interviewer_context})"
        body_lines.extend([interviewer_line])

    interview_type_key = interview.type.lower()

    if interview_type_key == "online" and not meeting_link:
        raise ValueError("Meeting link is required for online interviews.")
    if interview_type_key in {"in-person", "offline", "onsite"} and not location:
        raise ValueError("Location is required for in-person interviews.")
    if interview_type_key == "phone" and not instructions:
        raise ValueError("Call instructions are required for phone interviews.")

    if meeting_link and interview_type_key == "online":
        body_lines.extend(["", "Meeting Link:", meeting_link])
    elif location and interview_type_key in {"in-person", "offline", "onsite"}:
        body_lines.extend(["", "Location:", location])
    elif instructions and interview_type_key == "phone":
        body_lines.extend(["", "Call Instructions:", instructions])
    elif meeting_link:
        body_lines.extend(["", "Meeting Link:", meeting_link])
    elif location:
        body_lines.extend(["", "Location:", location])

    if instructions:
        body_lines.extend(["", "Additional Instructions:", instructions])

    body_lines.extend(
        [
            "",
            "Please join the interview at least 5 minutes before the scheduled time. If you are unable to attend, please notify us as soon as possible.",
            "",
            "We look forward to speaking with you.",
            "",
            "Best regards,",
            company_name,
        ]
    )

    if settings.smtp_from_email:
        body_lines.append(settings.smtp_from_email)

    return subject, "\n".join(body_lines)


# def _communication_response(communication: Communication, candidate: Candidate, interview: Interview, job: Job | None) -> dict[str, Any]:
#     interview_date, interview_time = _format_date_time(interview.date or "", interview.time or "")
#     return {
#         "communication_id": communication.id,
#         "interview_id": interview.id,
#         "candidate_id": candidate.id,
#         "candidate_name": candidate.name,
#         "recipient_email": communication.email,
#         "subject": communication.subject,
#         "body": communication.message,
#         "status": communication.status,
#         "generated_at": communication.generated_at.isoformat(timespec="seconds") if communication.generated_at else _iso_now(),
#         "job_id": communication.job_id,
#         "job_title": job.title if job else "",
#         "round_name": interview.round,
#         "interview_mode": interview.type,
#         "interview_date": interview_date or interview.date,
#         "interview_time": interview_time or interview.time,
#         "timezone": interview.timezone or "UTC",
#     }
def _communication_response(communication: Communication, candidate: Candidate, interview: Interview | None, job: Job | None) -> dict[str, Any]:
    if interview:
        interview_date, interview_time = _format_date_time(interview.date or "", interview.time or "")
    else:
        interview_date, interview_time = "", ""

    return {
        "communication_id": communication.id,
        "interview_id": interview.id if interview else None,
        "candidate_id": candidate.id,
        "candidate_name": candidate.name,
        "recipient_email": communication.email,
        "subject": communication.subject,
        "body": communication.message,
        "status": communication.status,
        "generated_at": communication.generated_at.isoformat(timespec="seconds") if communication.generated_at else _iso_now(),
        "job_id": communication.job_id,
        "job_title": job.title if job else "",
        "round_name": interview.round if interview else communication.recruitment_round,
        "interview_mode": interview.type if interview else "",
        "interview_date": interview_date if interview else "",
        "interview_time": interview_time if interview else "",
        "timezone": interview.timezone if interview else "UTC",
    }

def clear_pending_cache() -> None:
    _pending_queue_cache["timestamp"] = None
    _pending_queue_cache["queue"] = []


def _safe_send_result(send_result: dict[str, Any]) -> dict[str, Any]:
    return {
        "success": bool(send_result.get("success")),
        "status_code": int(send_result.get("status_code", 500)),
        "error_type": send_result.get("error_type", ""),
        "error_message": send_result.get("error_message", ""),
    }


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
        application = candidate.get("applications", [])[0]
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
    Returns candidates who have been scheduled and are pending email invitation.
    """
    async with get_db_session() as session:
        stmt = select(Communication).options(
            selectinload(Communication.candidate),
            selectinload(Communication.job)
        ).where(
            Communication.status.in_(["pending", "draft", "failed"])
        ).order_by(Communication.queued_at.desc())

        result = await session.execute(stmt)
        communications = result.scalars().all()

        pending_queue = []
        for comm in communications:
            interview_data = None
            if comm.interview_id:
                stmt_iv = select(Interview).where(Interview.id == comm.interview_id)
                res_iv = await session.execute(stmt_iv)
                interview_data = res_iv.scalar_one_or_none()

            pending_queue.append({
                "id": comm.id,
                "interview_id": comm.interview_id,
                "candidate_id": comm.candidate_id,
                "candidate_name": comm.candidate.name if comm.candidate else "",
                "candidate_email": comm.email,
                "application_id": comm.application_id,
                "job_id": comm.job_id,
                "job_title": comm.job.title if comm.job else "",
                "department": comm.job.department if comm.job else "",
                "round_number": 1,
                "round_name": comm.recruitment_round,
                "round": comm.recruitment_round,
                "interview_date": interview_data.date if interview_data else "",
                "interview_time": interview_data.time if interview_data else "",
                "interview_mode": interview_data.type if interview_data else "Online",
                "interviewer_name": interview_data.recruiter_name if interview_data else "",
                "meeting_link": interview_data.meeting_link if interview_data else "",
                "location": interview_data.location if interview_data else None,
                "invitation_email_status": interview_data.invitation_email_status if interview_data else "pending",
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

    if not interview and payload.email_type == "Interview Invitation":
        interviews = await data_store.list_interviews(candidate_id=payload.candidate_id)
        if interviews:
            interview = sorted(interviews, key=lambda iv: iv.get("updated_at", ""), reverse=True)[0]

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
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        logger.error(f"Communication draft error: {exc}")
        raise HTTPException(status_code=500, detail="Failed to generate draft")


async def _load_communication_bundle(session, communication_id: int) -> tuple[Communication | None, Candidate | None, Job | None, Interview | None]:
    stmt = select(Communication).options(
        selectinload(Communication.candidate),
        selectinload(Communication.job),
    ).where(Communication.id == communication_id)
    result = await session.execute(stmt)
    communication = result.scalar_one_or_none()
    if not communication:
        return None, None, None, None

    interview = None
    if communication.interview_id is not None:
        stmt_interview = select(Interview).where(Interview.id == communication.interview_id)
        result_interview = await session.execute(stmt_interview)
        interview = result_interview.scalar_one_or_none()
    if interview is None and communication.candidate_id:
        interview_stmt = select(Interview).where(Interview.candidate_id == communication.candidate_id)
        if communication.job_id is not None:
            interview_stmt = interview_stmt.where(Interview.job_id == communication.job_id)

        if communication.recruitment_round:
            exact_round_stmt = interview_stmt.where(Interview.round == communication.recruitment_round).order_by(Interview.updated_at.desc(), Interview.created_at.desc())
            exact_round_result = await session.execute(exact_round_stmt.limit(1))
            interview = exact_round_result.scalar_one_or_none()

        if interview is None:
            fallback_stmt = interview_stmt.order_by(Interview.updated_at.desc(), Interview.created_at.desc())
            fallback_result = await session.execute(fallback_stmt.limit(1))
            interview = fallback_result.scalar_one_or_none()

        if interview is not None and communication.interview_id is None:
            communication.interview_id = interview.id

    candidate = communication.candidate
    job = communication.job
    if candidate is None and communication.candidate_id:
        stmt_candidate = select(Candidate).where(Candidate.id == communication.candidate_id)
        result_candidate = await session.execute(stmt_candidate)
        candidate = result_candidate.scalar_one_or_none()
    if job is None and communication.job_id:
        stmt_job = select(Job).where(Job.id == communication.job_id)
        result_job = await session.execute(stmt_job)
        job = result_job.scalar_one_or_none()

    return communication, candidate, job, interview


# @router.post("/{communication_id}/generate-draft", response_model=CommunicationDraftResponse)
# async def generate_interview_draft(communication_id: int, payload: CommunicationDraftGenerateRequest):
#     try:
#         async with get_db_session() as session:
#             communication, candidate, job, interview = await _load_communication_bundle(session, communication_id)
#             if not communication:
#                 raise HTTPException(status_code=404, detail="Communication not found")
#             if not candidate:
#                 raise HTTPException(status_code=404, detail="Candidate not found")
#             if not interview:
#                 raise HTTPException(
#                     status_code=404,
#                     detail={
#                         "message": "Interview not found for communication",
#                         "communication_id": communication_id,
#                         "candidate_id": communication.candidate_id,
#                         "job_id": communication.job_id,
#                         "recruitment_round": communication.recruitment_round,
#                     },
#                 )

#             if communication.status == "draft" and not payload.regenerate and communication.subject and communication.message:
#                 return _communication_response(communication, candidate, interview, job)

#             subject, body = _build_interview_invitation_draft(communication, candidate, job, interview)
#             communication.subject = subject
#             communication.message = body
#             communication.status = "draft"
#             communication.generated_at = datetime.utcnow()
#             communication.error_message = ""
#             await session.commit()
#             await session.refresh(communication)
#             clear_pending_cache()
#             return _communication_response(communication, candidate, interview, job)
#     except ValueError as exc:
#         raise HTTPException(status_code=400, detail=str(exc))
@router.post("/{communication_id}/generate-draft", response_model=CommunicationDraftResponse)
async def generate_interview_draft(communication_id: int, payload: CommunicationDraftGenerateRequest):
    try:
        async with get_db_session() as session:
            communication, candidate, job, interview = await _load_communication_bundle(session, communication_id)
            if not communication:
                raise HTTPException(status_code=404, detail="Communication not found")
            if not candidate:
                raise HTTPException(status_code=404, detail="Candidate not found")

            if communication.status == "draft" and not payload.regenerate and communication.subject and communication.message:
                return _communication_response(communication, candidate, interview, job)

            if interview:
                # existing interview-invite logic
                subject, body = _build_interview_invitation_draft(communication, candidate, job, interview)
            else:
                # NEW: no interview yet → generic communication draft (e.g. Shortlisted notice)
                candidate_dict = {"name": candidate.name, "current_title": "", "match_score": 0}
                job_dict = {"title": job.title if job else ""}
                draft = await draft_communication_email(
                    candidate_dict, job_dict, None,
                    email_type=communication.recruitment_round or "Shortlisted",
                )
                subject, body = draft["subject"], draft["body"]

            communication.subject = subject
            communication.message = body
            communication.status = "draft"
            communication.generated_at = datetime.utcnow()
            communication.error_message = ""
            await session.commit()
            await session.refresh(communication)
            clear_pending_cache()
            return _communication_response(communication, candidate, interview, job)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

@router.post("/generate-drafts")
async def generate_bulk_interview_drafts(payload: CommunicationBulkDraftRequest) -> dict:
    results: list[dict[str, Any]] = []
    success_count = 0
    failure_count = 0

    async with get_db_session() as session:
        for communication_id in payload.communication_ids:
            candidate_name = ""
            try:
                communication, candidate, job, interview = await _load_communication_bundle(session, communication_id)
                if not communication or not candidate or not interview:
                    raise ValueError("Communication, candidate, or interview not found")
                candidate_name = candidate.name

                if communication.status == "draft" and not payload.regenerate and communication.subject and communication.message:
                    results.append({
                        "communication_id": communication.id,
                        "candidate_name": candidate.name,
                        "status": "draft",
                        "subject": communication.subject,
                    })
                    success_count += 1
                    continue

                subject, body = _build_interview_invitation_draft(communication, candidate, job, interview)
                communication.subject = subject
                communication.message = body
                communication.status = "draft"
                communication.generated_at = datetime.utcnow()
                communication.error_message = ""
                success_count += 1
                results.append({
                    "communication_id": communication.id,
                    "candidate_name": candidate.name,
                    "status": "draft",
                    "subject": subject,
                })
            except Exception as exc:
                failure_count += 1
                results.append({
                    "communication_id": communication_id,
                    "candidate_name": candidate_name,
                    "status": "failed",
                    "error_message": str(exc),
                })

        await session.commit()
        clear_pending_cache()

    return {
        "success": failure_count == 0,
        "sent": 0,
        "failed": failure_count,
        "generated": success_count,
        "message": (
            f"{success_count} personalized interview drafts were generated successfully." if failure_count == 0
            else f"{success_count} drafts generated successfully. {failure_count} draft could not be generated."
        ),
        "results": results,
    }


@router.put("/{communication_id}/draft", response_model=CommunicationDraftResponse)
async def save_interview_draft(communication_id: int, payload: CommunicationDraftUpdateRequest):
    async with get_db_session() as session:
        communication, candidate, job, interview = await _load_communication_bundle(session, communication_id)
        if not communication:
            raise HTTPException(status_code=404, detail="Communication not found")
        if not candidate:
            raise HTTPException(status_code=404, detail="Candidate not found")
        if not interview:
            raise HTTPException(status_code=404, detail="Interview not found for communication")

        communication.subject = payload.subject
        communication.message = payload.body
        communication.status = "draft"
        if communication.generated_at is None:
            communication.generated_at = datetime.utcnow()
        communication.error_message = ""
        await session.commit()
        await session.refresh(communication)
        clear_pending_cache()
        return _communication_response(communication, candidate, interview, job)


@router.put("/{communication_id}/cancel", response_model=CommunicationDraftResponse)
async def cancel_interview_communication(communication_id: int):
    async with get_db_session() as session:
        communication, candidate, job, interview = await _load_communication_bundle(session, communication_id)
        if not communication:
            raise HTTPException(status_code=404, detail="Communication not found")
        if not candidate or not interview:
            raise HTTPException(status_code=404, detail="Communication context not found")

        communication.status = "cancelled"
        communication.error_message = ""
        await session.commit()
        await session.refresh(communication)
        clear_pending_cache()
        return _communication_response(communication, candidate, interview, job)


# @router.post("/{communication_id}/send")
# async def send_interview_draft(communication_id: int) -> dict:
#     async with get_db_session() as session:
#         communication, candidate, job, interview = await _load_communication_bundle(session, communication_id)
#         if not communication:
#             raise HTTPException(status_code=404, detail="Communication not found")
#         if not candidate:
#             raise HTTPException(status_code=404, detail="Candidate not found")
#         if not interview:
#             raise HTTPException(status_code=404, detail="Interview not found for communication")
#         if not communication.subject or not communication.message:
#             raise HTTPException(status_code=400, detail="Draft is missing subject or body")

#         recipient_email = candidate.email.strip()
#         send_result = _safe_send_result({"success": False, "status_code": 500, "error_message": "Email service failed to send the message."})
#         if recipient_email:
#             send_result = _safe_send_result(
#                 send_custom_email(
#                     subject=communication.subject,
#                     body=communication.message,
#                     recipient=recipient_email,
#                     sender=settings.smtp_from_email,
#                 )
#             )

#         communication.status = "sent" if send_result["success"] else "failed"
#         communication.sent_at = datetime.utcnow() if send_result["success"] else None
#         communication.error_message = send_result["error_message"] if not send_result["success"] else ""
#         if send_result["success"] and interview:
#             interview.invitation_email_status = "sent"
#             interview.invitation_sent_at = datetime.utcnow()
#         elif interview:
#             interview.invitation_email_status = "failed"
#         await session.commit()
#         clear_pending_cache()

#     if not send_result["success"]:
#         return JSONResponse(
#             status_code=send_result["status_code"],
#             content={
#                 "success": False,
#                 "message": send_result["error_message"],
#                 "error_message": send_result["error_message"],
#                 "status": "failed",
#             },
#         )

#     return {
#         "success": True,
#         "message": "Interview invitation sent successfully.",
#         "status": "sent",
#         "communication_id": communication_id,
#         "candidate_id": candidate.id,
#         "interview_id": interview.id,
#         "recipient_email": recipient_email,
#     }
@router.post("/{communication_id}/send")
async def send_interview_draft(communication_id: int) -> dict:
    async with get_db_session() as session:
        communication, candidate, job, interview = await _load_communication_bundle(session, communication_id)
        if not communication:
            raise HTTPException(status_code=404, detail="Communication not found")
        if not candidate:
            raise HTTPException(status_code=404, detail="Candidate not found")
        if not communication.subject or not communication.message:
            raise HTTPException(status_code=400, detail="Draft is missing subject or body")

        recipient_email = candidate.email.strip()
        send_result = _safe_send_result({"success": False, "status_code": 500, "error_message": "Email service failed to send the message."})
        if recipient_email:
            send_result = _safe_send_result(
                send_custom_email(
                    subject=communication.subject,
                    body=communication.message,
                    recipient=recipient_email,
                    sender=settings.smtp_from_email,
                )
            )

        communication.status = "sent" if send_result["success"] else "failed"
        communication.sent_at = datetime.utcnow() if send_result["success"] else None
        communication.error_message = send_result["error_message"] if not send_result["success"] else ""
        if interview:
            interview.invitation_email_status = "sent" if send_result["success"] else "failed"
            if send_result["success"]:
                interview.invitation_sent_at = datetime.utcnow()
        await session.commit()
        clear_pending_cache()

    if not send_result["success"]:
        return JSONResponse(
            status_code=send_result["status_code"],
            content={
                "success": False,
                "message": send_result["error_message"],
                "error_message": send_result["error_message"],
                "status": "failed",
            },
        )

    return {
        "success": True,
        "message": "Interview invitation sent successfully.",
        "status": "sent",
        "communication_id": communication_id,
        "candidate_id": candidate.id,
        "interview_id": interview.id if interview else None,
        "recipient_email": recipient_email,
    }

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
            app = candidate.get("applications", [])[0]
            job_id = app.get("job_id")
            job = await data_store.get_job(job_id)
            job_title = job.get("title", "") if job else ""

    recipient_email = candidate.get("email", "").strip()
    sender_name = payload.sender_name or "Recruitment Team"
    body = payload.body
    if payload.reply_to_email:
        body += f"\n\nReply-To: {payload.reply_to_email}"
    body += f"\n\nBest regards,\n{sender_name}"

    send_result = _safe_send_result({"success": False, "status_code": 500, "error_message": "Email service failed to send the message."})
    if recipient_email:
        send_result = _safe_send_result(
            send_custom_email(
                subject=payload.subject,
                body=body,
                recipient=recipient_email,
                sender=settings.smtp_from_email,
            )
        )

    status = "sent" if send_result["success"] else "failed"
    result = await data_store.add_email_history(
        payload.candidate_id,
        payload.subject,
        body,
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
    
    async with get_db_session() as session:
        if payload.interview_id is not None:
            stmt_iv = select(Interview).where(Interview.id == payload.interview_id)
            res_iv = await session.execute(stmt_iv)
            iv = res_iv.scalar_one_or_none()
            if iv:
                iv.invitation_email_status = "sent" if send_result["success"] else "failed"
                if send_result["success"]:
                    iv.invitation_sent_at = datetime.utcnow()
                    
        stmt_comm = select(Communication).where(
            Communication.candidate_id == payload.candidate_id,
            Communication.status.in_(["pending", "failed"])
        )
        if payload.interview_id is not None:
            stmt_comm = stmt_comm.where(Communication.interview_id == payload.interview_id)
        res_comm = await session.execute(stmt_comm)
        comm = res_comm.scalars().first()
        if comm:
            comm.status = "sent" if send_result["success"] else "failed"
            comm.sent_at = datetime.utcnow() if send_result["success"] else None
            comm.error_message = send_result["error_message"] if not send_result["success"] else ""
            comm.subject = payload.subject
            comm.message = body
            
        await session.commit()
        
    clear_pending_cache()
    if not send_result["success"]:
        return JSONResponse(
            status_code=send_result["status_code"],
            content={
                "success": False,
                "message": send_result["error_message"],
                "error_message": send_result["error_message"],
                "status": status,
                "sent_at": result.get("sent_at", ""),
            },
        )
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
            app = candidate.get("applications", [])[0]
            job_id = app.get("job_id")
            job = await data_store.get_job(job_id)
            job_title = job.get("title", "") if job else ""

    recipient_email = candidate.get("email", "").strip()
    sender_name = sender_name or "Recruitment Team"
    full_body = body
    if reply_to_email:
        full_body += f"\n\nReply-To: {reply_to_email}"
    full_body += f"\n\nBest regards,\n{sender_name}"

    attachment_filename = None
    attachment_bytes = None
    if file:
        attachment_filename = file.filename
        attachment_bytes = await file.read()

    send_result = _safe_send_result({"success": False, "status_code": 500, "error_message": "Email service failed to send the message."})
    if recipient_email:
        send_result = _safe_send_result(
            send_custom_email(
                subject=subject,
                body=full_body,
                recipient=recipient_email,
                sender=settings.smtp_from_email,
                attachment_filename=attachment_filename,
                attachment_bytes=attachment_bytes,
            )
        )

    status = "sent" if send_result["success"] else "failed"
    result = await data_store.add_email_history(
        candidate_id,
        subject,
        full_body,
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
    
    async with get_db_session() as session:
        if interview_id is not None:
            stmt_iv = select(Interview).where(Interview.id == interview_id)
            res_iv = await session.execute(stmt_iv)
            iv = res_iv.scalar_one_or_none()
            if iv:
                iv.invitation_email_status = "sent" if send_result["success"] else "failed"
                if send_result["success"]:
                    iv.invitation_sent_at = datetime.utcnow()
                    
        stmt_comm = select(Communication).where(
            Communication.candidate_id == candidate_id,
            Communication.status.in_(["pending", "failed"])
        )
        if interview_id is not None:
            stmt_comm = stmt_comm.where(Communication.interview_id == interview_id)
        res_comm = await session.execute(stmt_comm)
        comm = res_comm.scalars().first()
        if comm:
            comm.status = "sent" if send_result["success"] else "failed"
            comm.sent_at = datetime.utcnow() if send_result["success"] else None
            comm.error_message = send_result["error_message"] if not send_result["success"] else ""
            comm.subject = subject
            comm.message = full_body
            
        await session.commit()
        
    clear_pending_cache()
    if not send_result["success"]:
        return JSONResponse(
            status_code=send_result["status_code"],
            content={
                "success": False,
                "message": send_result["error_message"],
                "error_message": send_result["error_message"],
                "status": status,
                "sent_at": result.get("sent_at", ""),
            },
        )
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
            app = candidate.get("applications", [])[0]
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

    async with get_db_session() as session:
        results: list[dict[str, Any]] = []
        sent = 0
        failed = 0
        auth_failed = False
        auth_message = ""

        for comm_id in communication_ids:
            try:
                stmt = select(Communication).options(
                    selectinload(Communication.candidate),
                    selectinload(Communication.job)
                ).where(Communication.id == comm_id)

                result = await session.execute(stmt)
                communication = result.scalar_one_or_none()

                if not communication:
                    failed += 1
                    results.append({
                        "communication_id": comm_id,
                        "status": "failed",
                        "error_message": "Communication record not found"
                    })
                    continue

                if communication.status == "sent":
                    sent += 1
                    results.append({
                        "communication_id": comm_id,
                        "candidate_id": communication.candidate_id,
                        "candidate_name": communication.candidate.name if communication.candidate else "",
                        "status": "sent",
                        "already_sent": True,
                        "error_message": "",
                    })
                    continue

                candidate_name = communication.candidate.name if communication.candidate else "Candidate"
                job_title = communication.job.title if communication.job else "the position"

                personalized_body = body or communication.message or ""
                personalized_subject = subject or communication.subject or ""
                if subject:
                    personalized_subject = personalized_subject.replace("{{candidate_name}}", candidate_name).replace("{{job_title}}", job_title)
                if body:
                    personalized_body = personalized_body.replace("{{candidate_name}}", candidate_name).replace("{{job_title}}", job_title)

                recipient_email = communication.email.strip()
                communication.status = "sending"
                communication.error_message = ""
                communication.subject = personalized_subject
                communication.message = personalized_body
                await session.flush()

                send_result = _safe_send_result({"success": False, "status_code": 500, "error_message": "Email service failed to send the message."})
                if recipient_email:
                    send_result = _safe_send_result(
                        send_custom_email(
                            subject=personalized_subject,
                            body=personalized_body + f"\n\nBest regards,\n{sender_name}",
                            recipient=recipient_email,
                            sender=settings.smtp_from_email,
                        )
                    )

                if send_result["success"]:
                    communication.status = "sent"
                    communication.sent_at = datetime.utcnow()
                    communication.error_message = ""
                    sent += 1
                    
                    if communication.interview_id:
                        stmt_iv = select(Interview).where(Interview.id == communication.interview_id)
                        res_iv = await session.execute(stmt_iv)
                        iv = res_iv.scalar_one_or_none()
                        if iv:
                            iv.invitation_email_status = "sent"
                            iv.invitation_sent_at = datetime.utcnow()
                else:
                    communication.status = "failed"
                    communication.sent_at = None
                    communication.error_message = send_result["error_message"]
                    failed += 1
                    if send_result["error_type"] == "authentication":
                        auth_failed = True
                        auth_message = send_result["error_message"]
                        
                    if communication.interview_id:
                        stmt_iv = select(Interview).where(Interview.id == communication.interview_id)
                        res_iv = await session.execute(stmt_iv)
                        iv = res_iv.scalar_one_or_none()
                        if iv:
                            iv.invitation_email_status = "failed"

                results.append({
                    "communication_id": comm_id,
                    "candidate_id": communication.candidate_id,
                    "candidate_name": candidate_name,
                    "email": recipient_email,
                    "status": communication.status,
                    "error_message": communication.error_message,
                })

                logger.info("Bulk email processed for communication %s", comm_id)

            except Exception as e:
                logger.error("Bulk email error for communication %s: %s", comm_id, e)
                failed += 1
                results.append({
                    "communication_id": comm_id,
                    "status": "failed",
                    "error_message": "Email service failed to send the message.",
                })

        await session.commit()

    response = {
        "success": failed == 0,
        "total": len(communication_ids),
        "sent": sent,
        "failed": failed,
        "results": results,
    }

    if sent > 0 and failed > 0:
        response["message"] = f"{sent} emails sent successfully. {failed} emails failed."
        clear_pending_cache()
        return JSONResponse(status_code=207, content=response)

    if sent == 0:
        response["message"] = auth_message or "Email service failed to send the message."
        clear_pending_cache()
        return JSONResponse(status_code=502 if auth_failed else 500, content=response)

    response["message"] = f"{sent} emails sent successfully."
    clear_pending_cache()
    return JSONResponse(status_code=200, content=response)


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
                "error_message": comm.error_message,
                "queued_at": comm.queued_at.isoformat() if comm.queued_at else None,
                "sent_at": comm.sent_at.isoformat() if comm.sent_at else None,
            })

        return {
            "items": items,
            "page": page,
            "page_size": page_size,
            "total": total,
        }



