import logging
from typing import Any
from datetime import datetime
from sqlalchemy.future import select
from sqlalchemy import or_, and_, desc

from backend.schemas.entities import JobCreate, CandidateCreate, ApplicationCreate
from backend.database.session import get_db_session
from backend.models.entities import Job, Candidate, Application, Resume, ResumeData, Interview, Employee, Activity, Skill, Communication

logger = logging.getLogger(__name__)

JOB_COLUMN_NAMES = {column.name for column in Job.__table__.columns}
CANDIDATE_COLUMN_NAMES = {column.name for column in Candidate.__table__.columns}


def _job_model_data(payload: JobCreate) -> dict:
    """Map validated API payload fields to SQLAlchemy Job column names."""
    return {
        key: value
        for key, value in payload.model_dump().items()
        if key in JOB_COLUMN_NAMES
    }


def _candidate_model_data(payload: CandidateCreate) -> dict:
    """Map validated API payload fields to SQLAlchemy Candidate column names.

    CandidateBase carries a couple of API-facing fields (skill_match_breakdown,
    hire_recommendation) that aren't persisted columns on the Candidate model --
    without this filter, Candidate(**payload.model_dump()) raises
    "invalid keyword argument" on every candidate create/update.
    """
    return {
        key: value
        for key, value in payload.model_dump().items()
        if key in CANDIDATE_COLUMN_NAMES
    }


def _job_skill_names(payload: JobCreate) -> list[str]:
    return (
        list(payload.preferred_skills)
        + list(payload.requirements)
        + list(payload.required_skills)
        + list(payload.technical_skills)
        + list(payload.soft_skills)
        + list(payload.qualifications)
    )

def model_to_dict(obj):
    if obj is None:
        return None
    d = {}
    for column in obj.__table__.columns:
        d[column.name] = getattr(obj, column.name)
    # Handle relationships if loaded
    if hasattr(obj, "skills") and obj.skills:
        if isinstance(obj.skills, list) and obj.skills and hasattr(obj.skills[0], "id"):
            d["skills"] = [{"id": s.id, "name": s.name, "category": s.category} for s in obj.skills]
        else:
            d["skills"] = obj.skills
    if hasattr(obj, "applications") and obj.applications:
        d["applications"] = [{"id": a.id, "job_id": a.job_id, "status": a.status, "candidate_id": a.candidate_id} for a in obj.applications]
    if hasattr(obj, "resumes") and obj.resumes:
        # Determine the type of the first resume in the list to serialize correctly
        first_resume = obj.resumes[0] if isinstance(obj.resumes, list) and obj.resumes else None
        if first_resume is not None:
            # Check for attributes to distinguish between ResumeData and Resume
            if hasattr(first_resume, 'filename'):
                # This is likely a ResumeData object (from Candidate.resumes)
                d["resumes"] = [
                    {
                        "id": r.id,
                        "filename": r.filename,
                        "mime_type": r.mime_type,
                        "file_path": r.file_path,
                        "status": r.status,
                        "created_at": str(r.created_at) if r.created_at else None,
                    }
                    for r in obj.resumes
                ]
            elif hasattr(first_resume, 'original_filename'):
                # This is likely a Resume object (from Application.resumes)
                d["resumes"] = [
                    {
                        "id": r.id,
                        "filename": r.original_filename,  # API compatibility: use original_filename as filename
                        "original_filename": r.original_filename,
                        "stored_filename": r.stored_filename,
                        "storage_path": r.storage_path,
                        "mime_type": r.mime_type,
                        "file_size": r.file_size,
                        "uploaded_at": str(r.uploaded_at) if r.uploaded_at else None,
                    }
                    for r in obj.resumes
                ]
            else:
                # Fallback to the original way (which might break, but we don't know the type)
                d["resumes"] = [{"id": r.id, "filename": r.filename, "created_at": str(r.created_at)} for r in obj.resumes]
        else:
            d["resumes"] = []
    return d

