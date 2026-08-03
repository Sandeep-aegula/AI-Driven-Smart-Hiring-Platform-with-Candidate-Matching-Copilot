from __future__ import annotations

import logging
from datetime import datetime, timedelta

from fastapi import APIRouter, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from backend.schemas.entities import CandidateCreate, CandidateRead, CompareCandidatesRequest, EmailDraftRequest, EmailSendRequest, EmailRecord
from backend.database.data_store import data_store
from backend.services.ai_candidate_service import generate_ranking_explanation, analyze_skill_gap, compare_candidates
from backend.services.ai_email_service import draft_candidate_email
from backend.services.emailer import send_custom_email
from backend.database.session import get_db_session
from backend.models.entities import Candidate, Application, Job, Resume, ResumeParseResult, ApplicationScore, Communication

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("")
async def get_candidates(
    search: str = "",
    status: str = "All",
    skill: str = "All",
    job_id: int | None = None,
    min_match_score: int = 0,
    limit: int = 100,
    offset: int = 0,
    sort_by: str = "ats_score",
    sort_order: str = "desc"
) -> dict:
    """
    List candidates with enhanced filtering and metadata.

    Query Parameters:
    - search: Search by candidate name or email
    - status: Filter by application status (New, Applied, Shortlisted, Interview, Rejected, All)
    - skill: Filter by skill (not yet implemented in DB, for future use)
    - job_id: Filter by job ID (shows only candidates for this job)
    - min_match_score: Minimum ATS score filter
    - limit: Pagination limit (default 100)
    - offset: Pagination offset (default 0)
    - sort_by: Sort field (ats_score, name, applied_at)
    - sort_order: Sort order (asc, desc)

    Returns:
        dict: {
            "items": [...],
            "total": int,
            "limit": int,
            "offset": int,
            "status_counts": dict,
            "average_ats_score": float,
            "selected_job_title": str,
            "role_candidate_count": int
        }
    """
    from sqlalchemy import func, select
    from sqlalchemy.orm import selectinload

    async with get_db_session() as session:
        # Build the base query to filter applications by job
        if job_id:
            # Get only candidates who applied for this specific job
            if status != "All" and status != "":
                app_stmt = select(Application.candidate_id).where(
                    Application.job_id == job_id,
                    Application.status == status,
                )
                app_result = await session.execute(app_stmt)
                candidate_ids = [row[0] for row in app_result.fetchall()]
            else:
                # When showing "All" for a specific job, exclude candidates
                # whose application has already moved past the initial HR review
                # so the Candidates tab only shows the decision queue.
                # A candidate is excluded if they have at least one application
                # for this job in an advanced workflow stage.
                advanced_statuses = [
                    "shortlisted",
                    "interview",
                    "rejected",
                    "hired",
                    "withdrawn",
                ]
                initial_review_stmt = select(Application.candidate_id).where(
                    Application.job_id == job_id,
                    Application.status.notin_(advanced_statuses),
                )
                initial_review_result = await session.execute(initial_review_stmt)
                initial_review_ids = {
                    row[0] for row in initial_review_result.fetchall()
                }

                advanced_stmt = select(Application.candidate_id).where(
                    Application.job_id == job_id,
                    Application.status.in_(advanced_statuses),
                )
                advanced_result = await session.execute(advanced_stmt)
                advanced_ids = {row[0] for row in advanced_result.fetchall()}

                candidate_ids = list(initial_review_ids - advanced_ids)

            if not candidate_ids:
                return {
                    "items": [],
                    "total": 0,
                    "limit": limit,
                    "offset": offset,
                    "status_counts": {},
                    "average_ats_score": 0.0,
                    "selected_job_title": "",
                    "role_candidate_count": 0,
                }
            # Main query: candidates filtered by job_id
            stmt = select(Candidate).where(Candidate.id.in_(candidate_ids))
        else:
            # All candidates
            stmt = select(Candidate)

            if status != "All" and status != "":
                stmt = stmt.where(Candidate.status == status)

        stmt = stmt.options(
            selectinload(Candidate.applications).selectinload(Application.job),
            selectinload(Candidate.applications).selectinload(Application.scores),
        )

        # Search filter
        if search:
            search_like = f"%{search}%"
            stmt = stmt.where(
                Candidate.name.ilike(search_like) |
                Candidate.email.ilike(search_like)
            )

        # Count total before pagination
        count_stmt = select(func.count(Candidate.id)).select_from(Candidate)

        if job_id:
            count_stmt = count_stmt.where(Candidate.id.in_(candidate_ids))

        if status != "All" and status != "":
            count_stmt = count_stmt.where(Candidate.status == status)

        if search:
            count_stmt = count_stmt.where(
                Candidate.name.ilike(f"%{search}%") |
                Candidate.email.ilike(f"%{search}%")
            )

        total_result = await session.execute(count_stmt)
        total = total_result.scalar() or 0

        # Sort by ATS score if job_id is provided, otherwise by name
        if sort_by == "ats_score" and job_id:
            # Need to join with ApplicationScore for sorting
            stmt = stmt.options(
                selectinload(Candidate.applications).selectinload(Application.scores)
            )
        elif sort_by == "name":
            stmt = stmt.order_by(Candidate.name.asc() if sort_order == "asc" else Candidate.name.desc())
        else:
            stmt = stmt.order_by(Candidate.updated_at.desc() if sort_order == "desc" else Candidate.updated_at.asc())

        # Pagination
        stmt = stmt.limit(limit).offset(offset)

        result = await session.execute(stmt)
        candidates_list = result.scalars().unique().all()

        # If sorting by ATS score, sort in Python after fetching
        if sort_by == "ats_score" and job_id and candidates_list:
            def get_ats_score(cand):
                for app in cand.applications:
                    if app.job_id == job_id:
                        for score in app.scores:
                            return score.ats_score if score.ats_score > 0 else 0
                return 0

            candidates_list = sorted(
                candidates_list,
                key=get_ats_score,
                reverse=(sort_order == "desc")
            )

        # Calculate status counts for the selected job
        status_counts = {}
        if job_id:
            status_count_stmt = select(
                Application.status,
                func.count(Application.id).label("count")
            ).where(
                Application.job_id == job_id
            ).group_by(Application.status)
        else:
            status_count_stmt = select(
                Candidate.status,
                func.count(Candidate.id).label("count")
            ).group_by(Candidate.status)

        status_result = await session.execute(status_count_stmt)
        status_counts = {row[0]: row[1] for row in status_result}

        # Calculate average ATS score for the selected job
        avg_ats = 0.0
        if job_id:
            ats_stmt = select(func.avg(ApplicationScore.ats_score)).join(
                Application
            ).where(
                Application.job_id == job_id,
                ApplicationScore.ats_score > 0
            )
            ats_result = await session.execute(ats_stmt)
            avg_ats = float(ats_result.scalar() or 0.0)

        # Get selected job title and candidate count for role
        selected_job_title = "All Jobs"
        role_candidate_count = total
        if job_id:
            job_stmt = select(Job).where(Job.id == job_id)
            job_result = await session.execute(job_stmt)
            job_row = job_result.scalar_one_or_none()
            if job_row:
                selected_job_title = job_row.title
                # Count candidates for this job
                role_count_stmt = select(func.count(Application.id)).where(
                    Application.job_id == job_id
                )
                role_count_result = await session.execute(role_count_stmt)
                role_candidate_count = role_count_result.scalar() or 0

        # Convert to dict and add ATS scores
        items = []
        for c in candidates_list:
            # Get ATS score from application for this job
            ats_score = 0
            application_status = "Applied"
            application_id = None

            if job_id:
                for app in c.applications:
                    if app.job_id == job_id:
                        application_id = app.id
                        application_status = app.status
                        for score in app.scores:
                            ats_score = score.ats_score
                            break
                        break
            else:
                # Use first application's score
                if c.applications:
                    app = c.applications[0]
                    application_id = app.id
                    application_status = app.status
                    for score in app.scores:
                        ats_score = score.ats_score
                        break

            # Apply min_match_score filter
            if min_match_score > 0 and ats_score < min_match_score:
                continue

            items.append({
                "id": c.id,
                "application_id": application_id,
                "job_id": job_id if job_id is not None else (c.applications[0].job_id if c.applications else None),
                "job_title": selected_job_title if job_id is not None else (c.applications[0].job.title if c.applications and c.applications[0].job else ""),
                "name": c.name,
                "email": c.email,
                "phone": c.phone,
                "current_title": c.current_title,
                "current_company": c.current_company,
                "years_experience": c.years_experience,
                "location": c.location,
                "status": application_status,
                "candidate_status": c.status,
                "ats_score": ats_score,
                "match_score": c.match_score,
                "summary": c.summary,
                "linkedin": c.linkedin,
                "github": c.github,
                "portfolio": c.portfolio,
                "avatar_url": c.avatar_url,
                "created_at": c.created_at.isoformat() if c.created_at else None,
                "updated_at": c.updated_at.isoformat() if c.updated_at else None,
            })

        logger.info(
            "GET /candidates returned %s items (search=%r, status=%r, job_id=%r, min_match_score=%s, offset=%s, limit=%s)",
            len(items),
            search,
            status,
            job_id,
            min_match_score,
            offset,
            limit,
        )

        return {
            "items": items,
            "total": len(items),  # Total after filtering
            "limit": limit,
            "offset": offset,
            "status_counts": status_counts,
            "average_ats_score": round(avg_ats, 1),
            "selected_job_title": selected_job_title,
            "role_candidate_count": role_candidate_count,
        }


