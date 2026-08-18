from __future__ import annotations

from ast import literal_eval
import logging

from fastapi import APIRouter, BackgroundTasks, File, Form, HTTPException, UploadFile

from backend.schemas.workflow import (
    HRApplicationRead,
    PublicApplicationCreate,
    PublicApplicationResponse,
    PublicJobDetail,
    PublicJobSummary,
)
from backend.scripts.services.application_workflow_service import (
    get_public_job,
    list_hr_applications,
    list_public_jobs,
    process_application_pipeline,
    submit_public_application,
)

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/jobs", response_model=list[PublicJobSummary])
async def get_public_jobs(
    search: str = "",
    department: str = "All",
    location: str = "All",
    employment_type: str = "All",
) -> list[PublicJobSummary]:
    return await list_public_jobs(search, department, location, employment_type)


@router.get("/jobs/{job_id}", response_model=PublicJobDetail)
async def get_public_job_details(job_id: int) -> PublicJobDetail:
    job = await get_public_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job


@router.post("/jobs/{job_id}/apply", response_model=PublicApplicationResponse)
async def apply_to_job(
    job_id: int,
    background_tasks: BackgroundTasks,
    full_name: str = Form(...),
    email: str = Form(...),
    phone: str = Form(...),
    location: str = Form(""),
    linkedin: str = Form(""),
    portfolio: str = Form(""),
    current_title: str = Form(""),
    years_experience: int = Form(0),
    current_company: str = Form(""),
    github: str = Form(""),
    skills: str = Form(""),
    cover_letter: str = Form(""),
    linkedin_url: str = Form(""),
    portfolio_url: str = Form(""),
    resume: UploadFile = File(...),
) -> PublicApplicationResponse:
    resolved_linkedin = linkedin.strip() or linkedin_url.strip()
    resolved_portfolio = portfolio.strip() or portfolio_url.strip()
    logger.info("Public application received for job_id=%s email=%s", job_id, email.strip().lower())

    parsed_skills: list[str] = []
    skills_value = skills.strip()
    if skills_value:
        try:
            literal_skills = literal_eval(skills_value)
        except Exception:
            literal_skills = None

        if isinstance(literal_skills, list):
            parsed_skills = [str(skill).strip() for skill in literal_skills if str(skill).strip()]
        else:
            parsed_skills = [s.strip() for s in skills_value.split(",") if s.strip()]

    payload = PublicApplicationCreate(
        full_name=full_name,
        email=email,
        phone=phone,
        location=location,
        linkedin=resolved_linkedin,
        portfolio=resolved_portfolio,
        current_title=current_title,
        years_experience=years_experience,
        current_company=current_company,
        github=github,
        skills=parsed_skills,
        cover_letter=cover_letter,
    )
    try:
        contents = await resume.read()
        result = await submit_public_application(
            job_id,
            payload,
            contents,
            resume.filename or "resume.pdf",
            resume.content_type or "",
        )
        background_tasks.add_task(process_application_pipeline, result["application_id"])
        return PublicApplicationResponse(**result)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail="Unable to submit application.") from exc
