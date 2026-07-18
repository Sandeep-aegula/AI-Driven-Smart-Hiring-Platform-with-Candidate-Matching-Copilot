from __future__ import annotations

import json
import logging
import re
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

from backend.ai.ollama_client import OllamaClient
from backend.services.emailer import send_recruiter_decision_email
from backend.schemas.entities import (
    ApplicationCreate,
    CandidateCreate,
    JobCreate,
    ResumeParseResponse,
    ScreeningResponse,
)

logger = logging.getLogger(__name__)

STORAGE_PATH = Path("storage.json")

def load_storage() -> dict[str, list[dict[str, Any]]]:
    if not STORAGE_PATH.exists():
        data = get_seed_data()
        save_storage(data)
        return data
    try:
        with open(STORAGE_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        logger.exception("Failed to load JSON storage. Resetting to seed data.")
        data = get_seed_data()
        save_storage(data)
        return data

def save_storage(data: dict):
    try:
        with open(STORAGE_PATH, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, default=str)
    except Exception:
        logger.exception("Failed to write to JSON storage.")

def _clean_list(values: list[str]) -> list[str]:
    seen = set()
    result = []
    for value in values:
        text = value.strip()
        key = text.lower()
        if text and key not in seen:
            seen.add(key)
            result.append(text)
    return result

def _ensure_list(value: Any) -> list[str]:
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    if isinstance(value, str) and value.strip():
        return [part.strip() for part in re.split(r"[,\nâ€¢;]", value) if part.strip()]
    return []

def get_seed_data() -> dict:
    skills = [
        {"id": 1, "name": "Python", "category": "General"},
        {"id": 2, "name": "FastAPI", "category": "General"},
        {"id": 3, "name": "SQL", "category": "General"},
        {"id": 4, "name": "PostgreSQL", "category": "General"},
        {"id": 5, "name": "Docker", "category": "General"},
        {"id": 6, "name": "Machine Learning", "category": "General"},
        {"id": 7, "name": "React", "category": "General"},
        {"id": 8, "name": "TypeScript", "category": "General"},
        {"id": 9, "name": "Ollama", "category": "General"},
        {"id": 10, "name": "Plotly", "category": "General"},
        {"id": 11, "name": "AgGrid", "category": "General"},
        {"id": 12, "name": "AWS", "category": "General"},
        {"id": 13, "name": "Kubernetes", "category": "General"}
    ]
    
    jobs = [
        {
            "id": 1,
            "title": "Senior Python & ML Engineer",
            "department": "Engineering",
            "location": "Remote",
            "experience_min": 5,
            "experience_max": 10,
            "salary_min": 120000,
            "salary_max": 180000,
            "employment_type": "Full-time",
            "hiring_manager": "Ava Morgan",
            "deadline": (datetime.utcnow() + timedelta(days=21)).date().isoformat(),
            "status": "Active",
            "description": "Build AI-native recruitment workflows and backend services.",
            "responsibilities": ["Design backend services", "Integrate resume parsing", "Collaborate with HR operations"],
            "requirements": ["Python", "FastAPI", "SQLAlchemy", "PostgreSQL"],
            "preferred_skills": ["Ollama", "Streamlit", "Plotly"],
            "nice_to_have_skills": ["Kubernetes", "React"],
            "benefits": ["Full medical/dental/vision coverage", "Flexible working hours & remote work", "Annual learning & development stipend", "401(k) matching plan"],
            "applications_count": 3,
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
            "skills": skills[:7]
        },
        {
            "id": 2,
            "title": "Data Analyst",
            "department": "Analytics",
            "location": "Hybrid",
            "experience_min": 2,
            "experience_max": 5,
            "salary_min": 80000,
            "salary_max": 110000,
            "employment_type": "Full-time",
            "hiring_manager": "Ava Morgan",
            "deadline": (datetime.utcnow() + timedelta(days=14)).date().isoformat(),
            "status": "Active",
            "description": "Help design and construct analytics dashboards and compile recruitment trends.",
            "responsibilities": ["Build SQL queries", "Construct visualization dashboards", "Draft analytics reports"],
            "requirements": ["SQL", "Python", "Tableau"],
            "preferred_skills": ["Plotly", "Excel"],
            "nice_to_have_skills": ["dbt"],
            "benefits": ["Health & wellness reimbursement", "Hybrid office workspace stipend", "Generous PTO & parental leave"],
            "applications_count": 0,
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
            "skills": [skills[0], skills[2]]
        }
    ]

    candidates = [
        {
            "id": 1,
            "name": "Sarah Jenkins",
            "email": "sarah.jenkins@example.com",
            "phone": "+1 (555) 019-2834",
            "linkedin": "https://linkedin.com/in/sarahjenkins",
            "github": "https://github.com/sarahjenkins",
            "portfolio": "https://sarahjenkins.dev",
            "current_title": "Senior Full-Stack Engineer",
            "years_experience": 8,
            "location": "New York, NY",
            "status": "Shortlisted",
            "match_score": 91,
            "tags": ["Full-stack", "Cloud"],
            "notes": [{"author": "Ava Morgan", "note": "Excellent technical review. Move to leadership round.", "created_at": datetime.utcnow().isoformat()}],
            "avatar_url": "",
            "summary": "Senior engineer with strong product delivery and FastAPI experience.",
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
            "skills": skills[:8]
        },
        {
            "id": 2,
            "name": "David Chen",
            "email": "david.chen@example.com",
            "phone": "+1 (555) 024-8192",
            "linkedin": "https://linkedin.com/in/davidchen",
            "github": "https://github.com/davidchen",
            "portfolio": "",
            "current_title": "Data Scientist",
            "years_experience": 4,
            "location": "San Francisco, CA",
            "status": "Interview Scheduled",
            "match_score": 84,
            "tags": ["ML", "NLP"],
            "notes": [{"author": "Ava Morgan", "note": "Strong machine learning basics. Schedule live test.", "created_at": datetime.utcnow().isoformat()}],
            "avatar_url": "",
            "summary": "Machine learning specialist with applied analytics experience.",
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
            "skills": [skills[0], skills[5], skills[8]]
        },
        {
            "id": 3,
            "name": "Emily Taylor",
            "email": "emily.taylor@example.com",
            "phone": "+1 (555) 013-5749",
            "linkedin": "https://linkedin.com/in/emilytaylor",
            "github": "https://github.com/emilytaylor",
            "portfolio": "",
            "current_title": "Backend Developer",
            "years_experience": 5,
            "location": "Austin, TX",
            "status": "Applied",
            "match_score": 78,
            "tags": ["API", "Databases"],
            "notes": [],
            "avatar_url": "",
            "summary": "Backend specialist with strong API design and PostgreSQL experience.",
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
            "skills": skills[:5]
        }
    ]

    applications = [
        {"id": 1, "candidate_id": 1, "job_id": 1, "status": "Shortlisted", "match_score": 91, "ai_summary": "Excellent fit for Python ML role.", "recruiter_notes": "Highly recommend.", "created_at": datetime.utcnow().isoformat(), "updated_at": datetime.utcnow().isoformat()},
        {"id": 2, "candidate_id": 2, "job_id": 1, "status": "Interview Scheduled", "match_score": 84, "ai_summary": "Good ML foundations.", "recruiter_notes": "Needs tech screen.", "created_at": datetime.utcnow().isoformat(), "updated_at": datetime.utcnow().isoformat()},
        {"id": 3, "candidate_id": 3, "job_id": 1, "status": "Applied", "match_score": 78, "ai_summary": "Solid API and SQL skills.", "recruiter_notes": "", "created_at": datetime.utcnow().isoformat(), "updated_at": datetime.utcnow().isoformat()}
    ]

    resume_data = [
        {
            "id": 1,
            "candidate_id": 1,
            "filename": "sarah_jenkins_resume.pdf",
            "mime_type": "application/pdf",
            "file_path": "uploads/sarah_jenkins_resume.pdf",
            "extracted_text": "Sarah Jenkins resume text...",
            "parsed_json": {"source": "seed"},
            "name": "Sarah Jenkins",
            "email": "sarah.jenkins@example.com",
            "phone": "+1 (555) 019-2834",
            "education": ["MS Computer Science - Georgia Tech"],
            "skills": ["Python", "SQL", "FastAPI", "AWS", "React"],
            "experience": ["8 years leading product engineering teams"],
            "projects": ["AI Resume Screener", "Cloud Native SaaS Platform"],
            "certifications": ["AWS Solutions Architect"],
            "languages": ["English"],
            "achievements": ["Led hiring automation at scale"],
            "status": "Parsed",
            "created_at": datetime.utcnow().isoformat()
        }
    ]

    activities = [
        {"icon": "fa-file-lines", "title": "Resume Uploaded", "description": "Sarah Jenkins - Senior Full-Stack Engineer", "time": "10 minutes ago"},
        {"icon": "fa-circle-check", "title": "Candidate Shortlisted", "description": "David Chen - Data Scientist", "time": "2 hours ago"},
        {"icon": "fa-calendar-days", "title": "Interview Scheduled", "description": "Emily Taylor - Backend Developer", "time": "Yesterday"}
    ]

    interviews = [
        {
            "id": 1,
            "candidate_id": 1,
            "candidate_name": "Sarah Jenkins",
            "interviewer": "Ava Morgan",
            "date": "2026-07-11",
            "time": "10:00",
            "stage": "Technical Assessment",
            "meeting_link": "https://meet.google.com/abc-defg-hij",
            "status": "Scheduled",
            "feedback_notes": "",
            "recommendation": "",
            "created_at": datetime.utcnow().isoformat()
        },
        {
            "id": 2,
            "candidate_id": 2,
            "candidate_name": "David Chen",
            "interviewer": "Ava Morgan",
            "date": "2026-07-11",
            "time": "11:30",
            "stage": "HR Culture Fit",
            "meeting_link": "https://meet.google.com/xyz-pdqo-lmn",
            "status": "Scheduled",
            "feedback_notes": "",
            "recommendation": "",
            "created_at": datetime.utcnow().isoformat()
        }
    ]

    employees = [
        {
            "id": 1,
            "name": "Alice Johnson",
            "department": "Engineering",
            "role": "Lead Frontend Engineer",
            "manager": "Marcus Aurelius",
            "joining_date": "2024-03-15",
            "performance_score": 92,
            "skills": [
                {"name": "React", "progress": 95},
                {"name": "TypeScript", "progress": 90},
                {"name": "CSS Grid", "progress": 85}
            ],
            "projects": ["Design System Revamp", "Stripe Checkout Integration"],
            "promotions": ["Senior Engineer (Jan 2025)", "Lead Engineer (Mar 2026)"]
        },
        {
            "id": 2,
            "name": "Bob Chen",
            "department": "Engineering",
            "role": "Senior ML Engineer",
            "manager": "Ava Morgan",
            "joining_date": "2023-11-01",
            "performance_score": 88,
            "skills": [
                {"name": "Python", "progress": 95},
                {"name": "PyTorch", "progress": 90},
                {"name": "Docker", "progress": 80}
            ],
            "projects": ["LLM Screening Pipeline", "Recommendation Engine v2"],
            "promotions": ["ML Engineer II (Jul 2024)", "Senior ML Engineer (Feb 2026)"]
        },
        {
            "id": 3,
            "name": "Charlie Davis",
            "department": "Analytics",
            "role": "Senior Data Analyst",
            "manager": "Sophia Lin",
            "joining_date": "2025-01-10",
            "performance_score": 85,
            "skills": [
                {"name": "SQL", "progress": 90},
                {"name": "Tableau", "progress": 85},
                {"name": "Python", "progress": 75}
            ],
            "projects": ["Recruiter ROI Dashboard", "Funnel Conversion Analytics"],
            "promotions": []
        }
    ]

    return {
        "skills": skills,
        "jobs": jobs,
        "candidates": candidates,
        "applications": applications,
        "resume_data": resume_data,
        "activities": activities,
        "interviews": interviews,
        "employees": employees
    }

def initialize_database() -> None:
    # Ensures storage JSON file exists
    load_storage()

def list_jobs(session: Any = None, search: str = "", department: str = "All", status: str = "All", sort_by: str = "updated_at") -> list[dict]:
    storage = load_storage()
    job_list = storage.get("jobs", [])
    
    if search:
        like = search.lower()
        job_list = [j for j in job_list if like in j["title"].lower() or like in j["department"].lower() or like in j["location"].lower()]
    if department != "All":
        job_list = [j for j in job_list if j["department"] == department]
    if status != "All":
        job_list = [j for j in job_list if j["status"] == status]
        
    # Sort
    reverse = True
    job_list.sort(key=lambda j: j.get(sort_by, j.get("updated_at", "")), reverse=reverse)
    return job_list

def get_job(session: Any = None, job_id: int = 1) -> dict | None:
    storage = load_storage()
    return next((j for j in storage.get("jobs", []) if j["id"] == job_id), None)

def create_job_record(session: Any = None, payload: JobCreate = None) -> dict:
    storage = load_storage()
    jobs = storage.get("jobs", [])
    new_id = max([j["id"] for j in jobs]) + 1 if jobs else 1
    
    # Map preferred skills or requirements to skill objects
    job_skills_names = payload.preferred_skills or payload.requirements
    skills_objs = _skill_objects(None, job_skills_names)
    
    job = {
        "id": new_id,
        "title": payload.title,
        "department": payload.department,
        "location": payload.location,
        "experience_min": payload.experience_min,
        "experience_max": payload.experience_max,
        "salary_min": payload.salary_min,
        "salary_max": payload.salary_max,
        "employment_type": payload.employment_type,
        "hiring_manager": payload.hiring_manager,
        "deadline": payload.deadline,
        "status": payload.status,
        "description": payload.description,
        "responsibilities": payload.responsibilities,
        "requirements": payload.requirements,
        "preferred_skills": payload.preferred_skills,
        "nice_to_have_skills": payload.nice_to_have_skills,
        "benefits": payload.benefits,
        "applications_count": 0,
        "created_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat(),
        "skills": skills_objs
    }
    jobs.append(job)
    storage["jobs"] = jobs
    save_storage(storage)
    return job

def update_job_record(session: Any = None, job_id: int = 1, payload: JobCreate = None) -> dict:
    storage = load_storage()
    jobs = storage.get("jobs", [])
    job = next((j for j in jobs if j["id"] == job_id), None)
    if not job:
        raise ValueError("Job not found")
        
    job_skills_names = payload.preferred_skills or payload.requirements
    skills_objs = _skill_objects(None, job_skills_names)
    
    for key, value in payload.model_dump().items():
        job[key] = value
        
    job["skills"] = skills_objs
    job["updated_at"] = datetime.utcnow().isoformat()
    
    save_storage(storage)
    return job

def archive_job_record(session: Any = None, job_id: int = 1) -> dict:
    storage = load_storage()
    jobs = storage.get("jobs", [])
    job = next((j for j in jobs if j["id"] == job_id), None)
    if not job:
        raise ValueError("Job not found")
    job["status"] = "Archived"
    save_storage(storage)
    return job

def delete_job_record(session: Any = None, job_id: int = 1) -> None:
    storage = load_storage()
    jobs = storage.get("jobs", [])
    storage["jobs"] = [j for j in jobs if j["id"] != job_id]
    save_storage(storage)

def clone_job_record(session: Any = None, job_id: int = 1) -> dict:
    storage = load_storage()
    jobs = storage.get("jobs", [])
    job = next((j for j in jobs if j["id"] == job_id), None)
    if not job:
        raise ValueError("Job not found")
        
    new_id = max([j["id"] for j in jobs]) + 1 if jobs else 1
    clone = {
        **job,
        "id": new_id,
        "title": f"{job['title']} Copy",
        "status": "Active",
        "applications_count": 0,
        "created_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat()
    }
    jobs.append(clone)
    save_storage(storage)
    return clone

def generate_job_description(job: JobCreate) -> dict[str, Any]:
    client = OllamaClient()
    prompt = f"""
Create a professional job description for this role.
Title: {job.title}
Department: {job.department}
Location: {job.location}
Experience: {job.experience_min}-{job.experience_max} years
Salary: {job.salary_min}-{job.salary_max}
Employment Type: {job.employment_type}
Hiring Manager: {job.hiring_manager}
Required Skills: {', '.join(job.requirements)}
Preferred Skills: {', '.join(job.preferred_skills)}
Nice To Have: {', '.join(job.nice_to_have_skills)}
Benefits: {', '.join(job.benefits)}

Return strict JSON with keys: description, responsibilities, requirements, preferred_skills, nice_to_have_skills, benefits.
"""
    try:
        response_text = client.generate(prompt, system="Return concise, production-grade hiring content.", format_json=True)
        data = OllamaClient.parse_json_response(response_text)
        return {
            "description": data.get("description", job.description),
            "responsibilities": _ensure_list(data.get("responsibilities", job.responsibilities)),
            "requirements": _ensure_list(data.get("requirements", job.requirements)),
            "preferred_skills": _ensure_list(data.get("preferred_skills", job.preferred_skills)),
            "nice_to_have_skills": _ensure_list(data.get("nice_to_have_skills", job.nice_to_have_skills)),
            "benefits": _ensure_list(data.get("benefits", job.benefits)),
        }
    except Exception:
        logger.exception("Failed to generate JD from Ollama.")
        return {
            "description": job.description or f"We are looking for a {job.title} to join our {job.department} team.",
            "responsibilities": job.responsibilities or ["Contribute to team projects", "Ensure quality standards"],
            "requirements": job.requirements or ["Relevant experience in engineering"],
            "preferred_skills": job.preferred_skills or [],
            "nice_to_have_skills": job.nice_to_have_skills or [],
            "benefits": job.benefits or ["Health care package", "Paid Time Off (PTO)", "Professional development support"]
        }

def list_candidates(session: Any = None, search: str = "", status: str = "All", skill: str = "All") -> list[dict]:
    storage = load_storage()
    candidates = storage.get("candidates", [])
    
    if search:
        like = search.lower()
        candidates = [c for c in candidates if like in c["name"].lower() or like in c["email"].lower() or like in c.get("current_title", "").lower()]
    if status != "All":
        candidates = [c for c in candidates if c["status"] == status]
    if skill != "All":
        candidates = [c for c in candidates if any(skill.lower() == s.get("name", "").lower() if isinstance(s, dict) else skill.lower() == s.lower() for s in c.get("skills", []))]
        
    candidates.sort(key=lambda c: (c.get("match_score", 0), c.get("updated_at", "")), reverse=True)
    return candidates

def get_candidate(session: Any = None, candidate_id: int = 1) -> dict | None:
    storage = load_storage()
    candidates = storage.get("candidates", [])
    cand = next((c for c in candidates if c["id"] == candidate_id), None)
    if cand:
        # Load related data to match route model expectation
        cand["applications"] = [a for a in storage.get("applications", []) if a["candidate_id"] == candidate_id]
        cand["resumes"] = [r for r in storage.get("resume_data", []) if r["candidate_id"] == candidate_id]
    return cand

def create_candidate_record(session: Any = None, payload: CandidateCreate = None) -> dict:
    storage = load_storage()
    candidates = storage.get("candidates", [])
    new_id = max([c["id"] for c in candidates]) + 1 if candidates else 1
    
    candidate = {
        **payload.model_dump(),
        "id": new_id,
        "notes": [],
        "avatar_url": "",
        "created_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat(),
        "skills": []
    }
    candidates.append(candidate)
    storage["candidates"] = candidates
    save_storage(storage)
    return candidate

def update_candidate_record(session: Any = None, candidate_id: int = 1, payload: CandidateCreate = None) -> dict:
    storage = load_storage()
    candidates = storage.get("candidates", [])
    candidate = next((c for c in candidates if c["id"] == candidate_id), None)
    if not candidate:
        raise ValueError("Candidate not found")
        
    for key, value in payload.model_dump().items():
        candidate[key] = value
        
    candidate["updated_at"] = datetime.utcnow().isoformat()
    save_storage(storage)
    return candidate

def add_candidate_note(session: Any = None, candidate_id: int = 1, note: str = "", author: str = "Recruiter") -> dict:
    storage = load_storage()
    candidates = storage.get("candidates", [])
    candidate = next((c for c in candidates if c["id"] == candidate_id), None)
    if not candidate:
        raise ValueError("Candidate not found")
        
    notes = list(candidate.get("notes", []))
    notes.insert(0, {"author": author, "note": note, "created_at": datetime.utcnow().isoformat()})
    candidate["notes"] = notes
    
    # Save timeline event
    activities = storage.get("activities", [])
    activities.insert(0, {
        "icon": "fa-user-pen",
        "title": "Note Added",
        "description": f"Note added for candidate {candidate.get('name')}.",
        "time": "Just now"
    })
    storage["activities"] = activities
    save_storage(storage)
    return candidate

def update_candidate_status(session: Any = None, candidate_id: int = 1, status: str = "") -> dict:
    storage = load_storage()
    candidates = storage.get("candidates", [])
    candidate = next((c for c in candidates if c["id"] == candidate_id), None)
    if not candidate:
        raise ValueError("Candidate not found")
    candidate["status"] = status
    candidate["updated_at"] = datetime.utcnow().isoformat()
    
    # Save timeline event
    activities = storage.get("activities", [])
    icon_map = {"Shortlisted": "fa-circle-check", "Interview Scheduled": "fa-calendar-days", "Approved": "fa-thumbs-up", "Rejected": "fa-circle-xmark"}
    activities.insert(0, {
        "icon": icon_map.get(status, "fa-user-clock"),
        "title": f"Candidate {status}",
        "description": f"{candidate.get('name')} status updated to {status}.",
        "time": "Just now"
    })
    storage["activities"] = activities
    save_storage(storage)

    decision_statuses = {"Shortlisted", "Approved", "Rejected"}
    if status in decision_statuses and candidate.get("decision_email_status") != status:
        if send_recruiter_decision_email(candidate, status):
            candidate["decision_email_status"] = status
            save_storage(storage)

    return candidate

def create_application_record(session: Any = None, payload: ApplicationCreate = None) -> dict:
    storage = load_storage()
    apps = storage.get("applications", [])
    new_id = max([a["id"] for a in apps]) + 1 if apps else 1
    
    app = {
        "id": new_id,
        "candidate_id": payload.candidate_id,
        "job_id": payload.job_id,
        "status": payload.status,
        "match_score": payload.match_score,
        "ai_summary": payload.ai_summary,
        "recruiter_notes": payload.recruiter_notes,
        "created_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat()
    }
    apps.append(app)
    storage["applications"] = apps
    
    # Update job application count
    jobs = storage.get("jobs", [])
    for j in jobs:
        if j["id"] == payload.job_id:
            j["applications_count"] += 1
            
    save_storage(storage)
    return app

def list_recent_uploads(session: Any = None, limit: int = 10) -> list[dict]:
    storage = load_storage()
    uploads = [_normalize_resume_record(upload) for upload in storage.get("resume_data", [])]
    uploads.sort(key=lambda u: u.get("created_at", ""), reverse=True)
    return uploads[:limit]

def store_resume_record(session: Any = None, candidate_id: int = 1, filename: str = "", mime_type: str = "", file_path: str = "", parsed: ResumeParseResponse = None, raw_text: str = "") -> dict:
    storage = load_storage()
    resumes = storage.get("resume_data", [])
    new_id = max([r["id"] for r in resumes]) + 1 if resumes else 1
    
    resume = {
        "id": new_id,
        "candidate_id": candidate_id,
        "filename": filename,
        "mime_type": mime_type,
        "file_path": file_path,
        "extracted_text": raw_text,
        "parsed_json": parsed.model_dump(),
        "name": parsed.name,
        "email": parsed.email,
        "phone": parsed.phone,
        "linkedin": parsed.linkedin,
        "github": parsed.github,
        "portfolio": parsed.portfolio,
        "education": parsed.education,
        "skills": parsed.skills,
        "experience": parsed.experience,
        "projects": parsed.projects,
        "certifications": parsed.certifications,
        "languages": parsed.languages,
        "achievements": parsed.achievements,
        "status": "Parsed",
        "created_at": datetime.utcnow().isoformat()
    }
    resumes.append(resume)
    storage["resume_data"] = resumes
    
    # Add timeline activity
    activities = storage.get("activities", [])
    activities.insert(0, {
        "icon": "fa-file-arrow-up",
        "title": "Resume Uploaded",
        "description": f"Uploaded and parsed {filename}.",
        "time": "Just now"
    })
    storage["activities"] = activities
    save_storage(storage)
    return resume

def _skill_objects(session: Any, skill_names: list[str]) -> list[dict]:
    storage = load_storage()
    skills = storage.get("skills", [])
    result = []
    
    for name in _clean_list(skill_names):
        existing = next((s for s in skills if s["name"].lower() == name.lower()), None)
        if existing:
            result.append(existing)
        else:
            new_id = max([s["id"] for s in skills]) + 1 if skills else 1
            new_skill = {"id": new_id, "name": name, "category": "General"}
            skills.append(new_skill)
            result.append(new_skill)
            
    storage["skills"] = skills
    save_storage(storage)
    return result

def upsert_candidate_from_resume(session: Any, parsed: ResumeParseResponse, default_title: str = "") -> dict:
    storage = load_storage()
    candidates = storage.get("candidates", [])
    email = parsed.email or f"{re.sub(r'[^a-z0-9]+', '.', parsed.name.lower()).strip('.') or 'candidate'}@example.com"
    
    candidate = next((c for c in candidates if c["email"] == email), None)
    skills_objs = _skill_objects(None, parsed.skills)
    
    if not candidate:
        new_id = max([c["id"] for c in candidates]) + 1 if candidates else 1
        candidate = {
            "id": new_id,
            "name": parsed.name or email.split("@")[0].replace('.', ' ').title(),
            "email": email,
            "phone": parsed.phone,
            "linkedin": parsed.linkedin,
            "github": parsed.github,
            "portfolio": parsed.portfolio,
            "current_title": default_title or "Applicant",
            "years_experience": 0,
            "location": "Remote",
            "status": "Applied",
            "match_score": 0,
            "tags": ["Imported"],
            "notes": [],
            "avatar_url": "",
            "summary": "Resume imported and parsed.",
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
            "skills": skills_objs
        }
        candidates.append(candidate)
    else:
        candidate["phone"] = parsed.phone or candidate.get("phone", "")
        candidate["linkedin"] = parsed.linkedin or candidate.get("linkedin", "")
        candidate["github"] = parsed.github or candidate.get("github", "")
        candidate["portfolio"] = parsed.portfolio or candidate.get("portfolio", "")
        candidate["skills"] = skills_objs
        candidate["updated_at"] = datetime.utcnow().isoformat()
        
    storage["candidates"] = candidates
    save_storage(storage)
    return candidate

def extract_resume_text(file_path: str) -> str:
    path = Path(file_path)
    suffix = path.suffix.lower()
    if suffix == ".pdf":
        import pdfplumber
        import fitz
        text_parts = []
        try:
            with pdfplumber.open(file_path) as pdf:
                for page in pdf.pages:
                    text_parts.append(page.extract_text() or "")
            if any(text_parts):
                return "\n".join(text_parts)
        except Exception:
            pass
        text_parts = []
        with fitz.open(file_path) as pdf_doc:
            for page in pdf_doc:
                text_parts.append(page.get_text())
        return "\n".join(text_parts)
    if suffix in {".docx", ".doc"}:
        import docx
        document = docx.Document(file_path)
        return "\n".join(paragraph.text for paragraph in document.paragraphs)
    raise ValueError(f"Unsupported file type: {suffix}")


def _profile_url(raw_text: str, provider: str) -> str:
    """Find a LinkedIn or GitHub profile even when a PDF omits the scheme."""
    compact_text = re.sub(r"\s+", "", raw_text or "")
    if provider == "linkedin":
        pattern = r"(?:https?://)?(?:www\.)?linkedin\.com/in/[A-Za-z0-9_-]+?(?=[|#]?(?:https?://)?(?:www\.)?(?:github|linkedin)\.com|[|#]|$)"
    else:
        pattern = r"(?:https?://)?(?:www\.)?github\.com/[A-Za-z0-9_-]+?(?=ProfessionalSummary|Education|TechnicalSkills|WorkExperience|Projects|Certifications|Achievements|Languages|[|#]|$)"
    match = re.search(pattern, compact_text, re.IGNORECASE)
    if not match:
        return ""
    url = match.group(0).rstrip(".,;:)")
    return url if url.lower().startswith(("http://", "https://")) else f"https://{url}"


def _fallback_name(lines: list[str], raw_text: str) -> str:
    if not lines:
        return ""
    first_line = lines[0]
    boundaries = [match.start() for match in (
        re.search(r"[\w.+-]+@[\w-]+\.[\w.-]+", first_line),
        re.search(r"(?:https?://)?(?:www\.)?linkedin\.com", first_line, re.IGNORECASE),
        re.search(r"(?:https?://)?(?:www\.)?github\.com", first_line, re.IGNORECASE),
    ) if match]
    return first_line[:min(boundaries)].strip(" -|#") if boundaries else first_line[:80]


def _valid_name(value: Any) -> bool:
    if not isinstance(value, str):
        return False
    compact = value.strip()
    return bool(compact) and len(compact) <= 80 and "@" not in compact and ".com" not in compact.lower()


def _normalize_resume_record(record: dict) -> dict:
    """Repair legacy parsed fields using the stored raw text without rewriting data."""
    normalized = dict(record)
    raw_text = normalized.get("extracted_text", "")
    parsed = dict(normalized.get("parsed_json") or {})
    heuristic = heuristic_resume_parse(raw_text) if raw_text else ResumeParseResponse()

    if not _valid_name(parsed.get("name")):
        parsed["name"] = heuristic.name
    for field in ("email", "phone", "education", "skills", "experience", "projects", "certifications", "languages", "achievements"):
        if not parsed.get(field):
            parsed[field] = getattr(heuristic, field)
    for provider in ("linkedin", "github"):
        parsed[provider] = _profile_url(parsed.get(provider, ""), provider) or _profile_url(raw_text, provider)
    parsed["portfolio"] = parsed.get("portfolio") or heuristic.portfolio
    normalized["parsed_json"] = parsed
    return normalized

def heuristic_resume_parse(raw_text: str) -> ResumeParseResponse:
    lines = [line.strip() for line in raw_text.splitlines() if line.strip()]
    email_match = re.search(r"[\w.+-]+@[\w-]+\.[\w.-]+", raw_text)
    phone_match = re.search(r"(?:\+?\d{1,3}[\s-]?)?(?:\(?\d{3}\)?[\s-]?)\d{3}[\s-]?\d{4}", raw_text)
    portfolio_match = re.search(r"https?://[^\s]+", raw_text, re.IGNORECASE)

    sections = {"education": [], "skills": [], "experience": [], "projects": [], "certifications": [], "languages": [], "achievements": []}
    current = None
    for line in lines:
        label = line.lower().rstrip(":")
        if any(token in label for token in ["education", "academic"]):
            current = "education"
            continue
        if any(token in label for token in ["skill", "competenc"]):
            current = "skills"
            continue
        if any(token in label for token in ["experience", "employment", "work history"]):
            current = "experience"
            continue
        if "project" in label:
            current = "projects"
            continue
        if "certification" in label:
            current = "certifications"
            continue
        if "language" in label:
            current = "languages"
            continue
        if any(token in label for token in ["achievement", "award"]):
            current = "achievements"
            continue
        if current and len(line) < 200:
            sections[current].append(line)

    fallback_skills = [token for token in re.findall(r"\b[A-Za-z][A-Za-z0-9+.#/-]{1,}\b", raw_text) if token.lower() not in {"education", "experience", "projects", "skills", "resume"}]
    name = _fallback_name(lines, raw_text)
    return ResumeParseResponse(
        name=name,
        email=email_match.group(0) if email_match else "",
        phone=phone_match.group(0) if phone_match else "",
        linkedin=_profile_url(raw_text, "linkedin"),
        github=_profile_url(raw_text, "github"),
        portfolio=portfolio_match.group(0) if portfolio_match else "",
        education=_clean_list(sections["education"]),
        skills=_clean_list(sections["skills"] + fallback_skills)[:40],
        experience=_clean_list(sections["experience"]),
        projects=_clean_list(sections["projects"]),
        certifications=_clean_list(sections["certifications"]),
        languages=_clean_list(sections["languages"]),
        achievements=_clean_list(sections["achievements"]),
        extracted_text=raw_text,
    )

def ollama_resume_parse(raw_text: str) -> ResumeParseResponse:
    client = OllamaClient()
    prompt = f"""
You are an expert AI Resume Parser. Analyze the following resume raw text and extract structured information.

Return strict JSON with the following keys and structure:
- name: string (candidate full name)
- email: string (candidate email address)
- phone: string (candidate phone number)
- linkedin: string (LinkedIn profile URL)
- github: string (GitHub profile URL)
- portfolio: string (Portfolio website URL)
- education: array of strings (degrees, schools, graduation years)
- skills: array of strings (technical and soft skills)
- experience: array of strings (work history: companies, roles, descriptions)
- projects: array of strings (project names and descriptions)
- certifications: array of strings (earned certifications)
- languages: array of strings (languages spoken)
- achievements: array of strings (awards, achievements)

Resume Text:
{raw_text[:6000]}
"""
    try:
        response_text = client.generate(prompt, system="You are a precise JSON extractor. Output valid JSON only, without any markdown formatting or explanations.", format_json=True)
        data = OllamaClient.parse_json_response(response_text)
        
        heuristic = heuristic_resume_parse(raw_text)
        
        return ResumeParseResponse(
            name=data.get("name", "").strip() if _valid_name(data.get("name")) else heuristic.name,
            email=data.get("email", "").strip() or heuristic.email,
            phone=data.get("phone", "").strip() or heuristic.phone,
            linkedin=_profile_url(data.get("linkedin", ""), "linkedin") or heuristic.linkedin,
            github=_profile_url(data.get("github", ""), "github") or heuristic.github,
            portfolio=data.get("portfolio", "").strip() or heuristic.portfolio,
            education=_ensure_list(data.get("education")) or heuristic.education,
            skills=_ensure_list(data.get("skills")) or heuristic.skills,
            experience=_ensure_list(data.get("experience")) or heuristic.experience,
            projects=_ensure_list(data.get("projects")) or heuristic.projects,
            certifications=_ensure_list(data.get("certifications")) or heuristic.certifications,
            languages=_ensure_list(data.get("languages")) or heuristic.languages,
            achievements=_ensure_list(data.get("achievements")) or heuristic.achievements,
            extracted_text=raw_text,
        )
    except Exception as e:
        logger.warning(f"Ollama resume parsing failed ({e}). Using heuristic parser fallback.")
        return heuristic_resume_parse(raw_text)

def _persist_parsed_resume(raw_text: str, filename: str, file_path: str = "", candidate_id: int | None = None) -> Any:
    if not raw_text.strip():
        raise ValueError("Resume text cannot be empty")

    parsed = ollama_resume_parse(raw_text)
    storage = load_storage()
    if candidate_id:
        candidate = next((c for c in storage["candidates"] if c["id"] == candidate_id), None)
        if not candidate:
            raise ValueError("Candidate not found")
    else:
        candidate = upsert_candidate_from_resume(None, parsed, default_title="Applicant")

    record = store_resume_record(
        None,
        candidate["id"],
        filename,
        "text/plain" if not file_path else "application/octet-stream",
        file_path,
        parsed,
        raw_text,
    )

    class ResultWrapper:
        def __init__(self, filename, mime_type, file_path, parsed, resume_id, candidate_id):
            self.filename = filename
            self.mime_type = mime_type
            self.file_path = file_path
            self.parsed = parsed
            self.resume_id = resume_id
            self.candidate_id = candidate_id

    return ResultWrapper(filename, record["mime_type"], file_path, parsed, record["id"], candidate["id"])


def parse_resume_file(session: Any = None, file_path: str = "", candidate_id: int | None = None) -> Any:
    return _persist_parsed_resume(
        extract_resume_text(file_path),
        Path(file_path).name,
        file_path,
        candidate_id,
    )


def parse_resume_text(session: Any = None, raw_text: str = "", filename: str = "pasted_resume.txt", candidate_id: int | None = None) -> Any:
    return _persist_parsed_resume(raw_text, filename, "", candidate_id)

async def screen_resume_against_job(session: Any, candidate_id: int, job_id: int) -> ScreeningResponse:
    from backend.database.data_store import data_store
    candidate = await data_store.get_candidate(candidate_id)
    job = await data_store.get_job(job_id)
    if not candidate or not job:
        raise ValueError("Candidate or job not found")

    resume = await data_store.get_latest_candidate_resume(candidate_id)
    
    resume_text = ""
    if resume:
        resume_text = resume.get("extracted_text", "")
    if not resume_text:
        resume_text = f"Name: {candidate['name']}\nSkills: {', '.join(s.get('name') if isinstance(s, dict) else s for s in candidate['skills'])}\nSummary: {candidate['summary']}"

    job_text = f"""
Title: {job['title']}
Department: {job['department']}
Location: {job['location']}
Hiring Manager: {job['hiring_manager']}
Experience: {job['experience_min']} to {job['experience_max']} years
Salary: {job['salary_min']} to {job['salary_max']}
Employment Type: {job['employment_type']}
Description: {job['description']}
Responsibilities: {', '.join(job['responsibilities'] or [])}
Requirements: {', '.join(job['requirements'] or [])}
Preferred Skills: {', '.join(job['preferred_skills'] or [])}
Nice to Have: {', '.join(job['nice_to_have_skills'] or [])}
"""

    client = OllamaClient()
    prompt = f"""
You are an expert HR Recruiting and Screening assistant. Evaluate the candidate's resume against the job description.

Candidate Resume:
{resume_text[:6000]}

Job Description:
{job_text}

Return strict JSON with the following keys and values:
- resume_summary: string (brief summary of candidate's profile)
- skill_match: integer (0-100 rating of how well candidate skills align with JD requirements)
- experience_match: integer (0-100 rating based on years of experience and relevance of roles)
- education_match: integer (0-100 rating based on education qualifications required vs candidate degree)
- projects_match: integer (0-100 rating based on relevance of candidate projects to the job responsibilities)
- strengths: array of strings (top 3 key strengths of the candidate)
- weaknesses: array of strings (top 2-3 gaps or weaknesses for this role)
- missing_skills: array of strings (specific critical skills required by JD but missing in candidate profile)
- overall_recommendation: string (must be exactly 'Approve', 'Shortlist', or 'Reject')
- overall_match_percent: integer (overall match percentage 0-100, weighted combination of matches)
- explanation: string (detailed, professional paragraph explaining the rationale for the recommendation)

Important: Output valid JSON only, without any markdown formatting or other explanations.
"""
    try:
        response_text = client.generate(prompt, system="You are an expert HR Screener. Output valid JSON only.", format_json=True)
        data = OllamaClient.parse_json_response(response_text)
        
        skill_match = int(data.get("skill_match", 70))
        experience_match = int(data.get("experience_match", 70))
        education_match = int(data.get("education_match", 70))
        projects_match = int(data.get("projects_match", 70))
        overall = int(data.get("overall_match_percent", 70))
        
        overall = max(0, min(100, overall))
        rec = data.get("overall_recommendation", "Shortlist")
        if rec not in {"Approve", "Shortlist", "Reject"}:
            if overall >= 85:
                rec = "Approve"
            elif overall >= 70:
                rec = "Shortlist"
            else:
                rec = "Reject"

        status_map = {"Approve": "Approved", "Shortlist": "Shortlisted", "Reject": "Rejected"}
        cand_status = status_map.get(rec, candidate.get("status", "New"))
        await data_store.update_candidate_screening_result(candidate_id, cand_status, overall)
        await data_store.upsert_application(candidate_id, job_id, rec, overall, data.get("resume_summary", ""))

        return ScreeningResponse(
            candidate_id=candidate_id,
            job_id=job_id,
            resume_summary=data.get("resume_summary", "Summary not available"),
            skill_match=skill_match,
            experience_match=experience_match,
            education_match=education_match,
            projects_match=projects_match,
            strengths=_ensure_list(data.get("strengths")),
            weaknesses=_ensure_list(data.get("weaknesses")),
            missing_skills=_ensure_list(data.get("missing_skills")),
            overall_recommendation=rec,
            overall_match_percent=overall,
            explanation=data.get("explanation", "Evaluation completed successfully."),
            radar={"Skills": skill_match, "Experience": experience_match, "Education": education_match, "Projects": projects_match},
        )
    except Exception as e:
        logger.exception("Ollama screening failed, using fallback heuristic evaluator")
        resume_skills = {s.lower() for s in (resume.get("skills", []) if resume else [])} | {s.get("name", "").lower() if isinstance(s, dict) else s.lower() for s in candidate.get("skills", [])}
        job_skills = {s.get("name", "").lower() if isinstance(s, dict) else s.lower() for s in job.get("skills", [])} | {s.lower() for s in (job.get("requirements", []) or [])} | {s.lower() for s in (job.get("preferred_skills", []) or [])}
        overlap = resume_skills & job_skills
        missing = sorted(job_skills - resume_skills)

        skill_match = min(100, int((len(overlap) / max(len(job_skills), 1)) * 100))
        experience_match = min(100, int((candidate.get("years_experience", 0) / max(job.get("experience_min", 1) or 1, 1)) * 100))
        education_match = 100 if resume and resume.get("education") else 70
        projects_match = 80 if resume and resume.get("projects") else 55
        overall = int((skill_match * 0.4) + (experience_match * 0.25) + (education_match * 0.2) + (projects_match * 0.15))

        if overall >= 85:
            rec = "Approve"
        elif overall >= 70:
            rec = "Shortlist"
        else:
            rec = "Reject"

        explanation = f"Ollama screening offline. Fallback scoring matches {len(overlap)} core skills."
        
        status_map = {"Approve": "Approved", "Shortlist": "Shortlisted", "Reject": "Rejected"}
        cand_status = status_map.get(rec, candidate.get("status", "New"))
        await data_store.update_candidate_screening_result(candidate_id, cand_status, overall)
        await data_store.upsert_application(candidate_id, job_id, rec, overall, "Fallback heuristic summary")

        return ScreeningResponse(
            candidate_id=candidate_id,
            job_id=job_id,
            resume_summary=candidate.get("summary", "Summary not available"),
            skill_match=skill_match,
            experience_match=experience_match,
            education_match=education_match,
            projects_match=projects_match,
            strengths=[f"Matches {len(overlap)} core skills", f"{candidate.get('years_experience')} years of experience"],
            weaknesses=[f"Missing skills: {', '.join(missing[:5])}" if missing else "No critical gaps"],
            missing_skills=missing,
            overall_recommendation=rec,
            overall_match_percent=overall,
            explanation=explanation,
            radar={"Skills": skill_match, "Experience": experience_match, "Education": education_match, "Projects": projects_match},
        )


def analytics_snapshot(session: Any = None) -> dict[str, Any]:
    storage = load_storage()
    jobs = storage.get("jobs", [])
    candidates = storage.get("candidates", [])
    applications = storage.get("applications", [])
    uploads = storage.get("resume_data", [])
    
    from collections import Counter
    return {
        "total_jobs": len(jobs),
        "active_jobs": sum(1 for job in jobs if job["status"] == "Active"),
        "candidates": len(candidates),
        "todays_interviews": sum(1 for c in candidates if c["status"] == "Interview Scheduled"),
        "shortlisted": sum(1 for c in candidates if c["status"] in ("Shortlisted", "Approved")),
        "rejected": sum(1 for c in candidates if c["status"] == "Rejected"),
        "employees": 28,
        "hiring_rate": min(100, int((sum(1 for c in candidates if c["status"] in ("Shortlisted", "Approved", "Hired")) / max(len(candidates), 1)) * 100)),
        "jobs": jobs,
        "candidates_list": candidates,
        "applications": applications,
        "uploads": uploads,
        "funnel": Counter(a["status"] for a in applications),
    }

def list_interviews(session: Any = None) -> list[dict]:
    storage = load_storage()
    interviews = storage.get("interviews", [])
    interviews.sort(key=lambda i: (i.get("date", ""), i.get("time", "")))
    return interviews

def create_interview_record(session: Any = None, payload: Any = None) -> dict:
    storage = load_storage()
    interviews = storage.get("interviews", [])
    new_id = max([i["id"] for i in interviews]) + 1 if interviews else 1
    
    candidate_name = payload.get("candidate_name", "")
    if not candidate_name and payload.get("candidate_id"):
        candidates = storage.get("candidates", [])
        cand = next((c for c in candidates if c["id"] == int(payload["candidate_id"])), None)
        if cand:
            candidate_name = cand["name"]
            
    interview = {
        "id": new_id,
        "candidate_id": int(payload.get("candidate_id")),
        "candidate_name": candidate_name,
        "interviewer": payload.get("interviewer", "Ava Morgan"),
        "date": payload.get("date"),
        "time": payload.get("time"),
        "stage": payload.get("stage", "Technical"),
        "meeting_link": payload.get("meeting_link", "https://meet.google.com/abc-defg-hij"),
        "status": payload.get("status", "Scheduled"),
        "feedback_notes": "",
        "recommendation": "",
        "created_at": datetime.utcnow().isoformat()
    }
    interviews.append(interview)
    storage["interviews"] = interviews
    
    # Update candidate status to Interview Scheduled
    candidates = storage.get("candidates", [])
    cand = next((c for c in candidates if c["id"] == int(payload["candidate_id"])), None)
    if cand:
        cand["status"] = "Interview Scheduled"
        cand["updated_at"] = datetime.utcnow().isoformat()
        
    # Add timeline event
    activities = storage.get("activities", [])
    activities.insert(0, {
        "icon": "fa-calendar-days",
        "title": "Interview Scheduled",
        "description": f"Interview scheduled with {candidate_name}.",
        "time": "Just now"
    })
    storage["activities"] = activities
    
    save_storage(storage)
    return interview

def update_interview_status(session: Any = None, interview_id: int = 1, status: str = "") -> dict:
    storage = load_storage()
    interviews = storage.get("interviews", [])
    intv = next((i for i in interviews if i["id"] == interview_id), None)
    if not intv:
        raise ValueError("Interview not found")
        
    intv["status"] = status
    
    # Add timeline event
    activities = storage.get("activities", [])
    activities.insert(0, {
        "icon": "fa-calendar-check" if status == "Completed" else "fa-calendar-xmark",
        "title": f"Interview {status}",
        "description": f"Interview with {intv.get('candidate_name')} marked as {status}.",
        "time": "Just now"
    })
    storage["activities"] = activities
    
    save_storage(storage)
    return intv

def add_interview_feedback(session: Any = None, interview_id: int = 1, feedback_notes: str = "", recommendation: str = "") -> dict:
    storage = load_storage()
    interviews = storage.get("interviews", [])
    intv = next((i for i in interviews if i["id"] == interview_id), None)
    if not intv:
        raise ValueError("Interview not found")
        
    intv["feedback_notes"] = feedback_notes
    intv["recommendation"] = recommendation
    intv["status"] = "Completed"
    
    # Add timeline event
    activities = storage.get("activities", [])
    activities.insert(0, {
        "icon": "fa-comment-medical",
        "title": "Feedback Logged",
        "description": f"Feedback logged for {intv.get('candidate_name')}.",
        "time": "Just now"
    })
    storage["activities"] = activities
    
    # Update candidate status if recommended
    if recommendation in ("Approve", "Approved", "Shortlist", "Shortlisted"):
        candidates = storage.get("candidates", [])
        cand = next((c for c in candidates if c["id"] == intv["candidate_id"]), None)
        if cand:
            cand["status"] = "Shortlisted"
            cand["updated_at"] = datetime.utcnow().isoformat()
            
    save_storage(storage)
    return intv

def generate_interview_questions(stage: str, skills_list: list[str]) -> list[str]:
    client = OllamaClient()
    prompt = f"""
Generate 3 professional interview questions for a candidate.
Stage: {stage}
Skills: {', '.join(skills_list)}

Return strict JSON with key: questions (which is an array of 3 strings).
"""
    try:
        response_text = client.generate(prompt, system="Output valid JSON only.", format_json=True)
        data = OllamaClient.parse_json_response(response_text)
        return _ensure_list(data.get("questions", []))
    except Exception:
        return [
            f"Explain your experience working with {skills_list[0] if skills_list else 'software systems'} in production.",
            f"Describe a challenging scenario in a {stage} environment and how you resolved it.",
            "How do you stay up-to-date with new technologies and frameworks?"
        ]

def list_employees(session: Any = None) -> list[dict]:
    storage = load_storage()
    return storage.get("employees", [])

def get_employee(session: Any = None, employee_id: int = 1) -> dict | None:
    storage = load_storage()
    employees = storage.get("employees", [])
    return next((e for e in employees if e["id"] == employee_id), None)