@router.get("/{candidate_id}")
async def get_candidate_by_id(candidate_id: int) -> dict:
    """Get detailed candidate information including resume and application data."""
    async with get_db_session() as session:
        from sqlalchemy.orm import selectinload

        stmt = select(Candidate).options(
            selectinload(Candidate.applications).selectinload(Application.job),
            selectinload(Candidate.applications).selectinload(Application.resumes),
            selectinload(Candidate.applications).selectinload(Application.scores),
        ).where(Candidate.id == candidate_id)

        result = await session.execute(stmt)
        candidate = result.scalar_one_or_none()

        if not candidate:
            raise HTTPException(status_code=404, detail="Candidate not found")

        # Build response with applications
        applications_data = []
        for app in candidate.applications:
            # Get the first resume if available
            resume_data = None
            if app.resumes:
                resume = app.resumes[0]
                resume_data = {
                    "id": resume.id,
                    "original_filename": resume.original_filename,
                    "stored_filename": resume.stored_filename,
                    "storage_path": resume.storage_path,
                    "mime_type": resume.mime_type,
                    "file_size": resume.file_size,
                    "uploaded_at": resume.uploaded_at.isoformat() if resume.uploaded_at else None,
                }

            # Get ATS score
            ats_score = 0
            if app.scores:
                ats_score = app.scores[0].ats_score if app.scores else 0

            applications_data.append({
                "id": app.id,
                "job_id": app.job_id,
                "job_title": app.job.title if app.job else "Unknown",
                "job_department": app.job.department if app.job else "",
                "status": app.status,
                "match_score": app.match_score,
                "ats_score": ats_score,
                "applied_at": app.created_at.isoformat() if app.created_at else None,
                "resume": resume_data,
            })

        return {
            "id": candidate.id,
            "name": candidate.name,
            "email": candidate.email,
            "phone": candidate.phone,
            "current_title": candidate.current_title,
            "current_company": candidate.current_company,
            "years_experience": candidate.years_experience,
            "location": candidate.location,
            "status": candidate.status,
            "match_score": candidate.match_score,
            "summary": candidate.summary,
            "linkedin": candidate.linkedin,
            "github": candidate.github,
            "portfolio": candidate.portfolio,
            "avatar_url": candidate.avatar_url,
            "created_at": candidate.created_at.isoformat() if candidate.created_at else None,
            "updated_at": candidate.updated_at.isoformat() if candidate.updated_at else None,
            "applications": applications_data,
        }


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


