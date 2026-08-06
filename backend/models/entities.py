from __future__ import annotations

from datetime import datetime
from enum import Enum

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, JSON, String, Table, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.database.base import Base


class JobStatus(str, Enum):
    draft = "draft"
    published = "published"
    paused = "paused"
    closed = "closed"
    # Legacy values kept for backward compatibility with existing rows.
    open = "Open"
    active = "Active"
    paused_legacy = "Paused"
    archived = "Archived"


class ApplicationWorkflowStatus(str, Enum):
    submitted = "submitted"
    parsing = "parsing"
    parsed = "parsed"
    under_review = "under_review"
    shortlisted = "shortlisted"
    rejected = "rejected"
    interview = "interview"
    hired = "hired"
    withdrawn = "withdrawn"


class CandidateStatus(str, Enum):
    new = "New"
    applied = "Applied"
    shortlisted = "Shortlisted"
    interview = "Interview Scheduled"
    rejected = "Rejected"
    hired = "Hired"
    approved = "Approved"


class ResumeStatus(str, Enum):
    uploaded = "Uploaded"
    parsed = "Parsed"
    reviewed = "Reviewed"


class ApplicationStatus(str, Enum):
    applied = "Applied"
    screening = "Screening"
    shortlisted = "Shortlisted"
    interview = "Interview Scheduled"
    rejected = "Rejected"
    approved = "Approved"


job_skills = Table(
    "job_skills",
    Base.metadata,
    Column("job_id", ForeignKey("jobs.id", ondelete="CASCADE"), primary_key=True),
    Column("skill_id", ForeignKey("skills.id", ondelete="CASCADE"), primary_key=True),
)

candidate_skills = Table(
    "candidate_skills",
    Base.metadata,
    Column("candidate_id", ForeignKey("candidates.id", ondelete="CASCADE"), primary_key=True),
    Column("skill_id", ForeignKey("skills.id", ondelete="CASCADE"), primary_key=True),
)


