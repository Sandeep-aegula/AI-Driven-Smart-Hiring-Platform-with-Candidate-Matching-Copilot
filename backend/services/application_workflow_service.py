from __future__ import annotations

import hashlib
import logging
import uuid
from datetime import date, datetime
from pathlib import Path

from sqlalchemy import desc, or_, select
from sqlalchemy.orm import selectinload

from backend.core.config import settings
from backend.database.session import get_db_session
from backend.models.entities import (
    Application,
    ApplicationScore,
    ApplicationWorkflowStatus,
    Candidate,
    Job,
    Resume,
    ResumeParseResult,
)
from backend.schemas.workflow import (
    HRApplicationRead,
    PublicApplicationCreate,
    PublicJobDetail,
    PublicJobSummary,
)
from backend.services.ai_resume_service import evaluate_candidate_match, parse_resume_to_json
from backend.services.resume_parser_service import extract_text_from_document

logger = logging.getLogger(__name__)

ALLOWED_EXTENSIONS = {".pdf", ".doc", ".docx", ".txt"}
MAX_FILE_SIZE = 5 * 1024 * 1024
PUBLISHED_STATUS = "published"


def _uploads_root() -> Path:
    root = Path(settings.uploads_dir)
    if not root.is_absolute():
        root = Path(__file__).resolve().parents[2] / root
    root.mkdir(parents=True, exist_ok=True)
    return root


def _normalize_job_status(status: str) -> str:
    legacy_to_draft = {"Active", "Open", "draft", ""}
    if status in legacy_to_draft:
        return "draft"
    lowered = status.lower()
    if lowered in {"published", "paused", "closed", "draft"}:
        return lowered
    if status == "Paused":
        return "paused"
    if status == "Archived":
        return "closed"
    return "draft"


def _job_is_public(job: Job) -> bool:
    return job.status == PUBLISHED_STATUS


def _deadline_passed(deadline: str) -> bool:
    if not deadline:
        return False
    try:
        return date.fromisoformat(deadline[:10]) < date.today()
    except ValueError:
        return False


def _public_summary(job: Job) -> PublicJobSummary:
    description = (job.description or "").strip()
    short = description[:220] + ("…" if len(description) > 220 else "")
    return PublicJobSummary(
        id=job.id,
        title=job.title,
        department=job.department,
        location=job.location,
        employment_type=job.employment_type,
        work_mode=job.work_mode,
        experience_required=job.experience_required,
        short_description=short,
        deadline=job.deadline,
        required_skills=job.required_skills or job.requirements or [],
    )


def _public_detail(job: Job) -> PublicJobDetail:
    summary = _public_summary(job)
    return PublicJobDetail(
        **summary.model_dump(),
        description=job.description or "",
        responsibilities=job.responsibilities or [],
        requirements=job.requirements or [],
        preferred_skills=job.preferred_skills or [],
        qualifications=job.qualifications or [],
        benefits=job.benefits or [],
        openings=job.openings or 1,
    )


def _job_requirements(job: Job) -> dict:
    return {
        "title": job.title,
        "description": job.description,
        "experience": job.experience_required,
        "required_skills": (job.requirements or []) + (job.required_skills or []),
        "preferred_skills": job.preferred_skills or [],
        "qualifications": job.qualifications or [],
    }


def _recommendation_label(value: str) -> str:
    mapping = {
        "Strong Hire": "strong_match",
        "Hire": "recommended",
        "Hold": "review",
        "Reject": "not_recommended",
    }
    return mapping.get(value, "review")


async def list_public_jobs(
    search: str = "",
    department: str = "All",
    location: str = "All",
    employment_type: str = "All",
) -> list[PublicJobSummary]:
    async with get_db_session() as session:
        stmt = select(Job).where(Job.status == PUBLISHED_STATUS)
        if search:
            like = f"%{search}%"
            stmt = stmt.where(
                or_(Job.title.ilike(like), Job.department.ilike(like), Job.location.ilike(like))
            )
        if department != "All":
            stmt = stmt.where(Job.department == department)
        if location != "All":
            stmt = stmt.where(Job.location.ilike(f"%{location}%"))
        if employment_type != "All":
            stmt = stmt.where(Job.employment_type.ilike(f"%{employment_type}%"))
        stmt = stmt.order_by(desc(Job.published_at), desc(Job.updated_at))
        jobs = (await session.execute(stmt)).scalars().all()
        return [_public_summary(j) for j in jobs if not _deadline_passed(j.deadline)]


