from __future__ import annotations

from fastapi import APIRouter, HTTPException

from backend.schemas.workflow import ApplicationStatusUpdate, HRApplicationRead
from backend.services.application_workflow_service import (
    list_hr_applications,
    update_application_status,
)

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
