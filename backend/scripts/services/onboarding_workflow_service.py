from __future__ import annotations

import logging
from datetime import datetime

from sqlalchemy import select, desc
from sqlalchemy.orm import selectinload

from backend.database.session import get_db_session
from backend.models.entities import (
    Application,
    ApplicationWorkflowStatus,
    Candidate,
    Communication,
    CommunicationStatus,
    Employee,
    Interview,
    Job,
    Onboarding,
    OnboardingDocumentRequirement,
    OnboardingDocumentStatus,
    OnboardingStatus,
)

logger = logging.getLogger(__name__)

DEFAULT_DOCUMENT_TYPES = [
    ("Government ID", "Government ID", True, 1),
    ("Address Proof", "Address Proof", True, 2),
    ("Educational Certificates", "Educational Certificates", True, 3),
    ("Previous Employment Documents", "Previous Employment Documents", False, 4),
    ("Offer Acceptance", "Offer Acceptance Letter", True, 5),
    ("Tax or Payroll Documents", "Tax/PAN/Aadhar Documents", False, 6),
    ("Passport Photograph", "Passport Size Photo", True, 7),
]

FINAL_SELECTION_STATUS = "selected"
FINAL_SELECTION_TIMESTAMP_STATUS = ApplicationWorkflowStatus.hired.value


def _employee_skill_payload(candidate: Candidate) -> list[dict]:
    skills: list[dict] = []
    for skill in candidate.skills or []:
        skill_name = getattr(skill, "name", "") or str(skill)
        if skill_name:
            skills.append({"name": skill_name, "proficiency": 50, "status": "Acquired"})
    return skills


async def _ensure_default_requirements(session, onboarding: Onboarding) -> None:
    existing = await session.execute(
        select(OnboardingDocumentRequirement).where(
            OnboardingDocumentRequirement.onboarding_id == onboarding.id
        )
    )
    existing_requirements = existing.scalars().all()
    existing_types = {req.document_type for req in existing_requirements}

    for doc_type, doc_name, required, order in DEFAULT_DOCUMENT_TYPES:
        if doc_type in existing_types:
            continue
        session.add(
            OnboardingDocumentRequirement(
                onboarding_id=onboarding.id,
                document_type=doc_type,
                document_name=doc_name,
                required=required,
                display_order=order,
                is_custom=False,
            )
        )


async def _latest_interview_for_application(session, application_id: int) -> Interview | None:
    stmt = (
        select(Interview)
        .where(Interview.application_id == application_id)
        .order_by(desc(Interview.round_number), desc(Interview.updated_at), desc(Interview.created_at))
    )
    result = await session.execute(stmt)
    return result.scalars().first()


async def _create_or_get_onboarding(session, application: Application, selected_at: datetime) -> Onboarding:
    existing_onboarding_result = await session.execute(
        select(Onboarding).where(Onboarding.application_id == application.id)
    )
    existing_onboarding = existing_onboarding_result.scalar_one_or_none()

    if existing_onboarding:
        existing_onboarding.selected_at = existing_onboarding.selected_at or selected_at
        existing_onboarding.department = existing_onboarding.department or (application.job.department if application.job else "")
        existing_onboarding.designation = existing_onboarding.designation or (application.job.title if application.job else "")
        existing_onboarding.joining_date = existing_onboarding.joining_date or selected_at.date().isoformat()
        await _ensure_default_requirements(session, existing_onboarding)
        return existing_onboarding

    onboarding = Onboarding(
        candidate_id=application.candidate_id,
        application_id=application.id,
        job_id=application.job_id,
        department=application.job.department if application.job else "",
        designation=application.job.title if application.job else "",
        joining_date=selected_at.date().isoformat(),
        selected_at=selected_at,
        status=OnboardingStatus.pending.value,
        ready_for_onboarding=False,
    )
    session.add(onboarding)
    await session.flush()
    await _ensure_default_requirements(session, onboarding)
    return onboarding


async def _load_onboarding(session, onboarding_id: int) -> Onboarding | None:
    stmt = (
        select(Onboarding)
        .options(
            selectinload(Onboarding.candidate),
            selectinload(Onboarding.application),
            selectinload(Onboarding.job),
            selectinload(Onboarding.document_requirements).selectinload(OnboardingDocumentRequirement.documents),
        )
        .where(Onboarding.id == onboarding_id)
    )
    result = await session.execute(stmt)
    return result.scalar_one_or_none()


async def _load_application(session, application_id: int) -> Application | None:
    stmt = (
        select(Application)
        .options(
            selectinload(Application.candidate),
            selectinload(Application.job),
            selectinload(Application.scores),
        )
        .where(Application.id == application_id)
    )
    result = await session.execute(stmt)
    return result.scalar_one_or_none()