async def get_public_job(job_id: int) -> PublicJobDetail | None:
    async with get_db_session() as session:
        job = await session.get(Job, job_id)
        if not job or not _job_is_public(job) or _deadline_passed(job.deadline):
            return None
        return _public_detail(job)


async def publish_job(job_id: int) -> dict:
    async with get_db_session() as session:
        job = await session.get(Job, job_id)
        if not job:
            raise ValueError("Job not found")
        job.status = PUBLISHED_STATUS
        job.published_at = datetime.utcnow()
        await session.flush()
        await session.refresh(job)
        return {"id": job.id, "status": job.status, "published_at": job.published_at}


async def pause_job(job_id: int) -> dict:
    async with get_db_session() as session:
        job = await session.get(Job, job_id)
        if not job:
            raise ValueError("Job not found")
        job.status = "paused"
        await session.flush()
        return {"id": job.id, "status": job.status}


async def close_job(job_id: int) -> dict:
    async with get_db_session() as session:
        job = await session.get(Job, job_id)
        if not job:
            raise ValueError("Job not found")
        job.status = "closed"
        await session.flush()
        return {"id": job.id, "status": job.status}


async def normalize_created_job_status(job_id: int, incoming_status: str) -> None:
    async with get_db_session() as session:
        job = await session.get(Job, job_id)
        if not job:
            return
        if incoming_status in {"Active", "Open", "draft", ""} or incoming_status.lower() == "draft":
            job.status = "draft"
            await session.flush()


