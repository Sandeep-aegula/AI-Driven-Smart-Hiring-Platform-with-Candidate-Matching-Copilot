from __future__ import annotations

from fastapi import APIRouter, HTTPException

from backend.database.session import session_scope
from backend.schemas.entities import ScreeningResponse
from backend.services.recruitment import screen_resume_against_job, update_candidate_status

router = APIRouter()


@router.get("", response_model=ScreeningResponse)
def screen(candidate_id: int, job_id: int) -> ScreeningResponse:
    with session_scope() as session:
        try:
            return screen_resume_against_job(session, candidate_id, job_id)
        except ValueError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/approve")
def approve(candidate_id: int) -> dict[str, str]:
    with session_scope() as session:
        update_candidate_status(session, candidate_id, "Approved")
        return {"status": "approved"}


@router.post("/shortlist")
def shortlist(candidate_id: int) -> dict[str, str]:
    with session_scope() as session:
        update_candidate_status(session, candidate_id, "Shortlisted")
        return {"status": "shortlisted"}


@router.post("/reject")
def reject(candidate_id: int) -> dict[str, str]:
    with session_scope() as session:
        update_candidate_status(session, candidate_id, "Rejected")
        return {"status": "rejected"}