async def select_application_for_onboarding(
    application_id: int,
    selected_by: str = "HR",
    selection_note: str = "",
) -> dict:
    async with get_db_session() as session:
        application = await _load_application(session, application_id)
        if not application:
            raise ValueError("Application not found")

        latest_interview = await _latest_interview_for_application(session, application_id)
        if not latest_interview:
            raise ValueError("Candidate is not eligible for final selection")
        if latest_interview.decision != "Selected":
            raise ValueError("Candidate is not eligible for final selection")
        if latest_interview.status != "Completed":
            raise ValueError("Candidate is not eligible for final selection")

        now = datetime.utcnow()
        application.status = FINAL_SELECTION_TIMESTAMP_STATUS
        application.final_decision = FINAL_SELECTION_STATUS
        application.final_decision_at = now
        application.final_selected_by = selected_by or application.final_selected_by or "HR"
        application.reviewed_at = now
        application.reviewed_by = selected_by or application.reviewed_by or "HR"
        if selection_note:
            application.recruiter_notes = selection_note

        if application.candidate:
            application.candidate.status = "Hired"

        onboarding = await _create_or_get_onboarding(session, application, now)

        await session.commit()

        onboarding = await _load_onboarding(session, onboarding.id)
        return {
            "application_id": application.id,
            "candidate_id": application.candidate_id,
            "job_id": application.job_id,
            "final_decision": application.final_decision,
            "final_decision_at": application.final_decision_at.isoformat() if application.final_decision_at else None,
            "selected_onboarding": {
                "id": onboarding.id if onboarding else None,
                "status": onboarding.status if onboarding else OnboardingStatus.pending.value,
            },
        }


async def record_interview_decision(
    interview_id: int,
    decision: str,
    reviewed_by: str = "HR",
) -> dict:
    async with get_db_session() as session:
        stmt = (
            select(Interview)
            .options(
                selectinload(Interview.application).selectinload(Application.candidate),
                selectinload(Interview.application).selectinload(Application.job),
            )
            .where(Interview.id == interview_id)
        )
        result = await session.execute(stmt)
        interview = result.scalar_one_or_none()
        if not interview:
            raise ValueError("Interview not found")

        application = interview.application
        if not application:
            raise ValueError("Application not found")

        job = application.job
        if not job:
            raise ValueError("Job not found")

        now = datetime.utcnow()
        interview.decision = decision
        interview.status = "Completed"
        
        is_final_round = interview.round_number >= job.interview_rounds

        # Normalize decision for comparison (accept both original and normalized forms)
        normalized_decision = decision.strip().lower().replace(" ", "_") if isinstance(decision, str) else decision
        
        if normalized_decision == "selected":
            if is_final_round:
                application.status = "hired" # Or FINAL_SELECTION_TIMESTAMP_STATUS if that's a constant
                application.current_stage = "Document Verification"
                application.final_decision = "Selected" # Or FINAL_SELECTION_STATUS
                application.final_decision_at = now
                application.final_selected_by = reviewed_by or application.final_selected_by or "HR"
                application.reviewed_at = now
                application.reviewed_by = reviewed_by or application.reviewed_by or "HR"
                if application.candidate:
                    application.candidate.status = "Hired"

                onboarding = await _create_or_get_onboarding(session, application, now)
                
                comm = Communication(
                    candidate_id=application.candidate_id,
                    application_id=application.id,
                    job_id=application.job_id,
                    interview_id=interview.id,
                    recruitment_round="Final Selection",
                    status=CommunicationStatus.pending.value,
                    email=application.candidate.email if application.candidate else "",
                    subject="Congratulations — Offer Letter",
                    message="",
                )
                session.add(comm)
                await session.commit()
                return {
                    "interview_id": interview.id,
                    "application_id": application.id,
                    "decision": decision,
                    "onboarding_id": onboarding.id,
                    "communication_id": comm.id,
                    "status": application.status,
                }
            else:
                application.status = ApplicationWorkflowStatus.interview.value
                application.current_stage = f"Interview Round {interview.round_number + 1}"
                if application.candidate:
                    application.candidate.status = "Interview Scheduled"

                # Automatically create next interview record (as requested or leave pending)
                next_interview = Interview(
                    candidate_id=application.candidate_id,
                    application_id=application.id,
                    job_id=application.job_id,
                    round_number=interview.round_number + 1,
                    round=f"Round {interview.round_number + 1}",
                    status="Scheduled"
                )
                session.add(next_interview)
                await session.flush()
                
                comm = Communication(
                    candidate_id=application.candidate_id,
                    application_id=application.id,
                    job_id=application.job_id,
                    interview_id=next_interview.id,
                    recruitment_round="Next Round",
                    status=CommunicationStatus.pending.value,
                    email=application.candidate.email if application.candidate else "",
                    subject="Interview Invitation — Next Round",
                    message="",
                )
                session.add(comm)
                await session.commit()
                return {
                    "interview_id": interview.id,
                    "application_id": application.id,
                    "decision": decision,
                    "status": application.status,
                    "communication_id": comm.id,
                    "next_interview_id": next_interview.id
                }

        elif normalized_decision == "rejected":
            application.status = "rejected"
            application.final_decision = "rejected"
            application.final_decision_at = now
            application.final_selected_by = reviewed_by or application.final_selected_by or "HR"
            application.reviewed_at = now
            application.reviewed_by = reviewed_by or application.reviewed_by or "HR"
            if application.candidate:
                application.candidate.status = "Rejected"
                
        elif normalized_decision == "next_round":
            application.status = ApplicationWorkflowStatus.interview.value
            application.current_stage = f"Interview Round {interview.round_number + 1}"
            if application.candidate:
                application.candidate.status = "Interview Scheduled"

            next_interview = Interview(
                candidate_id=application.candidate_id,
                application_id=application.id,
                job_id=application.job_id,
                round_number=interview.round_number + 1,
                round=f"Round {interview.round_number + 1}",
                status="Scheduled"
            )
            session.add(next_interview)
            await session.flush()
            
            comm = Communication(
                candidate_id=application.candidate_id,
                application_id=application.id,
                job_id=application.job_id,
                interview_id=next_interview.id,
                recruitment_round="Next Round",
                status=CommunicationStatus.pending.value,
                email=application.candidate.email if application.candidate else "",
                subject="Interview Invitation — Next Round",
                message="",
            )
            session.add(comm)
            await session.commit()
            return {
                "interview_id": interview.id,
                "application_id": application.id,
                "decision": decision,
                "status": application.status,
                "communication_id": comm.id,
                "next_interview_id": next_interview.id
            }

        elif normalized_decision == "hold":
            pass # Stays in current stage, interview is completed.

        await session.commit()
        return {
            "interview_id": interview.id,
            "application_id": application.id,
            "decision": decision,
            "status": application.status,
        }


