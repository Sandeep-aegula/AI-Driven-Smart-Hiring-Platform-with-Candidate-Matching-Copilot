from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, EmailStr, Field


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
    parsed_json: dict[str, Any] = Field(default_factory=list)


class ResumeParseResponse(BaseModel):
    name: str = ""
    email: str = ""
    phone: str = ""
    linkedin: str = ""
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
    date: str
    time: str
    duration: int = 60
    round: str
    type: str = "Online"
    meeting_platform: str = "Google Meet"
    meeting_link: str = ""
    panel_members: list[str] = Field(default_factory=list)
    recruiter_name: str = ""

    recruiter_name: str = ""


class InterviewRequest(BaseModel):
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
            openings: int = 1
            work_mode: str = "Remote"
            required_skills: list[str] = Field(default_factory=list)
            technical_skills: list[str] = Field(default_factory=list)
            soft_skills: list[str] = Field(default_factory=list)
            qualifications: list[str] = Field(default_factory=list)
            additional_requirements: list[str] = Field(default_factory=list)
            experience_required: str = ""
            salary_range: str = ""
    published_at: datetime | None = None
    created_at: datetime = None
    updated_at: datetime = None


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
    parsed_json: dict[str, Any] = Field(default_factory=list)


class ResumeParseResponse(BaseModel):
    name: str = ""
    email: str = ""
    phone: str = ""
    linkedin: str = ""
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
    date: str
    time: str
    duration: int = 60
    round: str
    type: str = "Online"
    meeting_platform: str = "Google Meet"
    meeting_link: str = ""
    panel_members: list[str] = Field(default_factory=list)
    recruiter_name: str = ""
    instructions: str = ""
    required_documents: list[str] = Field(default_factory=list)
    timezone: str = "UTC"


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


class PublicJobSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    department: str
    location: str
    employment_type: str
    work_mode: str = "Remote"
    experience_required: str = ""
    short_description: str = ""
    deadline: str = ""
    required_skills: list[str] = Field(default_factory=list)


class PublicJobDetail(PublicJobSummary):
    description: str = ""
    responsibilities: list[str] = Field(default_factory=list)
    requirements: list[str] = Field(default_factory=list)
    preferred_skills: list[str] = Field(default_factory=list)
    qualifications: list[str] = Field(default_factory=list)
    benefits: list[str] = Field(default_factory=list)
    openings: int = 1


class PublicApplicationCreate(BaseModel):
    full_name: str
    email: EmailStr
    phone: str
    location: str = ""
    linkedin: str = ""
    portfolio: str = ""
    current_title: str = ""
    years_experience: int = 0
    current_company: str = ""
    github: str = ""
    skills: list[str] = Field(default_factory=list)
    cover_letter: str = ""


class PublicApplicationResponse(BaseModel):
    application_id: int
    candidate_id: int
    job_id: int
    status: str
    message: str


class ApplicationStatusUpdate(BaseModel):
    status: str
    recruiter_notes: str = ""
    reviewed_by: str = ""


class ApplicationSelectRequest(BaseModel):
    reviewed_by: str = "HR"
    selection_note: str = ""


class ApplicationScoreRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    ats_score: int = 0
    skills_score: int = 0
    experience_score: int = 0
    education_score: int = 0
    keyword_score: int = 0
    job_match_score: int = 0
    recommendation: str = "review"
    strengths: list[str] = Field(default_factory=list)
    gaps: list[str] = Field(default_factory=list)
    scored_at: datetime | None = None


class ResumeParseRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    parser_status: str = "pending"
    extracted_name: str = ""
    extracted_email: str = ""
    extracted_phone: str = ""
    extracted_skills: list[str] = Field(default_factory=list)
    extracted_education: list[str] = Field(default_factory=list)
    extracted_experience: list[str] = Field(default_factory=list)
    extracted_projects: list[str] = Field(default_factory=list)
    extracted_certifications: list[str] = Field(default_factory=list)
    parser_error: str = ""
    parsed_at: datetime | None = None


class HRApplicationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    candidate_id: int
    job_id: int
    status: str
    source: str = ""
    cover_letter: str = ""
    applied_at: datetime | None = None
    reviewed_at: datetime | None = None
    reviewed_by: str = ""
    recruiter_notes: str = ""
    candidate_name: str = ""
    candidate_email: str = ""
    job_title: str = ""
    job_department: str = ""
    resume_filename: str = ""
    parser_status: str = "pending"
    score: ApplicationScoreRead | None = None
    parse_result: ResumeParseRead | None = None