async def submit_public_application(
    job_id: int,
    payload: PublicApplicationCreate,
    file_bytes: bytes,
    original_filename: str,
    mime_type: str,
) -> dict:
    ext = Path(original_filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise ValueError("Unsupported file type. Upload PDF, DOC, DOCX, or TXT.")
    if not file_bytes:
        raise ValueError("Uploaded file is empty.")
    if len(file_bytes) > MAX_FILE_SIZE:
        raise ValueError("File exceeds the 5MB limit.")

    file_hash = hashlib.sha256(file_bytes).hexdigest()
    stored_filename = f"{uuid.uuid4().hex}{ext}"
    storage_path = str(_uploads_root() / stored_filename)
    Path(storage_path).write_bytes(file_bytes)

    async with get_db_session() as session:
        job = await session.get(Job, job_id)
        if not job:
            raise ValueError("Job not found")
        if not _job_is_public(job):
            raise ValueError("This job is not accepting applications.")
        if _deadline_passed(job.deadline):
            raise ValueError("The application deadline for this job has passed.")

        stmt = select(Candidate).where(Candidate.email == payload.email)
        candidate = (await session.execute(stmt)).scalar_one_or_none()
        if not candidate:
            candidate = Candidate(
                name=payload.full_name.strip(),
                email=str(payload.email).strip().lower(),
                phone=payload.phone.strip(),
                linkedin=payload.linkedin.strip(),
                portfolio=payload.portfolio.strip(),
                current_title=payload.current_title.strip(),
                current_company=payload.current_company.strip(),
                github=payload.github.strip(),
                years_experience=payload.years_experience,
                location=payload.location.strip(),
                status="Applied",
                summary=payload.cover_letter.strip(),
            )
            session.add(candidate)
            await session.flush()
            logger.info("Created candidate id=%s for public application job_id=%s", candidate.id, job.id)
        else:
            if payload.full_name.strip():
                candidate.name = payload.full_name.strip()
            if payload.phone.strip():
                candidate.phone = payload.phone.strip()
            if payload.location.strip():
                candidate.location = payload.location.strip()
            if payload.linkedin.strip():
                candidate.linkedin = payload.linkedin.strip()
            if payload.portfolio.strip():
                candidate.portfolio = payload.portfolio.strip()
            if payload.current_title.strip():
                candidate.current_title = payload.current_title.strip()
            if payload.current_company.strip():
                candidate.current_company = payload.current_company.strip()
            if payload.github.strip():
                candidate.github = payload.github.strip()
            if payload.years_experience:
                candidate.years_experience = payload.years_experience
            logger.info("Reused existing candidate id=%s for public application job_id=%s", candidate.id, job.id)

        application = Application(
            candidate_id=candidate.id,
            job_id=job.id,
            status=ApplicationWorkflowStatus.submitted.value,
            source="careers_page",
            cover_letter=payload.cover_letter.strip(),
        )
        session.add(application)
        await session.flush()
        logger.info("Saved application id=%s candidate_id=%s job_id=%s", application.id, candidate.id, job.id)

        resume = Resume(
            application_id=application.id,
            candidate_id=candidate.id,
            original_filename=original_filename,
            stored_filename=stored_filename,
            storage_path=storage_path,
            mime_type=mime_type or "",
            file_size=len(file_bytes),
            file_hash=file_hash,
        )
        session.add(resume)
        await session.flush()

        parse_result = ResumeParseResult(
            resume_id=resume.id,
            application_id=application.id,
            parser_status="pending",
        )
        session.add(parse_result)

        job.applications_count = (job.applications_count or 0) + 1
        application.status = ApplicationWorkflowStatus.parsing.value
        await session.flush()
        logger.info("Public application pipeline queued for application_id=%s", application.id)

        return {
            "application_id": application.id,
            "candidate_id": candidate.id,
            "job_id": job.id,
            "status": application.status,
            "message": "Application submitted successfully. Resume parsing has started.",
        }


async def process_application_pipeline(application_id: int) -> None:
    try:
        async with get_db_session() as session:
            stmt = (
                select(Application)
                .where(Application.id == application_id)
                .options(
                    selectinload(Application.resumes),
                    selectinload(Application.parse_results),
                )
            )
            application = (await session.execute(stmt)).scalar_one_or_none()
            if not application or not application.resumes:
                return
            resume = application.resumes[0]
            parse_result = application.parse_results[0] if application.parse_results else None
            if not parse_result:
                parse_result = ResumeParseResult(
                    resume_id=resume.id,
                    application_id=application.id,
                    processor_status="processing",
                )
                session.add(parse_result)
            else:
                parse_result.parser_status = "processing"
            await session.flush()

        file_bytes = Path(resume.storage_path).read_bytes()
        raw_text = extract_text_from_document(file_bytes, resume.original_filename)

        async with get_db_session() as session:
            application = await session.get(Application, application_id)
            job = await session.get(Job, application.job_id)
            candidate = await session.get(Candidate, application.candidate_id)
            resume = (
                await session.execute(select(Resume).where(Resume.application_id == application_id))
            ).scalar_one()
            parse_result = (
                await session.execute(
                    select(ResumeParseResult).where(ResumeParseResult.application_id == application_id)
                )
            ).scalar_one()

            parse_result.raw_text = raw_text
            try:
                parsed = await parse_resume_to_json(raw_text)
                parse_result.parsed_data = parsed
                parse_result.extracted_name = parsed.get("name", "")
                parse_result.extracted_email = parsed.get("email", "")
                parse_result.extracted_phone = parsed.get("phone", "")
                parse_result.extracted_skills = parsed.get("skills", [])
                parse_result.extracted_education = parsed.get("education", [])
                parse_result.extracted_experience = parsed.get("experience", [])
                parse_result.extracted_projects = parsed.get("projects", [])
                parse_result.extracted_certifications = parsed.get("certifications", [])
                parse_result.parser_status = "completed"
                parse_result.parsed_at = datetime.utcnow()
                parse_result.parser_error = ""

                if not candidate.name and parse_result.extracted_name:
                    candidate.name = parse_result.extracted_name
                if not candidate.phone and parse_result.extracted_phone:
                    candidate.phone = parse_result.extracted_phone
                if parse_result.extracted_skills:
                    candidate.tags = list({*(candidate.tags or []), *parse_result.extracted_skills[:10]})

                eval_result = await evaluate_candidate_match(parsed, _job_requirements(job))
                recommendation = _recommendation_label(eval_result.get("hire_recommendation", "Hold"))
                breakdown = eval_result.get("skill_match_breakdown", {}) or {}
                score = ApplicationScore(
                    application_id=application.id,
                    job_id=job.id,
                    ats_score=int(eval_result.get("match_score", 0) or 0),
                    skills_score=int(breakdown.get("match_percentage", eval_result.get("match_score", 0)) or 0),
                    experience_score=int(eval_result.get("match_score", 0) or 0),
                    education_score=0,
                    keyword_score=int(breakdown.get("match_percentage", 0) or 0),
                    job_match_score=int(eval_result.get("match_score", 0) or 0),
                    recommendation=recommendation,
                    strengths=breakdown.get("matched_skills", []),
                    gaps=breakdown.get("missing_skills", []),
                    scoring_version="v1",
                    scored_at=datetime.utcnow(),
                )
                session.add(score)
                application.match_score = score.job_match_score
                application.ai_summary = eval_result.get("resume_summary", eval_result.get("reason", ""))
                application.status = ApplicationWorkflowStatus.parsed.value
            except Exception as exc:
                logger.exception("Resume parsing failed for application_id=%s", application_id)
                parse_result.parser_status = "failed"
                parse_result.parser_error = "Resume parsing failed. HR can still review the application."
                application.status = ApplicationWorkflowStatus.under_review.value
                session.add(
                    ApplicationScore(
                        application_id=application.id,
                        job_id=job.id,
                        recommendation="review",
                        scoring_error="Automatic scoring unavailable.",
                        scored_at=datetime.utcnow(),
                    )
                )
            await session.flush()
    except Exception:
        logger.exception("Application pipeline failed for application_id=%s", application_id)


async def list_hr_applications(
    search: str = "",
    job_id: int | None = None,
    status: str = "All",
    recommendation: str = "All",
) -> list[HRApplicationRead]:
    async with get_db_session() as session:
        stmt = (
            select(Application)
            .options(
                selectinload(Application.candidate),
                selectinload(Application.job),
                selectinload(Application.resumes),
                selectinload(Application.parse_results),
                selectinload(Application.scores),
            )
            .order_by(desc(Application.created_at))
        )
        if job_id is not None:
            stmt = stmt.where(Application.job_id == job_id)
        if status != "All":
            stmt = stmt.where(Application.status == status)
        applications = (await session.execute(stmt)).scalars().all()
        results: list[HRApplicationRead] = []
        for app in applications:
            candidate = app.candidate
            job = app.job
            if search:
                blob = f"{candidate.name} {candidate.email} {job.title}".lower()
                if search.lower() not in blob:
                    continue
            resume = app.resumes[0] if app.resumes else None
            parse_result = app.parse_results[0] if app.parse_results else None
            score = sorted(app.scores, key=lambda s: s.id, reverse=True)[0] if app.scores else None
            if recommendation != "All" and (not score or score.recommendation != recommendation):
                continue
            results.append(
                HRApplicationRead(
                    id=app.id,
                    candidate_id=app.candidate_id,
                    job_id=app.job_id,
                    status=app.status,
                    source=app.source,
                    cover_letter=app.cover_letter,
                    applied_at=app.created_at,
                    reviewed_at=app.reviewed_at,
                    reviewed_by=app.reviewed_by,
                    recruiter_notes=app.recruiter_notes,
                    candidate_name=candidate.name,
                    candidate_email=candidate.email,
                    job_title=job.title,
                    job_department=job.department,
                    resume_filename=resume.original_filename if resume else "",
                    parser_status=parse_result.parser_status if parse_result else "pending",
                    score=score,
                    parse_result=parse_result,
                )
            )
        return results


async def update_application_status(
    application_id: int,
    status: str,
    recruiter_notes: str = "",
    reviewed_by: str = "",
) -> dict:
    allowed = {s.value for s in ApplicationWorkflowStatus}
    if status not in allowed:
        raise ValueError(f"Invalid status. Allowed: {', '.join(sorted(allowed))}")
    async with get_db_session() as session:
        application = await session.get(Application, application_id)
        if not application:
            raise ValueError("Application not found")
        application.status = status
        application.recruiter_notes = recruiter_notes or application.recruiter_notes
        application.reviewed_by = reviewed_by or application.reviewed_by
        application.reviewed_at = datetime.utcnow()
        await session.flush()
        return {"id": application.id, "status": application.status}