async def _required_documents_verified(onboarding: Onboarding) -> tuple[bool, int, int]:
    total_required = 0
    verified = 0
    for requirement in onboarding.document_requirements:
        if not requirement.required:
            continue
        total_required += 1
        current_docs = [doc for doc in requirement.documents if doc.is_current]
        if current_docs and current_docs[0].status == OnboardingDocumentStatus.verified.value:
            verified += 1
    return verified > 0 and verified == total_required and total_required > 0, total_required, verified


async def complete_onboarding(onboarding_id: int, completed_by: str = "HR") -> dict:
    async with get_db_session() as session:
        onboarding = await _load_onboarding(session, onboarding_id)
        if not onboarding:
            raise ValueError("Onboarding record not found")

        existing_employee_result = await session.execute(
            select(Employee)
            .where(Employee.onboarding_id == onboarding.id)
            .order_by(desc(Employee.id))
            .limit(1)
        )
        existing_employee = existing_employee_result.scalars().first()

        ready, total_required, verified = await _required_documents_verified(onboarding)
        onboarding.ready_for_onboarding = ready
        if not ready:
            raise ValueError("Required documents are not verified")
        if onboarding.completed_at:
            if existing_employee:
                return {
                    "onboarding_id": onboarding.id,
                    "employee_id": existing_employee.id,
                    "status": onboarding.status,
                    "already_completed": True,
                }
            raise ValueError("Onboarding is already completed")

        if existing_employee:
            onboarding.status = OnboardingStatus.onboarding_completed.value
            onboarding.completed_at = onboarding.completed_at or datetime.utcnow()
            await session.commit()
            return {
                "onboarding_id": onboarding.id,
                "employee_id": existing_employee.id,
                "status": onboarding.status,
                "already_completed": True,
            }

        if not onboarding.candidate or not onboarding.application or not onboarding.job:
            raise ValueError("Onboarding is missing linked candidate, application, or job")

        employee = Employee(
            candidate_id=onboarding.candidate_id,
            application_id=onboarding.application_id,
            job_id=onboarding.job_id,
            onboarding_id=onboarding.id,
            name=onboarding.candidate.name,
            email=onboarding.candidate.email,
            phone=onboarding.candidate.phone,
            department=onboarding.department or onboarding.job.department,
            designation=onboarding.designation or onboarding.job.title,
            joining_date=onboarding.joining_date or datetime.utcnow().date().isoformat(),
            status="Active",
            work_location=onboarding.job.location or "Remote",
            reporting_manager=onboarding.job.hiring_manager or "",
            current_project="",
            avatar_url=onboarding.candidate.avatar_url or "",
            skills=_employee_skill_payload(onboarding.candidate),
            projects=[],
            performance_history=[],
            talent_insights={},
            notes=list(onboarding.candidate.notes or []),
        )
        session.add(employee)
        await session.flush()

        onboarding.status = OnboardingStatus.onboarding_completed.value
        onboarding.completed_at = datetime.utcnow()
        onboarding.ready_for_onboarding = True

        await session.commit()

        return {
            "onboarding_id": onboarding.id,
            "employee_id": employee.id,
            "status": onboarding.status,
            "total_required": total_required,
            "verified": verified,
        }