class RecruitmentDataStore:
    def __init__(self):
        pass

    async def initialize(self) -> None:
        """Seed initial reference data when tables are empty."""
        # Seed skills if empty
        async with get_db_session() as session:
            from sqlalchemy import select
            result = await session.execute(select(Skill).limit(1))
            if result.scalar_one_or_none() is None:
                seed_skills = [
                    "Python", "FastAPI", "SQL", "PostgreSQL", "Docker",
                    "Machine Learning", "React", "TypeScript", "Ollama",
                    "Plotly", "AgGrid", "AWS", "Kubernetes", "Java",
                    "JavaScript (ES6+)", "C#", "Agentic AI", "RAG", "LLMs",
                    "Vector Databases", "Data Analysis", "React.js", "Next.js",
                    "Node.js", "Express.js", "REST APIs", "Socket.io",
                    "AWS (EC2, S3, CloudWatch)", "Git", "MySQL", "Ms excel",
                    "Ms word", "Tally", "Autocad", "Unity", "Postman",
                    "VS Code", "n8n", "node js", "express js", "AWS EC2",
                    "S3", "CloudWatch",
                ]
                for skill_name in seed_skills:
                    session.add(Skill(name=skill_name, category="General"))
                await session.commit()

    async def _skill_objects(self, session, skill_names: list[str]) -> list[Skill]:
        seen = set()
        cleaned = []
        for name in skill_names:
            t = name.strip()
            k = t.lower()
            if t and k not in seen:
                seen.add(k)
                cleaned.append(t)
                
        result = []
        for name in cleaned:
            stmt = select(Skill).where(Skill.name.ilike(name))
            res = await session.execute(stmt)
            skill = res.scalar_one_or_none()
            if not skill:
                skill = Skill(name=name, category="General")
                session.add(skill)
            result.append(skill)
        return result

    # --- Job Operations ---
    async def list_jobs(self, search: str = "", department: str = "All", status: str = "All", sort_by: str = "updated_at") -> list[dict]:
        async with get_db_session() as session:
            stmt = select(Job)
            if search:
                like = f"%{search}%"
                stmt = stmt.where(or_(Job.title.ilike(like), Job.department.ilike(like), Job.location.ilike(like)))
            if department != "All":
                stmt = stmt.where(Job.department == department)
            if status != "All":
                stmt = stmt.where(Job.status == status)
                
            if sort_by == "updated_at":
                stmt = stmt.order_by(desc(Job.updated_at))
            elif sort_by == "created_at":
                stmt = stmt.order_by(desc(Job.created_at))
                
            res = await session.execute(stmt)
            return [model_to_dict(j) for j in res.scalars().all()]

    async def get_job(self, job_id: int) -> dict | None:
        async with get_db_session() as session:
            stmt = select(Job).where(Job.id == job_id)
            res = await session.execute(stmt)
            return model_to_dict(res.scalar_one_or_none())

    async def create_job(self, payload: JobCreate) -> dict:
        async with get_db_session() as session:
            try:
                skills_objs = await self._skill_objects(session, _job_skill_names(payload))
                job = Job(**_job_model_data(payload))
                job.skills = skills_objs
                session.add(job)
                await session.flush()
                await session.refresh(job)
                return model_to_dict(job)
            except Exception:
                logger.exception("Failed to create job for title=%r", payload.title)
                raise

    async def update_job(self, job_id: int, payload: JobCreate) -> dict:
        async with get_db_session() as session:
            try:
                stmt = select(Job).where(Job.id == job_id)
                res = await session.execute(stmt)
                job = res.scalar_one_or_none()
                if not job:
                    raise ValueError("Job not found")

                job.skills = await self._skill_objects(session, _job_skill_names(payload))

                for key, value in _job_model_data(payload).items():
                    setattr(job, key, value)

                await session.flush()
                await session.refresh(job)
                return model_to_dict(job)
            except ValueError:
                raise
            except Exception:
                logger.exception("Failed to update job id=%s", job_id)
                raise

    async def archive_job(self, job_id: int) -> dict:
        async with get_db_session() as session:
            stmt = select(Job).where(Job.id == job_id)
            res = await session.execute(stmt)
            job = res.scalar_one_or_none()
            if not job: raise ValueError("Job not found")
            job.status = "Archived"
            await session.commit()
            await session.refresh(job)
            return model_to_dict(job)

    async def delete_job(self, job_id: int) -> None:
        async with get_db_session() as session:
            stmt = select(Job).where(Job.id == job_id)
            res = await session.execute(stmt)
            job = res.scalar_one_or_none()
            if job:
                await session.delete(job)
                await session.commit()

    async def clone_job(self, job_id: int) -> dict:
        async with get_db_session() as session:
            stmt = select(Job).where(Job.id == job_id)
            res = await session.execute(stmt)
            job = res.scalar_one_or_none()
            if not job: raise ValueError("Job not found")
            
            clone_data = model_to_dict(job)
            for k in ["id", "created_at", "updated_at", "applications_count", "skills"]:
                clone_data.pop(k, None)
            clone_data["title"] = f"{job.title} Copy"
            clone_data["status"] = "Active"

            new_job = Job(**{k: v for k, v in clone_data.items() if k in JOB_COLUMN_NAMES})
            session.add(new_job)
            await session.commit()
            await session.refresh(new_job)
            return model_to_dict(new_job)

    # --- Candidate Operations ---
    async def list_candidates(
        self, search: str = "", status: str = "All", skill: str = "All", job_id: int | None = None, min_match_score: int = 0, limit: int = 100, offset: int = 0
    ) -> list[dict]:
        async with get_db_session() as session:
            stmt = select(Candidate)
            if search:
                like = f"%{search}%"
                stmt = stmt.where(or_(Candidate.name.ilike(like), Candidate.email.ilike(like)))
            if status != "All":
                stmt = stmt.where(Candidate.status == status)
            if min_match_score > 0:
                stmt = stmt.where(Candidate.match_score >= min_match_score)
            
            if job_id is not None:
                stmt = stmt.join(Application).where(Application.job_id == job_id)
                
            if skill != "All":
                stmt = stmt.join(Candidate.skills).where(Skill.name.ilike(skill))
                
            stmt = stmt.order_by(desc(Candidate.match_score), desc(Candidate.updated_at)).offset(offset).limit(limit)
            res = await session.execute(stmt)
            return [model_to_dict(c) for c in res.scalars().all()]

    async def get_candidate(self, candidate_id: int) -> dict | None:
        async with get_db_session() as session:
            stmt = select(Candidate).where(Candidate.id == candidate_id)
            res = await session.execute(stmt)
            return model_to_dict(res.scalar_one_or_none())

    async def create_candidate(self, payload: CandidateCreate) -> dict:
        async with get_db_session() as session:
            candidate = Candidate(**_candidate_model_data(payload))
            session.add(candidate)
            await session.commit()
            await session.refresh(candidate)
            return model_to_dict(candidate)

    async def update_candidate(self, candidate_id: int, payload: CandidateCreate) -> dict:
        async with get_db_session() as session:
            stmt = select(Candidate).where(Candidate.id == candidate_id)
            res = await session.execute(stmt)
            candidate = res.scalar_one_or_none()
            if not candidate: raise ValueError("Candidate not found")

            for key, value in _candidate_model_data(payload).items():
                setattr(candidate, key, value)
            
            await session.commit()
            await session.refresh(candidate)
            return model_to_dict(candidate)

    async def add_candidate_note(self, candidate_id: int, note: str, author: str = "Recruiter") -> dict:
        async with get_db_session() as session:
            stmt = select(Candidate).where(Candidate.id == candidate_id)
            res = await session.execute(stmt)
            candidate = res.scalar_one_or_none()
            if not candidate: raise ValueError("Candidate not found")
            
            notes = list(candidate.notes) if candidate.notes else []
            notes.append({"author": author, "note": note, "created_at": datetime.utcnow().isoformat()})
            candidate.notes = notes
            
            await session.commit()
            await session.refresh(candidate)
            return model_to_dict(candidate)

    async def update_candidate_status(self, candidate_id: int, status: str) -> dict:
        async with get_db_session() as session:
            stmt = select(Candidate).where(Candidate.id == candidate_id)
            res = await session.execute(stmt)
            candidate = res.scalar_one_or_none()
            if not candidate: raise ValueError("Candidate not found")
            
            candidate.status = status
            
            act = Activity(icon="fa-user-pen", title=f"Candidate {status}", description=f"{candidate.name} status updated to {status}.", time="Just now")
            session.add(act)
            
            await session.commit()
            await session.refresh(candidate)
            return model_to_dict(candidate)

    async def add_email_history(self, candidate_id: int, **kwargs) -> dict:
        # In the schema we don't have email_history table yet, but we will store it in notes or ignore if not strict.
        # Actually in original JSON it was in candidate["email_history"]. We can just add it to candidate.notes for now.
        async with get_db_session() as session:
            stmt = select(Candidate).where(Candidate.id == candidate_id)
            res = await session.execute(stmt)
            candidate = res.scalar_one_or_none()
            if not candidate: raise ValueError("Candidate not found")
            
            notes = list(candidate.notes) if candidate.notes else []
            kwargs["created_at"] = datetime.utcnow().isoformat()
            kwargs["sent_at"] = kwargs.get("sent_at") or kwargs["created_at"]
            kwargs["is_email"] = True
            notes.append(kwargs)
            candidate.notes = notes
            
            await session.commit()
            return kwargs

    # --- Application Operations ---
    async def create_application(self, payload: ApplicationCreate) -> dict:
        async with get_db_session() as session:
            app = Application(**payload.model_dump())
            session.add(app)
            
            stmt = select(Job).where(Job.id == payload.job_id)
            res = await session.execute(stmt)
            job = res.scalar_one_or_none()
            if job:
                job.applications_count += 1
            
            await session.commit()
            await session.refresh(app)
            return model_to_dict(app)

    async def list_applications(self, candidate_id: int | None = None, job_id: int | None = None) -> list[dict]:
        async with get_db_session() as session:
            stmt = select(Application)
            if candidate_id is not None:
                stmt = stmt.where(Application.candidate_id == candidate_id)
            if job_id is not None:
                stmt = stmt.where(Application.job_id == job_id)
            stmt = stmt.order_by(desc(Application.created_at))
            res = await session.execute(stmt)
            return [model_to_dict(a) for a in res.scalars().all()]

    # --- Resume & Upload Operations ---
    async def list_recent_uploads(self, limit: int = 10) -> list[dict]:
        async with get_db_session() as session:
            stmt = select(ResumeData).order_by(desc(ResumeData.created_at)).limit(limit)
            res = await session.execute(stmt)
            from backend.scripts.services.recruitment import _normalize_resume_record
            return [_normalize_resume_record(model_to_dict(u)) for u in res.scalars().all()]

    async def store_resume_record(self, candidate_id: int, filename: str, mime_type: str, file_path: str, parsed: Any, raw_text: str) -> dict:
        async with get_db_session() as session:
            p = parsed.model_dump() if hasattr(parsed, "model_dump") else parsed
            resume = ResumeData(
                candidate_id=candidate_id, filename=filename, mime_type=mime_type, file_path=file_path, extracted_text=raw_text, parsed_json=p,
                name=getattr(parsed, "name", ""), email=getattr(parsed, "email", ""), phone=getattr(parsed, "phone", ""),
                linkedin=getattr(parsed, "linkedin", ""), github=getattr(parsed, "github", ""), portfolio=getattr(parsed, "portfolio", ""),
                education=getattr(parsed, "education", []), skills=getattr(parsed, "skills", []), experience=getattr(parsed, "experience", []),
                projects=getattr(parsed, "projects", []), certifications=getattr(parsed, "certifications", []), languages=getattr(parsed, "languages", []),
                achievements=getattr(parsed, "achievements", []), status="Parsed"
            )
            session.add(resume)
            
            act = Activity(icon="fa-file-arrow-up", title="Resume Uploaded", description=f"Uploaded and parsed {filename}.", time="Just now")
            session.add(act)
            
            await session.commit()
            await session.refresh(resume)
            return model_to_dict(resume)

    async def get_latest_candidate_resume(self, candidate_id: int) -> dict | None:
        async with get_db_session() as session:
            stmt = select(ResumeData).where(ResumeData.candidate_id == candidate_id).order_by(desc(ResumeData.created_at)).limit(1)
            res = await session.execute(stmt)
            return model_to_dict(res.scalar_one_or_none())

    # --- Interview Operations ---
    async def list_interviews(self, candidate_id: int | None = None, job_id: int | None = None, status: str = "All", round_name: str = "All") -> list[dict]:
        async with get_db_session() as session:
            stmt = select(Interview)
            if candidate_id is not None: stmt = stmt.where(Interview.candidate_id == candidate_id)
            if job_id is not None: stmt = stmt.where(Interview.job_id == job_id)
            if status != "All": stmt = stmt.where(Interview.status == status)
            if round_name != "All": stmt = stmt.where(Interview.round == round_name)

            stmt = stmt.order_by(Interview.date, Interview.time)
            res = await session.execute(stmt)
            return [model_to_dict(i) for i in res.scalars().all()]

    async def create_interview(self, payload: dict) -> dict:
        async with get_db_session() as session:
            # Require application_id
            application_id = payload.get("application_id")
            if not application_id:
                raise ValueError("application_id is required to create an interview")
            
            # Validate application exists and is in a valid state
            stmt_app = select(Application).where(Application.id == application_id)
            res_app = await session.execute(stmt_app)
            app = res_app.scalar_one_or_none()
            if not app:
                raise ValueError(f"Application {application_id} not found")
            
            # Check application status allows scheduling interview
            invalid_statuses = ["rejected", "hired", "withdrawn"]
            if app.status in invalid_statuses:
                raise ValueError(f"Cannot schedule interview for application with status '{app.status}'")
            
            iv = Interview(**payload)
            iv.invitation_email_status = "pending"
            session.add(iv)
            await session.flush()
            
            stmt = select(Candidate).where(Candidate.id == iv.candidate_id)
            res = await session.execute(stmt)
            cand = res.scalar_one_or_none()
            if cand: 
                cand.status = "Interview Scheduled"
            
            # Create communication record (upsert-safe: update if exists)
            if cand:
                existing_comm_stmt = (
                    select(Communication)
                    .where(Communication.interview_id == iv.id)
                    .order_by(desc(Communication.id))
                    .limit(1)
                )
                existing_comm_res = await session.execute(existing_comm_stmt)
                existing_comm = existing_comm_res.scalars().first()
                if existing_comm:
                    existing_comm.candidate_id = iv.candidate_id
                    existing_comm.application_id = application_id
                    existing_comm.job_id = iv.job_id
                    existing_comm.recruitment_round = iv.round
                    existing_comm.status = "pending"
                    existing_comm.email = cand.email
                    existing_comm.subject = f"Interview Invitation — {iv.round}"
                else:
                    comm = Communication(
                        candidate_id=iv.candidate_id,
                        application_id=application_id,
                        job_id=iv.job_id,
                        interview_id=iv.id,
                        recruitment_round=iv.round,
                        status="pending",
                        email=cand.email,
                        subject=f"Interview Invitation — {iv.round}",
                        message="",
                    )
                    session.add(comm)
            
            await session.commit()
            await session.refresh(iv)
            return model_to_dict(iv)

    async def get_interview(self, interview_id: int) -> dict | None:
        async with get_db_session() as session:
            stmt = select(Interview).where(Interview.id == interview_id)
            res = await session.execute(stmt)
            return model_to_dict(res.scalar_one_or_none())

    async def update_interview(self, interview_id: int, payload: dict) -> dict:
        async with get_db_session() as session:
            stmt = select(Interview).where(Interview.id == interview_id)
            res = await session.execute(stmt)
            iv = res.scalar_one_or_none()
            if not iv: raise ValueError("Interview not found")
            
            for k, v in payload.items(): setattr(iv, k, v)
            
            iv.invitation_email_status = "pending"
            
            stmt_comm = (
                select(Communication)
                .where(Communication.interview_id == interview_id)
                .order_by(desc(Communication.id))
                .limit(1)
            )
            res_comm = await session.execute(stmt_comm)
            comm = res_comm.scalars().first()
            if comm:
                comm.status = "pending"
                comm.recruitment_round = iv.round
                comm.sent_at = None
                comm.error_message = ""
                comm.generated_at = None
            else:
                stmt_cand = select(Candidate).where(Candidate.id == iv.candidate_id)
                res_cand = await session.execute(stmt_cand)
                cand = res_cand.scalar_one_or_none()
                
                stmt_app = (
                    select(Application)
                    .where(Application.candidate_id == iv.candidate_id, Application.job_id == iv.job_id)
                    .order_by(desc(Application.id))
                    .limit(1)
                )
                res_app = await session.execute(stmt_app)
                app = res_app.scalars().first()
                app_id = app.id if app else None
                if not app_id:
                    stmt_app_fallback = (
                        select(Application)
                        .where(Application.candidate_id == iv.candidate_id)
                        .order_by(desc(Application.id))
                        .limit(1)
                    )
                    res_app_fallback = await session.execute(stmt_app_fallback)
                    app_fallback = res_app_fallback.scalars().first()
                    app_id = app_fallback.id if app_fallback else None
                
                if app_id and cand:
                    new_comm = Communication(
                        candidate_id=iv.candidate_id,
                        application_id=app_id,
                        job_id=iv.job_id,
                        interview_id=iv.id,
                        recruitment_round=iv.round,
                        status="pending",
                        email=cand.email,
                        subject=f"Interview Invitation — {iv.round}",
                        message=""
                    )
                    session.add(new_comm)
                    
            await session.commit()
            await session.refresh(iv)
            return model_to_dict(iv)

    async def update_interview_status(self, interview_id: int, status: str) -> dict:
        async with get_db_session() as session:
            stmt = select(Interview).where(Interview.id == interview_id)
            res = await session.execute(stmt)
            iv = res.scalar_one_or_none()
            if not iv: raise ValueError("Interview not found")
            iv.status = status
            
            if status in ("Completed", "Cancelled") and iv.candidate_id:
                c_stmt = select(Candidate).where(Candidate.id == iv.candidate_id)
                c_res = await session.execute(c_stmt)
                cand = c_res.scalar_one_or_none()
                if cand and status == "Completed": cand.status = "Interviewed"
                
            await session.commit()
            await session.refresh(iv)
            return model_to_dict(iv)

    async def add_interview_feedback(self, interview_id: int, feedback: dict) -> dict:
        async with get_db_session() as session:
            stmt = select(Interview).where(Interview.id == interview_id)
            res = await session.execute(stmt)
            iv = res.scalar_one_or_none()
            if not iv: raise ValueError("Interview not found")
            iv.feedback = feedback
            iv.status = "Feedback Logged"
            
            if iv.candidate_id:
                c_stmt = select(Candidate).where(Candidate.id == iv.candidate_id)
                c_res = await session.execute(c_stmt)
                cand = c_res.scalar_one_or_none()
                if cand: cand.status = "Under Review"
                
            await session.commit()
            await session.refresh(iv)
            return model_to_dict(iv)

    async def log_interview_decision(self, interview_id: int, decision: str) -> dict:
        async with get_db_session() as session:
            stmt = select(Interview).where(Interview.id == interview_id)
            res = await session.execute(stmt)
            iv = res.scalar_one_or_none()
            if not iv: raise ValueError("Interview not found")
            iv.decision = decision
            iv.status = "Completed"
            
            if iv.candidate_id:
                c_stmt = select(Candidate).where(Candidate.id == iv.candidate_id)
                c_res = await session.execute(c_stmt)
                cand = c_res.scalar_one_or_none()
                if cand:
                    if decision == "Selected": cand.status = "Hired"
                    elif decision == "Rejected": cand.status = "Rejected"
                    elif decision == "Next Round": cand.status = "Interviewing"
                    
            await session.commit()
            await session.refresh(iv)
            return model_to_dict(iv)

    # --- Employee Operations ---
    async def list_employees(self, search: str = "", department: str = "All", designation: str = "All", status: str = "All", limit: int = 100, offset: int = 0) -> list[dict]:
        async with get_db_session() as session:
            stmt = select(Employee)
            if search:
                like = f"%{search}%"
                stmt = stmt.where(or_(Employee.name.ilike(like), Employee.email.ilike(like)))
            if department != "All": stmt = stmt.where(Employee.department == department)
            if designation != "All": stmt = stmt.where(Employee.designation == designation)
            if status != "All": stmt = stmt.where(Employee.status == status)
            
            stmt = stmt.order_by(desc(Employee.joining_date)).offset(offset).limit(limit)
            res = await session.execute(stmt)
            return [model_to_dict(e) for e in res.scalars().all()]

    async def get_employee(self, employee_id: int) -> dict | None:
        async with get_db_session() as session:
            stmt = select(Employee).where(Employee.id == employee_id)
            res = await session.execute(stmt)
            return model_to_dict(res.scalar_one_or_none())

    async def get_employee_by_candidate_id(self, candidate_id: int) -> dict | None:
        async with get_db_session() as session:
            stmt = (
                select(Employee)
                .where(Employee.candidate_id == candidate_id)
                .order_by(desc(Employee.id))
                .limit(1)
            )
            res = await session.execute(stmt)
            return model_to_dict(res.scalars().first())

    async def employee_exists(self, candidate_id: int) -> bool:
        emp = await self.get_employee_by_candidate_id(candidate_id)
        return emp is not None

    async def create_employee(self, payload: dict) -> dict:
        async with get_db_session() as session:
            emp = Employee(**payload)
            session.add(emp)
            
            act = Activity(icon="fa-user-tie", title="New Employee Onboarded", description=f"{emp.name} joined as {emp.designation or 'Employee'}.", time="Just now")
            session.add(act)
            
            await session.commit()
            await session.refresh(emp)
            return model_to_dict(emp)

    async def update_employee(self, employee_id: int, payload: dict) -> dict:
        async with get_db_session() as session:
            stmt = select(Employee).where(Employee.id == employee_id)
            res = await session.execute(stmt)
            emp = res.scalar_one_or_none()
            if not emp: raise ValueError("Employee not found")
            
            for k, v in payload.items(): setattr(emp, k, v)
            await session.commit()
            await session.refresh(emp)
            return model_to_dict(emp)

    async def update_employee_skills(self, employee_id: int, skills: list[dict]) -> dict:
        async with get_db_session() as session:
            stmt = select(Employee).where(Employee.id == employee_id)
            res = await session.execute(stmt)
            emp = res.scalar_one_or_none()
            if not emp: raise ValueError("Employee not found")
            emp.skills = skills
            await session.commit()
            await session.refresh(emp)
            return model_to_dict(emp)

    async def add_employee_project(self, employee_id: int, project: dict) -> dict:
        async with get_db_session() as session:
            stmt = select(Employee).where(Employee.id == employee_id)
            res = await session.execute(stmt)
            emp = res.scalar_one_or_none()
            if not emp: raise ValueError("Employee not found")
            
            projs = list(emp.projects) if emp.projects else []
            new_id = max([p.get("id", 0) for p in projs]) + 1 if projs else 1
            project["id"] = new_id
            projs.append(project)
            emp.projects = projs
            
            await session.commit()
            return project

    async def update_employee_project(self, employee_id: int, project_id: int, payload: dict) -> dict:
        async with get_db_session() as session:
            stmt = select(Employee).where(Employee.id == employee_id)
            res = await session.execute(stmt)
            emp = res.scalar_one_or_none()
            if not emp: raise ValueError("Employee not found")
            
            projs = list(emp.projects) if emp.projects else []
            for p in projs:
                if p.get("id") == project_id:
                    for k, v in payload.items(): p[k] = v
                    break
            emp.projects = projs
            
            await session.commit()
            return payload

    async def add_employee_performance(self, employee_id: int, performance: dict) -> dict:
        async with get_db_session() as session:
            stmt = select(Employee).where(Employee.id == employee_id)
            res = await session.execute(stmt)
            emp = res.scalar_one_or_none()
            if not emp: raise ValueError("Employee not found")
            
            perfs = list(emp.performance_history) if emp.performance_history else []
            new_id = max([p.get("id", 0) for p in perfs]) + 1 if perfs else 1
            performance["id"] = new_id
            perfs.append(performance)
            emp.performance_history = perfs
            
            await session.commit()
            return performance

    async def update_candidate_screening_result(
        self, candidate_id: int, status: str, score: int
    ) -> dict:
        async with get_db_session() as session:
            stmt = select(Candidate).where(Candidate.id == candidate_id)
            res = await session.execute(stmt)
            candidate = res.scalar_one_or_none()
            if not candidate:
                raise ValueError("Candidate not found")
            candidate.status = status
            candidate.match_score = score
            await session.commit()
            await session.refresh(candidate)
            return model_to_dict(candidate)

    async def upsert_application(
        self,
        candidate_id: int,
        job_id: int,
        recommendation: str,
        score: int,
        summary: str = "",
    ) -> dict:
        async with get_db_session() as session:
            stmt = (
                select(Application)
                .where(
                    Application.candidate_id == candidate_id,
                    Application.job_id == job_id,
                )
                .order_by(desc(Application.id))
                .limit(1)
            )
            res = await session.execute(stmt)
            app = res.scalars().first()
            if app:
                app.status = recommendation
                app.match_score = score
                app.ai_summary = summary
            else:
                app = Application(
                    candidate_id=candidate_id,
                    job_id=job_id,
                    status=recommendation,
                    match_score=score,
                    ai_summary=summary,
                )
                session.add(app)
                # Increment job applications count
                job_stmt = select(Job).where(Job.id == job_id)
                job_res = await session.execute(job_stmt)
                job = job_res.scalar_one_or_none()
                if job:
                    job.applications_count = (job.applications_count or 0) + 1
            await session.commit()
            await session.refresh(app)
            return model_to_dict(app)

    async def parse_resume_file(self, file_path: str) -> dict:
        from backend.scripts.services.resume_parser_service import extract_text_from_document
        from pathlib import Path
        raw_text = extract_text_from_document(
            Path(file_path).read_bytes(), Path(file_path).name
        )
        return await self.parse_resume_text(raw_text, Path(file_path).name)

    async def parse_resume_text(
        self, raw_text: str, filename: str = "pasted_resume.txt"
    ) -> dict:
        from backend.scripts.services.resume_parser_service import (
            ollama_resume_parse,
            heuristic_resume_parse,
        )
        parsed = ollama_resume_parse(raw_text)
        return parsed.model_dump()

    async def upsert_candidate_from_resume(
        self, parsed: dict, default_title: str = ""
    ) -> dict:
        async with get_db_session() as session:
            email = parsed.get("email", "")
            stmt = (
                select(Candidate)
                .where(Candidate.email == email)
                .order_by(desc(Candidate.id))
                .limit(1)
            )
            res = await session.execute(stmt)
            candidate = res.scalars().first()
            skill_names = parsed.get("skills", [])
            skills_objs = await self._skill_objects(session, skill_names)
            if not candidate:
                from sqlalchemy import func
                max_id = await session.execute(select(func.max(Candidate.id)))
                new_id = (max_id.scalar() or 0) + 1
                candidate = Candidate(
                    id=new_id,
                    name=parsed.get("name", email.split("@")[0]),
                    email=email,
                    phone=parsed.get("phone", ""),
                    linkedin=parsed.get("linkedin", ""),
                    github=parsed.get("github", ""),
                    portfolio=parsed.get("portfolio", ""),
                    current_title=default_title or "Applicant",
                    years_experience=0,
                    location="Remote",
                    status="Applied",
                    match_score=0,
                    tags=["Imported"],
                    summary="Resume imported and parsed.",
                    skills=skills_objs,
                )
                session.add(candidate)
            else:
                candidate.phone = parsed.get("phone", candidate.phone)
                candidate.linkedin = parsed.get("linkedin", candidate.linkedin)
                candidate.github = parsed.get("github", candidate.github)
                candidate.portfolio = parsed.get("portfolio", candidate.portfolio)
                candidate.skills = skills_objs
            await session.commit()
            await session.refresh(candidate)
            return model_to_dict(candidate)

    async def update_talent_insights(
        self, employee_id: int, insights: dict
    ) -> dict:
        async with get_db_session() as session:
            stmt = select(Employee).where(Employee.id == employee_id)
            res = await session.execute(stmt)
            emp = res.scalar_one_or_none()
            if not emp:
                raise ValueError("Employee not found")
            emp.talent_insights = insights
            await session.commit()
            await session.refresh(emp)
            return model_to_dict(emp)


data_store = RecruitmentDataStore()
