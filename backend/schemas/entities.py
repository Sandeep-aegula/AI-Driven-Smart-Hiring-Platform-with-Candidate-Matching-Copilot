from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from backend.models.entities import OnboardingDocumentStatus, OnboardingStatus


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
    
    # New fields for Job Management module
    openings: int = 1
    work_mode: str = "Remote"
    required_skills: list[str] = Field(default_factory=list)
    technical_skills: list[str] = Field(default_factory=list)
    soft_skills: list[str] = Field(default_factory=list)
    qualifications: list[str] = Field(default_factory=list)
    additional_requirements: list[str] = Field(default_factory=list)
    experience_required: str = ""
    salary_range: str = ""

class AIGeneratedJobDraft(BaseModel):
    required_skills: list[str] = Field(default_factory=list)
    preferred_skills: list[str] = Field(default_factory=list)
    experience_required: str = ""
    education_requirements: str = ""
    responsibilities: list[str] = Field(default_factory=list)
    qualifications: list[str] = Field(default_factory=list)
    job_description: str = ""


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
    skill_match_breakdown: dict = Field(default_factory=dict)
    hire_recommendation: str = ""
    tags: list[str] = Field(default_factory=list)
    summary: str = ""


class BatchUploadStatus(BaseModel):
    batch_id: str
    total_files: int
    processed_files: int
    successful: int
    failed: int
    is_complete: bool


class ResumeDraftResponse(BaseModel):
    candidate_id: int
    raw_text: str
    parsed_json: dict


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

class CompareCandidatesRequest(BaseModel):
    candidate_ids: list[int]
    job_id: int


class CommunicationDraftRequest(BaseModel):
    candidate_id: int
    email_type: str
    job_id: int | None = None
    interview_id: int | None = None
    sender_name: str = ""
    reply_to_email: str = ""


class CommunicationDraftGenerateRequest(BaseModel):
    regenerate: bool = False


class CommunicationDraftUpdateRequest(BaseModel):
    subject: str
    body: str


class CommunicationBulkDraftRequest(BaseModel):
    communication_ids: list[int] = Field(default_factory=list)
    regenerate: bool = False


class CommunicationDraftResponse(BaseModel):
    communication_id: int
    interview_id: int
    candidate_id: int
    candidate_name: str
    recipient_email: str
    subject: str
    body: str
    status: str
    generated_at: str
    job_id: int | None = None
    job_title: str = ""
    round_name: str = ""
    interview_mode: str = ""
    interview_date: str = ""
    interview_time: str = ""
    timezone: str = ""


class CommunicationSendRequest(BaseModel):
    candidate_id: int
    subject: str
    body: str
    email_type: str
    decision: str
    interview_id: int | None = None
    sender_name: str = ""
    reply_to_email: str = ""


class EmailDraftRequest(BaseModel):
    email_type: str
    job_id: int


class EmailSendRequest(BaseModel):
    subject: str
    body: str


class EmailRecord(BaseModel):
    id: int
    subject: str
    body: str
    status: str
    sent_at: str
    email_type: str = ""
    decision: str = ""
    interview_id: int | None = None
    job_id: int | None = None
    job_title: str = ""
    round_name: str = ""
    sender_name: str = ""
    reply_to_email: str = ""
    draft_saved: bool = False
from pydantic import field_validator
from typing import Literal


class InterviewDecisionRequest(BaseModel):
    decision: Literal["selected", "rejected", "hold", "next_round"]
    feedback: dict | None = None
    notes: str | None = None

    @field_validator("decision", mode="before")
    @classmethod
    def normalize_decision(cls, v):
        if isinstance(v, str):
            return v.strip().lower().replace(" ", "_")
        return v


class InterviewDecisionResponse(BaseModel):
    interview_id: int
    application_id: int
    decision: str
    status: str
    onboarding_id: int | None = None
    communication_id: int | None = None
    next_interview_id: int | None = None
    model_config = ConfigDict(from_attributes=True)


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

class InterviewCreate(BaseModel):
    candidate_id: int
    job_id: int
    application_id: int
    date: str
    time: str
    timezone: str = "UTC"
    duration: int = 60
    round: str
    instructions: str = ""
    type: str = "Online"
    meeting_platform: str = "Google Meet"
    meeting_link: str = ""
    location: str | None = None
    interviewer_designation: str = ""
    invitation_email_status: str = "pending"
    panel_members: list[str] = Field(default_factory=list)
    recruiter_name: str = ""



