"""SQLAlchemy models — import entities to register all tables on Base.metadata."""

import backend.models.entities as entities
from backend.models.entities import (
    Activity,
    Application,
    ApplicationScore,
    ApplicationStatus,
    ApplicationWorkflowStatus,
    Candidate,
    CandidateStatus,
    Employee,
    HRUser,
    Interview,
    Job,
    JobStatus,
    Resume,
    ResumeData,
    ResumeParseResult,
    ResumeStatus,
    Skill,
)
from backend.database.base import Base

__all__ = [
    "Base",
    "entities",
    "Activity",
    "Application",
    "ApplicationScore",
    "ApplicationStatus",
    "ApplicationWorkflowStatus",
    "Candidate",
    "CandidateStatus",
    "Employee",
    "HRUser",
    "Interview",
    "Job",
    "JobStatus",
    "Resume",
    "ResumeData",
    "ResumeParseResult",
    "ResumeStatus",
    "Skill",
]