@router.post("/applications/{application_id}/shortlist")
async def shortlist_candidate(application_id: int) -> dict:
    """
    Shortlist a candidate for a specific application.
    Updates application status and creates a communication queue record.
    """
    from sqlalchemy import select
    from backend.models.entities import Application, Communication, Candidate, Job

    async with get_db_session() as session:
        # Get the application with candidate and job
        stmt = select(Application).options(
            selectinload(Application.candidate),
            selectinload(Application.job)
        ).where(Application.id == application_id)

        result = await session.execute(stmt)
        application = result.scalar_one_or_none()

        if not application:
            raise HTTPException(status_code=404, detail="Application not found")

        # Check if already shortlisted
        if application.status == "shortlisted":
            return {
                "success": True,
                "message": "Candidate is already shortlisted",
                "application_id": application_id,
                "status": "shortlisted"
            }

        # Update application status
        application.status = "shortlisted"
        application.candidate.status = "Shortlisted"
        logger.info(f"Candidate {application.candidate_id} shortlisted for application {application_id}")

        # Check if communication record already exists
        comm_stmt = select(Communication).where(
            Communication.application_id == application_id,
            Communication.status == "pending"
        )
        comm_result = await session.execute(comm_stmt)
        existing_comm = comm_result.scalar_one_or_none()

        if not existing_comm:
            # Create communication queue record
            communication = Communication(
                candidate_id=application.candidate_id,
                application_id=application_id,
                job_id=application.job_id,
                recruitment_round="Initial Screening",
                status="pending",
                email=application.candidate.email,
                subject=f"Application Update: {application.job.title}",
                message=f"Dear {application.candidate.name},\n\nWe are pleased to inform you that your application for the position of {application.job.title} has been shortlisted for further consideration.",
                queued_at=datetime.utcnow()
            )
            session.add(communication)
            logger.info(f"Communication queue record created for application {application_id}")

        await session.commit()

        return {
            "success": True,
            "message": "Candidate shortlisted successfully",
            "application_id": application_id,
            "candidate_id": application.candidate_id,
            "candidate_name": application.candidate.name,
            "job_title": application.job.title if application.job else "",
            "status": "shortlisted",
            "communication_created": existing_comm is None
        }


