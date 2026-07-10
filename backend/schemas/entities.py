from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class SkillRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    category: str


class JobBase(BaseModel):
    title: str
    department: str
    location: str = "Remote"
    experience_min: int = 0
    experience_max: int = 0
    salary_min: int = 0
    salary_max: int = 0
    employment_type: str = "Full-time"
    hiring_manager: str = ""
    deadline: str = ""
    status: str = "Active"
    description: str = ""
    responsibilities: list[str] = Field(default_factory=list)
    requirements: list[str] = Field(default_factory=list)
    preferred_skills: list[str] = Field(default_factory=list)
    nice_to_have_skills: list[str] = Field(default_factory=list)
    benefits: list[str] = Field(default_factory=list)


class JobCreate(JobBase):
    pass


class JobRead(JobBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    applications_count: int = 0
    created_at: datetime | None = None
    updated_at: datetime | None = None
    skills: list[SkillRead] = Field(default_factory=list)


class CandidateBase(BaseModel):
    name: str
    email: str
    phone: str = ""
    linkedin: str = ""
    github: str = ""
    portfolio: str = ""
    current_title: str = ""
    years_experience: int = 0
    location: str = ""
    status: str = "New"
    match_score: int = 0
    tags: list[str] = Field(default_factory=list)
    summary: str = ""


class CandidateCreate(CandidateBase):
    pass


class CandidateRead(CandidateBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    notes: list[dict[str, Any]] = Field(default_factory=list)
    avatar_url: str = ""
    created_at: datetime | None = None
    updated_at: datetime | None = None
    skills: list[SkillRead] = Field(default_factory=list)


class ApplicationCreate(BaseModel):
    candidate_id: int
    job_id: int
    status: str = "Applied"
    match_score: int = 0
    ai_summary: str = ""
    recruiter_notes: str = ""


class ApplicationRead(ApplicationCreate):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime | None = None
    updated_at: datetime | None = None


class ResumeUploadResponse(BaseModel):
    id: int
    candidate_id: int
    filename: str
    status: str
    parsed_json: dict[str, Any] = Field(default_factory=dict)


class ResumeParseResponse(BaseModel):
    name: str = ""
    email: str = ""
    phone: str = ""
    linkedin: str = ""
    github: str = ""
    portfolio: str = ""
    education: list[str] = Field(default_factory=list)
    skills: list[str] = Field(default_factory=list)
    experience: list[str] = Field(default_factory=list)
    projects: list[str] = Field(default_factory=list)
    certifications: list[str] = Field(default_factory=list)
    languages: list[str] = Field(default_factory=list)
    achievements: list[str] = Field(default_factory=list)
    extracted_text: str = ""


class ScreeningResponse(BaseModel):
    candidate_id: int
    job_id: int
    resume_summary: str
    skill_match: int
    experience_match: int
    education_match: int
    projects_match: int
    strengths: list[str]
    weaknesses: list[str]
    missing_skills: list[str]
    overall_recommendation: str
    overall_match_percent: int
    explanation: str
    radar: dict[str, int]
