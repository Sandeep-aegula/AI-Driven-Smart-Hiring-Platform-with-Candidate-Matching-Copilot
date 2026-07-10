from __future__ import annotations

from datetime import datetime
from enum import Enum

from sqlalchemy import Column, DateTime, ForeignKey, Integer, JSON, String, Table, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.database.base import Base


class JobStatus(str, Enum):
    open = "Open"
    active = "Active"
    paused = "Paused"
    archived = "Archived"


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
    applications_count: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    skills: Mapped[list[Skill]] = relationship(secondary=job_skills, lazy="selectin")


class Candidate(Base):
    __tablename__ = "candidates"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    email: Mapped[str] = mapped_column(String(255), nullable=False, unique=True, index=True)
    phone: Mapped[str] = mapped_column(String(80), default="")
    linkedin: Mapped[str] = mapped_column(String(255), default="")
    github: Mapped[str] = mapped_column(String(255), default="")
    portfolio: Mapped[str] = mapped_column(String(255), default="")
    current_title: Mapped[str] = mapped_column(String(200), default="")
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
    resumes: Mapped[list["ResumeData"]] = relationship(back_populates="candidate", cascade="all, delete-orphan")
    applications: Mapped[list["Application"]] = relationship(back_populates="candidate", cascade="all, delete-orphan")


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
    status: Mapped[str] = mapped_column(String(50), default=ApplicationStatus.applied.value, index=True)
    match_score: Mapped[int] = mapped_column(Integer, default=0)
    ai_summary: Mapped[str] = mapped_column(Text, default="")
    recruiter_notes: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    candidate: Mapped[Candidate] = relationship(back_populates="applications")