@router.post("/applications/shortlist-bulk")
async def shortlist_candidates_bulk(application_ids: list[int]) -> dict:
    """
    Bulk shortlist multiple candidates for their applications.
    Each application_id must belong to a valid application.
    Returns summary of successful and failed shortlists.
    """
    from sqlalchemy import select
    from sqlalchemy.orm import selectinload
    from backend.models.entities import Application, Communication, Candidate, Job

    if not application_ids:
        raise HTTPException(status_code=400, detail="No application IDs provided")

    if len(application_ids) > 100:
        raise HTTPException(status_code=400, detail="Cannot shortlist more than 100 candidates at once")

    results = {
        "successful": [],
        "failed": [],
        "already_shortlisted": []
    }

    async with get_db_session() as session:
        for app_id in application_ids:
            try:
                # Get the application with candidate and job
                stmt = select(Application).options(
                    selectinload(Application.candidate),
                    selectinload(Application.job)
                ).where(Application.id == app_id)

                result = await session.execute(stmt)
                application = result.scalar_one_or_none()

                if not application:
                    results["failed"].append({
                        "application_id": app_id,
                        "error": "Application not found"
                    })
                    continue

                # Check if already shortlisted
                if application.status == "shortlisted":
                    results["already_shortlisted"].append({
                        "application_id": app_id,
                        "candidate_id": application.candidate_id,
                        "candidate_name": application.candidate.name
                    })
                    continue

                # Update application status
                application.status = "shortlisted"
                application.candidate.status = "Shortlisted"
                logger.info(f"Bulk shortlist: Candidate {application.candidate_id} shortlisted for application {app_id}")

                # Check if communication record already exists
                comm_stmt = select(Communication).where(
                    Communication.application_id == app_id,
                    Communication.status == "pending"
                )
                comm_result = await session.execute(comm_stmt)
                existing_comm = comm_result.scalar_one_or_none()

                if not existing_comm:
                    # Create communication queue record
                    communication = Communication(
                        candidate_id=application.candidate_id,
                        application_id=app_id,
                        job_id=application.job_id,
                        recruitment_round="Initial Screening",
                        status="pending",
                        email=application.candidate.email,
                        subject=f"Application Update: {application.job.title}",
                        message=f"Dear {application.candidate.name},\n\nWe are pleased to inform you that your application for the position of {application.job.title} has been shortlisted for further consideration.",
                        queued_at=datetime.utcnow()
                    )
                    session.add(communication)

                results["successful"].append({
                    "application_id": app_id,
                    "candidate_id": application.candidate_id,
                    "candidate_name": application.candidate.name,
                    "job_title": application.job.title if application.job else ""
                })

                logger.info(f"Bulk shortlist: Candidate {application.candidate_id} shortlisted for application {app_id}")

            except Exception as e:
                logger.error(f"Bulk shortlist error for application {app_id}: {e}")
                results["failed"].append({
                    "application_id": app_id,
                    "error": str(e)
                })

        await session.commit()

    total_success = len(results["successful"]) + len(results["already_shortlisted"])
    if len(results["failed"]) > 0:
        # Partial success is acceptable
        logger.warning(f"Bulk shortlist completed with {len(results['failed'])} failures")

    return {
        "success": True,
        "message": f"Shortlisted {len(results['successful'])} candidates ({len(results['already_shortlisted'])} already shortlisted, {len(results['failed'])} failed)",
        "results": results,
        "total_processed": len(application_ids),
        "total_successful": len(results["successful"]),
        "total_already_shortlisted": len(results["already_shortlisted"]),
        "total_failed": len(results["failed"])
    }