class Skill(Base):
    __tablename__ = "skills"
    __table_args__ = (UniqueConstraint("name", name="uq_skill_name"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    category: Mapped[str] = mapped_column(String(80), nullable=False, default="General")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Job(Base):
    __tablename__ = "jobs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    department: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    location: Mapped[str] = mapped_column(String(120), nullable=False, default="Remote")
    experience_min: Mapped[int] = mapped_column(Integer, default=0)
    experience_max: Mapped[int] = mapped_column(Integer, default=0)
    salary_min: Mapped[int] = mapped_column(Integer, default=0)
    salary_max: Mapped[int] = mapped_column(Integer, default=0)
    employment_type: Mapped[str] = mapped_column(String(80), default="Full-time")
    hiring_manager: Mapped[str] = mapped_column(String(120), default="")
    deadline: Mapped[str] = mapped_column(String(50), default="")
    status: Mapped[str] = mapped_column(String(50), default=JobStatus.active.value, index=True)
    description: Mapped[str] = mapped_column(Text, default="")
    responsibilities: Mapped[list[str]] = mapped_column(JSON, default=list)
    requirements: Mapped[list[str]] = mapped_column(JSON, default=list)
    preferred_skills: Mapped[list[str]] = mapped_column(JSON, default=list)
    nice_to_have_skills: Mapped[list[str]] = mapped_column(JSON, default=list)
    benefits: Mapped[list[str]] = mapped_column(JSON, default=list)
    openings: Mapped[int] = mapped_column(Integer, default=1)
    work_mode: Mapped[str] = mapped_column(String(50), default="Remote")
    required_skills: Mapped[list[str]] = mapped_column(JSON, default=list)
    technical_skills: Mapped[list[str]] = mapped_column(JSON, default=list)
    soft_skills: Mapped[list[str]] = mapped_column(JSON, default=list)
    qualifications: Mapped[list[str]] = mapped_column(JSON, default=list)
    additional_requirements: Mapped[list[str]] = mapped_column(JSON, default=list)
    experience_required: Mapped[str] = mapped_column(String(120), default="")
    salary_range: Mapped[str] = mapped_column(String(120), default="")
    applications_count: Mapped[int] = mapped_column(Integer, default=0)
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    interview_rounds: Mapped[int] = mapped_column(Integer, default=1)

    skills: Mapped[list[Skill]] = relationship(secondary=job_skills, lazy="selectin")


class Candidate(Base):
    __tablename__ = "candidates"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    email: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    phone: Mapped[str] = mapped_column(String(80), default="")
    linkedin: Mapped[str] = mapped_column(String(255), default="")
    github: Mapped[str] = mapped_column(String(255), default="")
    portfolio: Mapped[str] = mapped_column(String(255), default="")
    current_title: Mapped[str] = mapped_column(String(200), default="")
    current_company: Mapped[str] = mapped_column(String(200), default="")
    years_experience: Mapped[int] = mapped_column(Integer, default=0)
    location: Mapped[str] = mapped_column(String(120), default="")
    status: Mapped[str] = mapped_column(String(50), default=CandidateStatus.new.value, index=True)
    match_score: Mapped[int] = mapped_column(Integer, default=0)
    tags: Mapped[list[str]] = mapped_column(JSON, default=list)
    notes: Mapped[list[dict]] = mapped_column(JSON, default=list)
    avatar_url: Mapped[str] = mapped_column(String(255), default="")
    summary: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    skills: Mapped[list[Skill]] = relationship(secondary=candidate_skills, lazy="selectin")
    resumes: Mapped[list["ResumeData"]] = relationship(back_populates="candidate", cascade="all, delete-orphan", lazy="selectin")
    applications: Mapped[list["Application"]] = relationship(back_populates="candidate", cascade="all, delete-orphan", lazy="selectin")


class ResumeData(Base):
    __tablename__ = "resume_data"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    candidate_id: Mapped[int] = mapped_column(ForeignKey("candidates.id", ondelete="CASCADE"), nullable=False, index=True)
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    mime_type: Mapped[str] = mapped_column(String(120), default="")
    file_path: Mapped[str] = mapped_column(String(500), default="")
    extracted_text: Mapped[str] = mapped_column(Text, default="")
    parsed_json: Mapped[dict] = mapped_column(JSON, default=dict)
    name: Mapped[str] = mapped_column(String(200), default="")
    email: Mapped[str] = mapped_column(String(255), default="")
    phone: Mapped[str] = mapped_column(String(80), default="")
    linkedin: Mapped[str] = mapped_column(String(255), default="")
    github: Mapped[str] = mapped_column(String(255), default="")
    portfolio: Mapped[str] = mapped_column(String(255), default="")
    education: Mapped[list[str]] = mapped_column(JSON, default=list)
    skills: Mapped[list[str]] = mapped_column(JSON, default=list)
    experience: Mapped[list[str]] = mapped_column(JSON, default=list)
    projects: Mapped[list[str]] = mapped_column(JSON, default=list)
    certifications: Mapped[list[str]] = mapped_column(JSON, default=list)
    languages: Mapped[list[str]] = mapped_column(JSON, default=list)
    achievements: Mapped[list[str]] = mapped_column(JSON, default=list)
    status: Mapped[str] = mapped_column(String(50), default=ResumeStatus.uploaded.value)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    candidate: Mapped[Candidate] = relationship(back_populates="resumes")


class Application(Base):
    __tablename__ = "applications"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    candidate_id: Mapped[int] = mapped_column(ForeignKey("candidates.id", ondelete="CASCADE"), nullable=False, index=True)
    job_id: Mapped[int] = mapped_column(ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(50), default=ApplicationWorkflowStatus.submitted.value, index=True)
    current_stage: Mapped[str] = mapped_column(String(100), default="Applied")
    source: Mapped[str] = mapped_column(String(80), default="careers_page")
    cover_letter: Mapped[str] = mapped_column(Text, default="")
    match_score: Mapped[int] = mapped_column(Integer, default=0)
    ai_summary: Mapped[str] = mapped_column(Text, default="")
    recruiter_notes: Mapped[str] = mapped_column(Text, default="")
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    reviewed_by: Mapped[str] = mapped_column(String(200), default="")
    final_decision: Mapped[str] = mapped_column(String(50), default="")
    final_decision_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    final_selected_by: Mapped[str] = mapped_column(String(200), default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    candidate: Mapped[Candidate] = relationship(back_populates="applications")
    job: Mapped[Job] = relationship(lazy="selectin")
    resumes: Mapped[list["Resume"]] = relationship(back_populates="application", cascade="all, delete-orphan", lazy="selectin")
    parse_results: Mapped[list["ResumeParseResult"]] = relationship(back_populates="application", cascade="all, delete-orphan", lazy="selectin")
    scores: Mapped[list["ApplicationScore"]] = relationship(back_populates="application", cascade="all, delete-orphan", lazy="selectin")


class Resume(Base):
    __tablename__ = "resumes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    application_id: Mapped[int] = mapped_column(ForeignKey("applications.id", ondelete="CASCADE"), nullable=False, index=True)
    candidate_id: Mapped[int] = mapped_column(ForeignKey("candidates.id", ondelete="CASCADE"), nullable=False, index=True)
    original_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    stored_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    storage_path: Mapped[str] = mapped_column(String(500), nullable=False)
    mime_type: Mapped[str] = mapped_column(String(120), default="")
    file_size: Mapped[int] = mapped_column(Integer, default=0)
    file_hash: Mapped[str] = mapped_column(String(64), default="", index=True)
    uploaded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    application: Mapped[Application] = relationship(back_populates="resumes")
    candidate: Mapped[Candidate] = relationship(lazy="selectin")
    parse_results: Mapped[list["ResumeParseResult"]] = relationship(back_populates="resume", cascade="all, delete-orphan", lazy="selectin")


class ResumeParseResult(Base):
    __tablename__ = "resume_parse_results"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    resume_id: Mapped[int] = mapped_column(ForeignKey("resumes.id", ondelete="CASCADE"), nullable=False, index=True)
    application_id: Mapped[int] = mapped_column(ForeignKey("applications.id", ondelete="CASCADE"), nullable=False, index=True)
    parser_status: Mapped[str] = mapped_column(String(50), default="pending", index=True)
    raw_text: Mapped[str] = mapped_column(Text, default="")
    parsed_data: Mapped[dict] = mapped_column(JSON, default=dict)
    extracted_name: Mapped[str] = mapped_column(String(200), default="")
    extracted_email: Mapped[str] = mapped_column(String(255), default="")
    extracted_phone: Mapped[str] = mapped_column(String(80), default="")
    extracted_skills: Mapped[list[str]] = mapped_column(JSON, default=list)
    extracted_education: Mapped[list[str]] = mapped_column(JSON, default=list)
    extracted_experience: Mapped[list[str]] = mapped_column(JSON, default=list)
    extracted_projects: Mapped[list[str]] = mapped_column(JSON, default=list)
    extracted_certifications: Mapped[list[str]] = mapped_column(JSON, default=list)
    parser_error: Mapped[str] = mapped_column(Text, default="")
    parsed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    resume: Mapped[Resume] = relationship(back_populates="parse_results")
    application: Mapped[Application] = relationship(back_populates="parse_results")


class ApplicationScore(Base):
    __tablename__ = "application_scores"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    application_id: Mapped[int] = mapped_column(ForeignKey("applications.id", ondelete="CASCADE"), nullable=False, index=True)
    job_id: Mapped[int] = mapped_column(ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False, index=True)
    ats_score: Mapped[int] = mapped_column(Integer, default=0)
    skills_score: Mapped[int] = mapped_column(Integer, default=0)
    experience_score: Mapped[int] = mapped_column(Integer, default=0)
    education_score: Mapped[int] = mapped_column(Integer, default=0)
    keyword_score: Mapped[int] = mapped_column(Integer, default=0)
    job_match_score: Mapped[int] = mapped_column(Integer, default=0)
    recommendation: Mapped[str] = mapped_column(String(50), default="review")
    strengths: Mapped[list[str]] = mapped_column(JSON, default=list)
    gaps: Mapped[list[str]] = mapped_column(JSON, default=list)
    scoring_version: Mapped[str] = mapped_column(String(50), default="v1")
    scoring_error: Mapped[str] = mapped_column(Text, default="")
    scored_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    application: Mapped[Application] = relationship(back_populates="scores")
    job: Mapped[Job] = relationship(lazy="selectin")


class Interview(Base):
    __tablename__ = "interviews"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    candidate_id: Mapped[int] = mapped_column(ForeignKey("candidates.id", ondelete="CASCADE"), nullable=False, index=True)
    job_id: Mapped[int | None] = mapped_column(ForeignKey("jobs.id", ondelete="SET NULL"), nullable=True, index=True)
    date: Mapped[str] = mapped_column(String(50), default="")
    time: Mapped[str] = mapped_column(String(50), default="")
    timezone: Mapped[str] = mapped_column(String(80), default="UTC")
    duration: Mapped[int] = mapped_column(Integer, default=60)
    round: Mapped[str] = mapped_column(String(100), default="")
    instructions: Mapped[str] = mapped_column(Text, default="")
    type: Mapped[str] = mapped_column(String(50), default="Online")
    meeting_platform: Mapped[str] = mapped_column(String(100), default="Google Meet")
    meeting_link: Mapped[str] = mapped_column(String(500), default="")
    location: Mapped[str | None] = mapped_column(String(255), nullable=True)
    interviewer_designation: Mapped[str] = mapped_column(String(120), default="")
    invitation_email_status: Mapped[str] = mapped_column(String(50), default="pending", nullable=False)
    invitation_sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    panel_members: Mapped[list[str]] = mapped_column(JSON, default=list)
    recruiter_name: Mapped[str] = mapped_column(String(100), default="")
    status: Mapped[str] = mapped_column(String(50), default="Scheduled")
    feedback: Mapped[dict] = mapped_column(JSON, default=dict)
    decision: Mapped[str] = mapped_column(String(50), default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    candidate: Mapped[Candidate] = relationship(lazy="selectin")
    job: Mapped[Job | None] = relationship(lazy="selectin")
    application_id: Mapped[int | None] = mapped_column(ForeignKey("applications.id", ondelete="SET NULL"), nullable=True, index=True)
    round_number: Mapped[int] = mapped_column(Integer, default=1)
    interviewer_email: Mapped[str] = mapped_column(String(255), default="")
    application: Mapped[Application | None] = relationship(lazy="selectin")


class Employee(Base):
    __tablename__ = "employees"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    candidate_id: Mapped[int | None] = mapped_column(ForeignKey("candidates.id", ondelete="SET NULL"), nullable=True, index=True)
    application_id: Mapped[int | None] = mapped_column(ForeignKey("applications.id", ondelete="SET NULL"), nullable=True, index=True)
    job_id: Mapped[int | None] = mapped_column(ForeignKey("jobs.id", ondelete="SET NULL"), nullable=True, index=True)
    onboarding_id: Mapped[int | None] = mapped_column(ForeignKey("onboardings.id", ondelete="SET NULL"), nullable=True, index=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    email: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    phone: Mapped[str] = mapped_column(String(80), default="")
    department: Mapped[str] = mapped_column(String(120), default="")
    designation: Mapped[str] = mapped_column(String(120), default="")
    joining_date: Mapped[str] = mapped_column(String(50), default="")
    status: Mapped[str] = mapped_column(String(50), default="Active")
    work_location: Mapped[str] = mapped_column(String(120), default="Remote")
    reporting_manager: Mapped[str] = mapped_column(String(120), default="")
    current_project: Mapped[str] = mapped_column(String(120), default="")
    avatar_url: Mapped[str] = mapped_column(String(255), default="")
    skills: Mapped[list[dict]] = mapped_column(JSON, default=list)
    projects: Mapped[list[dict]] = mapped_column(JSON, default=list)
    performance_history: Mapped[list[dict]] = mapped_column(JSON, default=list)
    talent_insights: Mapped[dict] = mapped_column(JSON, default=dict)
    notes: Mapped[list[dict]] = mapped_column(JSON, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    candidate: Mapped[Candidate | None] = relationship(lazy="selectin")


class Activity(Base):
    __tablename__ = "activities"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    icon: Mapped[str] = mapped_column(String(50), default="")
    title: Mapped[str] = mapped_column(String(200), default="")
    description: Mapped[str] = mapped_column(Text, default="")
    time: Mapped[str] = mapped_column(String(50), default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class OnboardingStatus(str, Enum):
    pending = "Pending"
    documents_uploaded = "Documents Uploaded"
    under_review = "Under Review"
    documents_incomplete = "Documents Incomplete"
    documents_rejected = "Documents Rejected"
    documents_verified = "Documents Verified"
    ready_for_onboarding = "Ready for Onboarding"
    onboarding_completed = "Onboarding Completed"
    ready_for_employee_creation = "Ready for Employee Creation"


class OnboardingDocumentStatus(str, Enum):
    missing = "Missing"
    required = "Required"
    optional = "Optional"
    uploaded = "Uploaded"
    under_review = "Under Review"
    verified = "Verified"
    rejected = "Rejected"
    re_upload_requested = "Re-upload Requested"


class Onboarding(Base):
    __tablename__ = "onboardings"
    __table_args__ = (UniqueConstraint("application_id", name="uq_onboarding_application_id"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    candidate_id: Mapped[int] = mapped_column(ForeignKey("candidates.id", ondelete="CASCADE"), nullable=False, index=True)
    application_id: Mapped[int] = mapped_column(ForeignKey("applications.id", ondelete="CASCADE"), nullable=False, index=True)
    job_id: Mapped[int] = mapped_column(ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False, index=True)
    department: Mapped[str] = mapped_column(String(120), default="")
    designation: Mapped[str] = mapped_column(String(120), default="")
    joining_date: Mapped[str] = mapped_column(String(50), default="")
    selected_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    status: Mapped[str] = mapped_column(String(50), default=OnboardingStatus.pending.value, index=True)
    ready_for_onboarding: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    candidate: Mapped[Candidate] = relationship(lazy="selectin")
    application: Mapped[Application] = relationship(lazy="selectin")
    job: Mapped[Job] = relationship(lazy="selectin")
    document_requirements: Mapped[list["OnboardingDocumentRequirement"]] = relationship(back_populates="onboarding", cascade="all, delete-orphan", lazy="selectin")
    documents: Mapped[list["OnboardingDocument"]] = relationship(back_populates="onboarding", cascade="all, delete-orphan", lazy="selectin")


class OnboardingDocumentRequirement(Base):
    __tablename__ = "onboarding_document_requirements"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    onboarding_id: Mapped[int] = mapped_column(ForeignKey("onboardings.id", ondelete="CASCADE"), nullable=False, index=True)
    document_type: Mapped[str] = mapped_column(String(120), nullable=False)
    document_name: Mapped[str] = mapped_column(String(200), nullable=False)
    required: Mapped[bool] = mapped_column(Boolean, default=True)
    display_order: Mapped[int] = mapped_column(Integer, default=0)
    is_custom: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    onboarding: Mapped[Onboarding] = relationship(back_populates="document_requirements")
    documents: Mapped[list["OnboardingDocument"]] = relationship(back_populates="requirement", cascade="all, delete-orphan", lazy="selectin")


class OnboardingDocument(Base):
    __tablename__ = "onboarding_documents"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    onboarding_id: Mapped[int] = mapped_column(ForeignKey("onboardings.id", ondelete="CASCADE"), nullable=False, index=True)
    requirement_id: Mapped[int] = mapped_column(ForeignKey("onboarding_document_requirements.id", ondelete="CASCADE"), nullable=False, index=True)
    version: Mapped[int] = mapped_column(Integer, default=1)
    original_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    stored_filename: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    storage_path: Mapped[str] = mapped_column(String(500), nullable=False)
    mime_type: Mapped[str] = mapped_column(String(120), default="")
    file_size: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[str] = mapped_column(String(50), default=OnboardingDocumentStatus.uploaded.value, index=True)
    rejection_reason: Mapped[str] = mapped_column(Text, default="")
    reupload_message: Mapped[str] = mapped_column(Text, default="")
    is_current: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    uploaded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    verified_by: Mapped[str] = mapped_column(String(255), default="")
    rejected_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    rejected_by: Mapped[str] = mapped_column(String(255), default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    onboarding: Mapped[Onboarding] = relationship(back_populates="documents")
    requirement: Mapped[OnboardingDocumentRequirement] = relationship(back_populates="documents")


class CommunicationStatus(str, Enum):
    pending = "pending"
    draft = "draft"
    sending = "sending"
    sent = "sent"
    failed = "failed"
    cancelled = "cancelled"
    read = "read"


class Communication(Base):
    __tablename__ = "communications"
    __table_args__ = (UniqueConstraint("interview_id", name="uq_communication_interview_id"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    candidate_id: Mapped[int] = mapped_column(ForeignKey("candidates.id", ondelete="CASCADE"), nullable=False, index=True)
    application_id: Mapped[int] = mapped_column(ForeignKey("applications.id", ondelete="CASCADE"), nullable=False, index=True)
    job_id: Mapped[int] = mapped_column(ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False, index=True)
    interview_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    recruitment_round: Mapped[str] = mapped_column(String(200), default="Initial Screening")
    status: Mapped[str] = mapped_column(String(50), default=CommunicationStatus.pending.value, index=True)
    email: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    subject: Mapped[str] = mapped_column(String(500), default="")
    message: Mapped[str] = mapped_column(Text, default="")
    error_message: Mapped[str] = mapped_column(Text, default="")
    email_template: Mapped[str] = mapped_column(String(100), default="")
    communication_type: Mapped[str] = mapped_column(String(100), default="interview_invitation")
    queued_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    generated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    candidate: Mapped[Candidate] = relationship(lazy="selectin")
    application: Mapped[Application] = relationship(lazy="selectin")
    job: Mapped[Job] = relationship(lazy="selectin")


class HRUser(Base):
    __tablename__ = "hr_users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(String(255), nullable=False, unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())



