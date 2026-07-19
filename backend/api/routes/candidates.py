from __future__ import annotations
import logging

from fastapi import APIRouter, HTTPException

from backend.schemas.entities import CandidateCreate, CandidateRead, CompareCandidatesRequest, EmailDraftRequest, EmailSendRequest, EmailRecord
from backend.database.data_store import data_store
from backend.services.ai_candidate_service import generate_ranking_explanation, analyze_skill_gap, compare_candidates
from backend.services.ai_email_service import draft_candidate_email
from backend.services.emailer import send_custom_email

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("", response_model=list[CandidateRead])
async def get_candidates(
    search: str = "", 
    status: str = "All", 
    skill: str = "All",
    job_id: int | None = None,
    min_match_score: int = 0,
    limit: int = 100,
    offset: int = 0
) -> list[CandidateRead]:
    return await data_store.list_candidates(
        search=search, 
        status=status, 
        skill=skill, 
        job_id=job_id, 
        min_match_score=min_match_score, 
        limit=limit, 
        offset=offset
    )


@router.get("/{candidate_id}", response_model=CandidateRead)
async def get_candidate_by_id(candidate_id: int) -> CandidateRead:
    candidate = await data_store.get_candidate(candidate_id)
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found")
    return candidate


@router.post("", response_model=CandidateRead)
async def create_candidate(payload: CandidateCreate) -> CandidateRead:
    return await data_store.create_candidate(payload)


@router.put("/{candidate_id}", response_model=CandidateRead)
async def update_candidate(candidate_id: int, payload: CandidateCreate) -> CandidateRead:
    try:
        return await data_store.update_candidate(candidate_id, payload)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/{candidate_id}/notes", response_model=CandidateRead)
async def note_candidate(candidate_id: int, note: str) -> CandidateRead:
    try:
        return await data_store.add_candidate_note(candidate_id, note)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


from backend.services.employee_conversion_service import create_employee_from_candidate

@router.post("/{candidate_id}/status", response_model=CandidateRead)
async def status_candidate(candidate_id: int, status: str) -> CandidateRead:
    try:
        cand = await data_store.update_candidate_status(candidate_id, status)
        if status == "Hired":
            await create_employee_from_candidate(candidate_id)
        return cand
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


# --- AI Endpoints ---

async def _get_job_context_for_candidate(candidate_id: int) -> dict:
    candidate = await data_store.get_candidate(candidate_id)
    if not candidate:
        raise ValueError("Candidate not found")
        
    apps = candidate.get("applications", [])
    if apps:
        job = await data_store.get_job(apps[0]["job_id"])
        if job:
            return job
    return {}


@router.get("/{candidate_id}/rank")
async def get_candidate_rank(candidate_id: int):
    candidate = await data_store.get_candidate(candidate_id)
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found")
        
    if "ranking_explanation" in candidate:
        return {"ranking_explanation": candidate["ranking_explanation"]}
        
    try:
        job = await _get_job_context_for_candidate(candidate_id)
        explanation = await generate_ranking_explanation(candidate, job)
        
        if data_store._candidates_by_id.get(candidate_id):
            data_store._candidates_by_id[candidate_id]["ranking_explanation"] = explanation
            await data_store._save()
            
        return {"ranking_explanation": explanation}
    except Exception as e:
        logger.error(f"Ranking explanation error: {e}")
        return {"ranking_explanation": "AI ranking unavailable at this time."}


@router.get("/{candidate_id}/skill-gap")
async def get_candidate_skill_gap(candidate_id: int):
    candidate = await data_store.get_candidate(candidate_id)
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found")
        
    if "skill_gap_analysis" in candidate:
        return candidate["skill_gap_analysis"]
        
    try:
        job = await _get_job_context_for_candidate(candidate_id)
        gap = await analyze_skill_gap(candidate, job)
        
        if data_store._candidates_by_id.get(candidate_id):
            data_store._candidates_by_id[candidate_id]["skill_gap_analysis"] = gap
            await data_store._save()
            
        return gap
    except Exception as e:
        logger.error(f"Skill gap error: {e}")
        return {"error": str(e)}


@router.post("/compare")
async def compare_multiple_candidates(payload: CompareCandidatesRequest):
    job = await data_store.get_job(payload.job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
        
    cands = []
    for cid in payload.candidate_ids:
        c = await data_store.get_candidate(cid)
        if c: cands.append(c)
        
    if len(cands) < 2:
        raise HTTPException(status_code=400, detail="Must provide at least 2 valid candidates to compare.")
        
    try:
        return await compare_candidates(cands, job)
    except Exception as e:
        logger.error(f"Compare error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{candidate_id}/generate-email")
async def draft_candidate_email_route(candidate_id: int, payload: EmailDraftRequest):
    candidate = await data_store.get_candidate(candidate_id)
    job = await data_store.get_job(payload.job_id)
    if not candidate or not job:
        raise HTTPException(status_code=404, detail="Candidate or Job not found")
        
    try:
        return await draft_candidate_email(candidate, job, payload.email_type)
    except Exception as e:
        logger.error(f"Email draft error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{candidate_id}/send-email", response_model=EmailRecord)
async def send_candidate_email(candidate_id: int, payload: EmailSendRequest):
    candidate = await data_store.get_candidate(candidate_id)
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found")
    
    # Actually send the email via SMTP (with Sent folder support)
    email_sent = False
    recipient_email = candidate.get("email", "").strip()
    if recipient_email:
        try:
            email_sent = send_custom_email(
                subject=payload.subject,
                body=payload.body,
                recipient=recipient_email,
                sender=settings.smtp_from_email
            )
        except Exception as e:
            logger.error(f"Failed to send email to {recipient_email}: {e}")
            email_sent = False
    
    # Save to history regardless
    status = "Sent" if email_sent else "Failed"
    return await data_store.add_email_history(
        candidate_id, 
        payload.subject, 
        payload.body, 
        status=status,
        email_type=payload.email_type if hasattr(payload, 'email_type') else "",
        draft_saved=False
    )


@router.get("/{candidate_id}/email-history", response_model=list[EmailRecord])
async def get_email_history(candidate_id: int):
    candidate = await data_store.get_candidate(candidate_id)
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found")
    return candidate.get("email_history", [])