@router.get("/applications/{application_id}")
async def get_application_details(application_id: int) -> dict:
    """
    Get detailed application information including resume, parse results, and ATS score.
    """
    from sqlalchemy import select
    from sqlalchemy.orm import selectinload
    from backend.models.entities import Application, Resume, ResumeParseResult, ApplicationScore

    async with get_db_session() as session:
        stmt = select(Application).options(
            selectinload(Application.candidate),
            selectinload(Application.job),
            selectinload(Application.resumes).selectinload(Resume.parse_results),
            selectinload(Application.scores),
        ).where(Application.id == application_id)

        result = await session.execute(stmt)
        application = result.scalar_one_or_none()

        if not application:
            raise HTTPException(status_code=404, detail="Application not found")

        # Get the latest resume
        resume_data = None
        parse_result = None
        if application.resumes:
            resume = application.resumes[-1]
            resume_data = {
                "id": resume.id,
                "original_filename": resume.original_filename,
                "stored_filename": resume.stored_filename,
                "storage_path": resume.storage_path,
                "mime_type": resume.mime_type,
                "file_size": resume.file_size,
                "uploaded_at": resume.uploaded_at.isoformat() if resume.uploaded_at else None,
            }

            # Get parse result
            if resume.parse_results:
                parse_result = resume.parse_results[-1]

        # Get ATS score
        ats_score = None
        if application.scores:
            ats_score = application.scores[-1]

        return {
            "id": application.id,
            "candidate_id": application.candidate_id,
            "job_id": application.job_id,
            "status": application.status,
            "match_score": application.match_score,
            "source": application.source,
            "cover_letter": application.cover_letter,
            "ai_summary": application.ai_summary,
            "recruiter_notes": application.recruiter_notes,
            "created_at": application.created_at.isoformat() if application.created_at else None,
            "updated_at": application.updated_at.isoformat() if application.updated_at else None,
            "candidate": {
                "id": application.candidate.id,
                "name": application.candidate.name,
                "email": application.candidate.email,
                "phone": application.candidate.phone,
                "current_title": application.candidate.current_title,
                "current_company": application.candidate.current_company,
                "years_experience": application.candidate.years_experience,
                "location": application.candidate.location,
                "linkedin": application.candidate.linkedin,
                "github": application.candidate.github,
                "portfolio": application.candidate.portfolio,
                "summary": application.candidate.summary,
            },
            "job": {
                "id": application.job.id if application.job else None,
                "title": application.job.title if application.job else "",
                "department": application.job.department if application.job else "",
                "location": application.job.location if application.job else "",
            } if application.job else None,
            "resume": resume_data,
            "ats_score": {
                "id": ats_score.id if ats_score else None,
                "ats_score": ats_score.ats_score if ats_score else 0,
                "skills_score": ats_score.skills_score if ats_score else 0,
                "experience_score": ats_score.experience_score if ats_score else 0,
                "education_score": ats_score.education_score if ats_score else 0,
                "keyword_score": ats_score.keyword_score if ats_score else 0,
                "job_match_score": ats_score.job_match_score if ats_score else 0,
                "recommendation": ats_score.recommendation if ats_score else "",
                "strengths": ats_score.strengths if ats_score else [],
                "gaps": ats_score.gaps if ats_score else [],
                "scored_at": ats_score.scored_at.isoformat() if ats_score and ats_score.scored_at else None,
            } if ats_score else None,
        }


