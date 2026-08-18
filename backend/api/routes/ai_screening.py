from __future__ import annotations

from fastapi import APIRouter, HTTPException

from backend.schemas.entities import ScreeningResponse
from backend.scripts.services.recruitment import screen_resume_against_job
from backend.database.data_store import data_store

router = APIRouter()


@router.get("", response_model=ScreeningResponse)
async def screen(candidate_id: int, job_id: int) -> ScreeningResponse:
    try:
        return await screen_resume_against_job(None, candidate_id, job_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/approve")
async def approve(candidate_id: int) -> dict[str, str]:
    await data_store.update_candidate_status(candidate_id, "Approved")
    return {"status": "approved"}


@router.post("/shortlist")
async def shortlist(candidate_id: int) -> dict[str, str]:
    await data_store.update_candidate_status(candidate_id, "Shortlisted")
    return {"status": "shortlisted"}


@router.post("/reject")
async def reject(candidate_id: int) -> dict[str, str]:
    await data_store.update_candidate_status(candidate_id, "Rejected")
    return {"status": "rejected"}

