from __future__ import annotations

from fastapi import APIRouter, HTTPException

from backend.schemas.workflow import ApplicationStatusUpdate, ApplicationSelectRequest, HRApplicationRead
from backend.scripts.services.application_workflow_service import (
    list_hr_applications,
    update_application_status,
)
from backend.scripts.services.onboarding_workflow_service import select_application_for_onboarding

router = APIRouter()


@router.get("", response_model=list[HRApplicationRead])
async def get_applications(
    search: str = "",
    job_id: int | None = None,
    status: str = "All",
    recommendation: str = "All",
) -> list[HRApplicationRead]:
    return await list_hr_applications(search, job_id, status, recommendation)


@router.patch("/{application_id}/status")
async def patch_application_status(application_id: int, payload: ApplicationStatusUpdate) -> dict:
    try:
        return await update_application_status(
            application_id,
            payload.status,
            payload.recruiter_notes,
            payload.reviewed_by,
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/{application_id}/select")
async def select_application(application_id: int, payload: ApplicationSelectRequest | None = None) -> dict:
    try:
        reviewer = payload.reviewed_by if payload else "HR"
        note = payload.selection_note if payload else ""
        return await select_application_for_onboarding(application_id, selected_by=reviewer, selection_note=note)
    except ValueError as exc:
        detail = str(exc)
        status_code = 404 if "not found" in detail.lower() else 400
        raise HTTPException(status_code=status_code, detail=detail) from exc