class InterviewFeedback(BaseModel):
    technical_evaluation: int = 0
    communication_rating: int = 0
    coding_assessment: int = 0
    problem_solving: int = 0
    behavioral_assessment: int = 0
    overall_performance: str = ""
    recruiter_comments: str = ""
    interview_notes: str = ""
    final_score: int = 0


class InterviewQuestionsRequest(BaseModel):
    round_type: str | None = None
    difficulty_level: str
    number_of_questions: int = Field(ge=1, le=15)
    regenerate: bool = False


class InterviewQuestion(BaseModel):
    question: str
    model_answer: str
    evaluation_guideline: str


class InterviewQuestionsResponse(BaseModel):
    questions: list[InterviewQuestion]
    cached: bool = False
    warning: str | None = None


class InterviewEmailDraftRequest(BaseModel):
    email_mode: str


class ProjectRecord(BaseModel):
    id: int = 0
    name: str
    client: str = ""
    description: str = ""
    role: str = ""
    team_size: int = 0
    tech_stack: list[str] = Field(default_factory=list)
    start_date: str = ""
    end_date: str = ""
    status: str = "Active"
    responsibilities: str = ""
    outcome: str = ""

class PerformanceRecord(BaseModel):
    id: int = 0
    month: str
    year: int
    kpi_score: int
    productivity_score: int
    completion_rate: int
    attendance_rate: int
    notes: str = ""

class SkillUpdate(BaseModel):
    name: str
    proficiency: int = 50
    status: str = "Acquired"  # Acquired, Under Training

class EmployeeBase(BaseModel):
    name: str
    email: str
    phone: str = ""
    department: str = ""
    designation: str = ""
    joining_date: str = ""
    status: str = "Active"
    work_location: str = "Remote"
    reporting_manager: str = ""
    current_project: str = ""
    avatar_url: str = ""
    skills: list[SkillUpdate] = Field(default_factory=list)
    projects: list[ProjectRecord] = Field(default_factory=list)
    performance_history: list[PerformanceRecord] = Field(default_factory=list)
    talent_insights: dict = Field(default_factory=dict)
    notes: list[dict] = Field(default_factory=list)
    resume_id: int | None = None
    candidate_id: int | None = None
    application_id: int | None = None
    job_id: int | None = None
    onboarding_id: int | None = None


class OnboardingDocumentBase(BaseModel):
    original_filename: str
    stored_filename: str
    storage_path: str
    mime_type: str | None = None
    file_size: int
    status: OnboardingDocumentStatus
    rejection_reason: str | None = None
    reupload_message: str | None = None
    is_current: bool = True


class OnboardingDocumentCreate(OnboardingDocumentBase):
    onboarding_id: int
    requirement_id: int


class OnboardingDocumentRead(OnboardingDocumentBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    version: int
    uploaded_at: datetime
    verified_at: datetime | None = None
    verified_by: str | None = None
    rejected_at: datetime | None = None
    rejected_by: str | None = None


class OnboardingDocumentRequirementBase(BaseModel):
    document_type: str
    document_name: str
    required: bool = True
    display_order: int = 0


class OnboardingDocumentRequirementCreate(OnboardingDocumentRequirementBase):
    onboarding_id: int


class OnboardingDocumentRequirementRead(OnboardingDocumentRequirementBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    documents: list[OnboardingDocumentRead] = Field(default_factory=list)


class OnboardingBase(BaseModel):
    department: str
    designation: str
    joining_date: str
    status: OnboardingStatus
    selected_at: datetime | None = None
    ready_for_onboarding: bool = False


class OnboardingCreate(OnboardingBase):
    candidate_id: int
    application_id: int
    job_id: int


class OnboardingRead(OnboardingBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    candidate: CandidateRead
    job: JobRead
    document_requirements: list[OnboardingDocumentRequirementRead] = Field(default_factory=list)
    application_id: int | None = None
    created_at: datetime
    updated_at: datetime
    completed_at: datetime | None = None
    completed_at: datetime | None = None
