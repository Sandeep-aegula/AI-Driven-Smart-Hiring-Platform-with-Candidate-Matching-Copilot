from __future__ import annotations

import json
import logging
import asyncio
from pathlib import Path
from typing import Any
import aiofiles
from collections import defaultdict
from datetime import datetime

from backend.schemas.entities import JobCreate, CandidateCreate, ApplicationCreate

logger = logging.getLogger(__name__)

class RecruitmentDataStore:
    def __init__(self, storage_path: str = "storage.json"):
        self.storage_path = Path(storage_path)
        self._lock = asyncio.Lock()
        self._data = None
        
        # Indices for O(1) lookups
        self._jobs_by_id = {}
        self._candidates_by_id = {}
        self._interviews_by_id = {}
        self._employees_by_id = {}
        self._skills_by_name = {}
        self._apps_by_candidate_id = defaultdict(list)
        self._apps_by_job_id = defaultdict(list)
        self._resumes_by_candidate_id = defaultdict(list)

    async def initialize(self) -> None:
        """Initialize the storage and load/cache all data into memory."""
        await self._load_storage()

    async def _load_storage(self) -> dict[str, Any]:
        if self._data is not None:
            return self._data
            
        async with self._lock:
            # Double check inside the lock
            if self._data is not None:
                return self._data
                
            if not self.storage_path.exists():
                from backend.services.recruitment import get_seed_data
                self._data = get_seed_data()
                await self._save_storage_to_disk_unlocked()
            else:
                try:
                    async with aiofiles.open(self.storage_path, "r", encoding="utf-8") as f:
                        content = await f.read()
                        self._data = json.loads(content)
                except Exception:
                    logger.exception("Failed to load JSON storage. Resetting to seed data.")
                    from backend.services.recruitment import get_seed_data
                    self._data = get_seed_data()
                    await self._save_storage_to_disk_unlocked()
                    
            self._rebuild_indices()
            return self._data

    def _rebuild_indices(self) -> None:
        """Rebuild the memory indices for optimal lookup times."""
        self._jobs_by_id = {j["id"]: j for j in self._data.get("jobs", [])}
        self._candidates_by_id = {c["id"]: c for c in self._data.get("candidates", [])}
        self._interviews_by_id = {i["id"]: i for i in self._data.get("interviews", [])}
        self._employees_by_id = {e["id"]: e for e in self._data.get("employees", [])}
        self._skills_by_name = {s["name"].lower(): s for s in self._data.get("skills", [])}
        
        self._apps_by_candidate_id = defaultdict(list)
        self._apps_by_job_id = defaultdict(list)
        for app in self._data.get("applications", []):
            self._apps_by_candidate_id[app["candidate_id"]].append(app)
            self._apps_by_job_id[app["job_id"]].append(app)
            
        self._resumes_by_candidate_id = defaultdict(list)
        for r in self._data.get("resume_data", []):
            self._resumes_by_candidate_id[r["candidate_id"]].append(r)

    async def _save_storage_to_disk_unlocked(self) -> None:
        try:
            async with aiofiles.open(self.storage_path, "w", encoding="utf-8") as f:
                content = json.dumps(self._data, indent=2, default=str)
                await f.write(content)
        except Exception:
            logger.exception("Failed to write to JSON storage.")

    async def _save(self) -> None:
        async with self._lock:
            await self._save_storage_to_disk_unlocked()
            self._rebuild_indices()

    # --- Skill Helpers ---
    def _skill_objects(self, skill_names: list[str]) -> list[dict]:
        skills = self._data.setdefault("skills", [])
        result = []
        
        seen = set()
        cleaned_names = []
        for name in skill_names:
            t = name.strip()
            k = t.lower()
            if t and k not in seen:
                seen.add(k)
                cleaned_names.append(t)
                
        for name in cleaned_names:
            existing = self._skills_by_name.get(name.lower())
            if existing:
                result.append(existing)
            else:
                new_id = max([s["id"] for s in skills]) + 1 if skills else 1
                new_skill = {"id": new_id, "name": name, "category": "General"}
                skills.append(new_skill)
                self._skills_by_name[name.lower()] = new_skill
                result.append(new_skill)
        return result

    # --- Job Operations ---
    async def list_jobs(self, search: str = "", department: str = "All", status: str = "All", sort_by: str = "updated_at") -> list[dict]:
        if self._data is None:
            await self._load_storage()
            
        job_list = list(self._jobs_by_id.values())
        
        if search:
            like = search.lower()
            job_list = [j for j in job_list if like in j["title"].lower() or like in j["department"].lower() or like in j["location"].lower()]
        if department != "All":
            job_list = [j for j in job_list if j["department"] == department]
        if status != "All":
            job_list = [j for j in job_list if j["status"] == status]
            
        job_list.sort(key=lambda j: j.get(sort_by, j.get("updated_at", "")), reverse=True)
        return job_list

    async def get_job(self, job_id: int) -> dict | None:
        if self._data is None:
            await self._load_storage()
        return self._jobs_by_id.get(job_id)

    async def create_job(self, payload: JobCreate) -> dict:
        if self._data is None:
            await self._load_storage()
            
        jobs = self._data.setdefault("jobs", [])
        new_id = max([j["id"] for j in jobs]) + 1 if jobs else 1
        
        job_skills_names = payload.preferred_skills + payload.requirements + payload.required_skills + payload.technical_skills + payload.soft_skills
        skills_objs = self._skill_objects(job_skills_names)
        
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
        await self._save()
        return job

    async def update_job(self, job_id: int, payload: JobCreate) -> dict:
        if self._data is None:
            await self._load_storage()
            
        job = self._jobs_by_id.get(job_id)
        if not job:
            raise ValueError("Job not found")
            
        job_skills_names = payload.preferred_skills + payload.requirements + payload.required_skills + payload.technical_skills + payload.soft_skills
        skills_objs = self._skill_objects(job_skills_names)
        
        for key, value in payload.model_dump().items():
            job[key] = value
            
        job["skills"] = skills_objs
        job["updated_at"] = datetime.utcnow().isoformat()
        
        await self._save()
        return job

    async def archive_job(self, job_id: int) -> dict:
        if self._data is None:
            await self._load_storage()
            
        job = self._jobs_by_id.get(job_id)
        if not job:
            raise ValueError("Job not found")
            
        job["status"] = "Archived"
        await self._save()
        return job

    async def delete_job(self, job_id: int) -> None:
        if self._data is None:
            await self._load_storage()
            
        jobs = self._data.setdefault("jobs", [])
        self._data["jobs"] = [j for j in jobs if j["id"] != job_id]
        await self._save()

    async def clone_job(self, job_id: int) -> dict:
        if self._data is None:
            await self._load_storage()
            
        job = self._jobs_by_id.get(job_id)
        if not job:
            raise ValueError("Job not found")
            
        jobs = self._data.setdefault("jobs", [])
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
        await self._save()
        return clone

    # --- Candidate Operations ---
    async def list_candidates(
        self, 
        search: str = "", 
        status: str = "All", 
        skill: str = "All", 
        job_id: int | None = None,
        min_match_score: int = 0,
        limit: int = 100,
        offset: int = 0
    ) -> list[dict]:
        if self._data is None:
            await self._load_storage()
            
        candidates = list(self._candidates_by_id.values())
        
        if search:
            like = search.lower()
            candidates = [c for c in candidates if like in c["name"].lower() or like in c["email"].lower() or like in c.get("current_title", "").lower()]
        if status != "All":
            candidates = [c for c in candidates if c["status"] == status]
        if skill != "All":
            candidates = [c for c in candidates if any(skill.lower() == s.get("name", "").lower() if isinstance(s, dict) else skill.lower() == s.lower() for s in c.get("skills", []))]
        if job_id is not None:
            # Filter to candidates that have an application for this job
            app_cand_ids = {app["candidate_id"] for app in self._apps_by_job_id.get(job_id, [])}
            candidates = [c for c in candidates if c["id"] in app_cand_ids]
        if min_match_score > 0:
            candidates = [c for c in candidates if c.get("match_score", 0) >= min_match_score]
            
        candidates.sort(key=lambda c: (c.get("match_score", 0), c.get("updated_at", "")), reverse=True)
        return candidates[offset:offset+limit]

    async def get_candidate(self, candidate_id: int) -> dict | None:
        if self._data is None:
            await self._load_storage()
            
        cand = self._candidates_by_id.get(candidate_id)
        if cand:
            cand_copy = dict(cand)
            cand_copy["applications"] = self._apps_by_candidate_id.get(candidate_id, [])
            cand_copy["resumes"] = self._resumes_by_candidate_id.get(candidate_id, [])
            return cand_copy
        return None

    async def create_candidate(self, payload: CandidateCreate) -> dict:
        if self._data is None:
            await self._load_storage()
            
        candidates = self._data.setdefault("candidates", [])
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
        await self._save()
        return candidate

    async def update_candidate(self, candidate_id: int, payload: CandidateCreate) -> dict:
        if self._data is None:
            await self._load_storage()
            
        candidate = self._candidates_by_id.get(candidate_id)
        if not candidate:
            raise ValueError("Candidate not found")
            
        for key, value in payload.model_dump().items():
            candidate[key] = value
            
        candidate["updated_at"] = datetime.utcnow().isoformat()
        await self._save()
        return candidate

    async def add_candidate_note(self, candidate_id: int, note: str, author: str = "Recruiter") -> dict:
        if self._data is None:
            await self._load_storage()
            
        candidate = self._candidates_by_id.get(candidate_id)
        if not candidate:
            raise ValueError("Candidate not found")
            
        notes = candidate.setdefault("notes", [])
        notes.append({
            "author": author,
            "note": note,
            "created_at": datetime.utcnow().isoformat()
        })
        
        candidate["updated_at"] = datetime.utcnow().isoformat()
        await self._save()
        return candidate

    async def update_candidate_status(self, candidate_id: int, status: str) -> dict:
        if self._data is None:
            await self._load_storage()
            
        candidate = self._candidates_by_id.get(candidate_id)
        if not candidate:
            raise ValueError("Candidate not found")
            
        candidate["status"] = status
        candidate["updated_at"] = datetime.utcnow().isoformat()
        
        activities = self._data.setdefault("activities", [])
        activities.insert(0, {
            "icon": "fa-user-pen",
            "title": f"Candidate {status}",
            "description": f"{candidate.get('name')} status updated to {status}.",
            "time": "Just now"
        })
        
        await self._save()
        return candidate

    async def add_email_history(
        self,
        candidate_id: int,
        subject: str,
        body: str,
        status: str = "Sent",
        email_type: str = "",
        decision: str = "",
        interview_id: int | None = None,
        job_id: int | None = None,
        job_title: str = "",
        round_name: str = "",
        sender_name: str = "",
        reply_to_email: str = "",
        draft_saved: bool = False,
    ) -> dict:
        if self._data is None:
            await self._load_storage()
            
        candidate = self._candidates_by_id.get(candidate_id)
        if not candidate:
            raise ValueError("Candidate not found")
            
        emails = candidate.setdefault("email_history", [])
        new_id = max([e.get("id", 0) for e in emails]) + 1 if emails else 1
        
        email_record = {
            "id": new_id,
            "subject": subject,
            "body": body,
            "status": status,
            "sent_at": datetime.utcnow().isoformat(),
            "email_type": email_type,
            "decision": decision,
            "interview_id": interview_id,
            "job_id": job_id,
            "job_title": job_title,
            "round_name": round_name,
            "sender_name": sender_name,
            "reply_to_email": reply_to_email,
            "draft_saved": draft_saved,
        }
        emails.append(email_record)
        candidate["updated_at"] = datetime.utcnow().isoformat()
        
        await self._save()
        return email_record

    # --- Application Operations ---
    async def create_application(self, payload: ApplicationCreate) -> dict:
        if self._data is None:
            await self._load_storage()
            
        apps = self._data.setdefault("applications", [])
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
        
        # Update job application count
        job = self._jobs_by_id.get(payload.job_id)
        if job:
            job["applications_count"] = job.get("applications_count", 0) + 1
            
        await self._save()
        return app

    # --- Resume & Upload Operations ---
    async def list_recent_uploads(self, limit: int = 10) -> list[dict]:
        if self._data is None:
            await self._load_storage()
            
        from backend.services.recruitment import _normalize_resume_record
        uploads = [_normalize_resume_record(upload) for upload in self._data.get("resume_data", [])]
        uploads.sort(key=lambda u: u.get("created_at", ""), reverse=True)
        return uploads[:limit]

    async def store_resume_record(self, candidate_id: int, filename: str, mime_type: str, file_path: str, parsed: Any, raw_text: str) -> dict:
        if self._data is None:
            await self._load_storage()
            
        resumes = self._data.setdefault("resume_data", [])
        new_id = max([r["id"] for r in resumes]) + 1 if resumes else 1
        
        resume = {
            "id": new_id,
            "candidate_id": candidate_id,
            "filename": filename,
            "mime_type": mime_type,
            "file_path": file_path,
            "extracted_text": raw_text,
            "parsed_json": parsed.model_dump() if hasattr(parsed, "model_dump") else parsed,
            "name": getattr(parsed, "name", ""),
            "email": getattr(parsed, "email", ""),
            "phone": getattr(parsed, "phone", ""),
            "linkedin": getattr(parsed, "linkedin", ""),
            "github": getattr(parsed, "github", ""),
            "portfolio": getattr(parsed, "portfolio", ""),
            "education": getattr(parsed, "education", []),
            "skills": getattr(parsed, "skills", []),
            "experience": getattr(parsed, "experience", []),
            "projects": getattr(parsed, "projects", []),
            "certifications": getattr(parsed, "certifications", []),
            "languages": getattr(parsed, "languages", []),
            "achievements": getattr(parsed, "achievements", []),
            "status": "Parsed",
            "created_at": datetime.utcnow().isoformat()
        }
        resumes.append(resume)
        
        # Add timeline activity
        activities = self._data.setdefault("activities", [])
        activities.insert(0, {
            "icon": "fa-file-arrow-up",
            "title": "Resume Uploaded",
            "description": f"Uploaded and parsed {filename}.",
            "time": "Just now"
        })
        
        await self._save()
        return resume

    async def get_latest_candidate_resume(self, candidate_id: int) -> dict | None:
        if self._data is None:
            await self._load_storage()
        resumes = self._resumes_by_candidate_id.get(candidate_id, [])
        if resumes:
            # Return latest based on list order (which is append order)
            return resumes[-1]
        return None

    # --- Interview Operations ---
    async def list_interviews(
        self, 
        candidate_id: int | None = None, 
        job_id: int | None = None, 
        status: str = "All",
        round_name: str = "All"
    ) -> list[dict]:
        if self._data is None:
            await self._load_storage()
        
        interviews = list(self._interviews_by_id.values())
        
        if candidate_id is not None:
            interviews = [i for i in interviews if i.get("candidate_id") == candidate_id]
        if job_id is not None:
            interviews = [i for i in interviews if i.get("job_id") == job_id]
        if status != "All":
            interviews = [i for i in interviews if i.get("status") == status]
        if round_name != "All":
            interviews = [i for i in interviews if i.get("round") == round_name]
            
        interviews.sort(key=lambda i: i.get("date", "") + i.get("time", ""))
        return interviews

    async def create_interview(self, payload: dict) -> dict:
        if self._data is None:
            await self._load_storage()
            
        interviews = self._data.setdefault("interviews", [])
        new_id = max([i["id"] for i in interviews]) + 1 if interviews else 1
        
        interview = {
            **payload,
            "id": new_id,
            "status": "Scheduled",
            "feedback": {},
            "decision": "",
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        }
        interviews.append(interview)
        
        candidate = self._candidates_by_id.get(payload.get("candidate_id"))
        if candidate:
            candidate["status"] = "Interview Scheduled"
            candidate["updated_at"] = datetime.utcnow().isoformat()
            
        await self._save()
        return interview

    async def get_interview(self, interview_id: int) -> dict | None:
        if self._data is None:
            await self._load_storage()
        return self._interviews_by_id.get(interview_id)

    async def update_interview(self, interview_id: int, payload: dict) -> dict:
        if self._data is None:
            await self._load_storage()
            
        interview = self._interviews_by_id.get(interview_id)
        if not interview:
            raise ValueError("Interview not found")
            
        for key, value in payload.items():
            interview[key] = value
            
        interview["updated_at"] = datetime.utcnow().isoformat()
        await self._save()
        return interview

    async def update_interview_status(self, interview_id: int, status: str) -> dict:
        if self._data is None:
            await self._load_storage()
            
        interview = self._interviews_by_id.get(interview_id)
        if not interview:
            raise ValueError("Interview not found")
            
        interview["status"] = status
        interview["updated_at"] = datetime.utcnow().isoformat()
        
        # Also update corresponding candidate status if needed
        cand_id = interview.get("candidate_id")
        if cand_id and status in ("Completed", "Cancelled"):
            candidate = self._candidates_by_id.get(cand_id)
            if candidate:
                if status == "Completed":
                    candidate["status"] = "Interviewed"
                candidate["updated_at"] = datetime.utcnow().isoformat()
                
        await self._save()
        return interview

    async def add_interview_feedback(self, interview_id: int, feedback: dict) -> dict:
        if self._data is None:
            await self._load_storage()
            
        interview = self._interviews_by_id.get(interview_id)
        if not interview:
            raise ValueError("Interview not found")
            
        interview["feedback"] = feedback
        interview["status"] = "Feedback Logged"
        interview["updated_at"] = datetime.utcnow().isoformat()
        
        cand_id = interview.get("candidate_id")
        if cand_id:
            candidate = self._candidates_by_id.get(cand_id)
            if candidate:
                candidate["status"] = "Under Review"
                candidate["updated_at"] = datetime.utcnow().isoformat()
                
        await self._save()
        return interview

    async def log_interview_decision(self, interview_id: int, decision: str) -> dict:
        if self._data is None:
            await self._load_storage()
            
        interview = self._interviews_by_id.get(interview_id)
        if not interview:
            raise ValueError("Interview not found")
            
        interview["decision"] = decision
        interview["status"] = "Completed"
        interview["updated_at"] = datetime.utcnow().isoformat()
        
        cand_id = interview.get("candidate_id")
        if cand_id:
            candidate = self._candidates_by_id.get(cand_id)
            if candidate:
                if decision == "Selected":
                    candidate["status"] = "Hired"
                    logger.info(f"Hand-off to Employee Module: Candidate {cand_id} hired from Interview {interview_id}.")
                elif decision == "Rejected":
                    candidate["status"] = "Rejected"
                elif decision == "Next Round":
                    candidate["status"] = "Interviewing"
                candidate["updated_at"] = datetime.utcnow().isoformat()
                
        await self._save()
        return interview

    # --- Employee Operations ---
    async def list_employees(
        self, 
        search: str = "", 
        department: str = "All", 
        designation: str = "All", 
        status: str = "All", 
        limit: int = 100, 
        offset: int = 0
    ) -> list[dict]:
        if self._data is None:
            await self._load_storage()
            
        emps = list(self._employees_by_id.values())
        
        if search:
            like = search.lower()
            emps = [e for e in emps if like in e["name"].lower() or like in e.get("email", "").lower()]
        if department != "All":
            emps = [e for e in emps if e.get("department") == department]
        if designation != "All":
            emps = [e for e in emps if e.get("designation") == designation]
        if status != "All":
            emps = [e for e in emps if e.get("status") == status]
            
        emps.sort(key=lambda e: e.get("joining_date", ""), reverse=True)
        return emps[offset:offset+limit]

    async def get_employee(self, employee_id: int) -> dict | None:
        if self._data is None:
            await self._load_storage()
        return self._employees_by_id.get(employee_id)
        
    async def get_employee_by_candidate_id(self, candidate_id: int) -> dict | None:
        if self._data is None:
            await self._load_storage()
        for emp in self._employees_by_id.values():
            if emp.get("candidate_id") == candidate_id:
                return emp
        return None

    async def employee_exists(self, candidate_id: int) -> bool:
        emp = await self.get_employee_by_candidate_id(candidate_id)
        return emp is not None

    async def create_employee(self, payload: dict) -> dict:
        if self._data is None:
            await self._load_storage()
            
        employees = self._data.setdefault("employees", [])
        new_id = max([e["id"] for e in employees]) + 1 if employees else 1
        
        emp = {
            **payload,
            "id": new_id,
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        }
        employees.append(emp)
        
        activities = self._data.setdefault("activities", [])
        activities.insert(0, {
            "icon": "fa-user-tie",
            "title": "New Employee Onboarded",
            "description": f"{emp.get('name')} joined as {emp.get('designation', 'Employee')}.",
            "time": "Just now"
        })
        
        await self._save()
        return emp

    async def update_employee(self, employee_id: int, payload: dict) -> dict:
        if self._data is None:
            await self._load_storage()
            
        emp = self._employees_by_id.get(employee_id)
        if not emp:
            raise ValueError("Employee not found")
            
        for key, value in payload.items():
            emp[key] = value
            
        emp["updated_at"] = datetime.utcnow().isoformat()
        await self._save()
        return emp

    async def update_employee_skills(self, employee_id: int, skills: list[dict]) -> dict:
        if self._data is None:
            await self._load_storage()
            
        emp = self._employees_by_id.get(employee_id)
        if not emp:
            raise ValueError("Employee not found")
            
        emp["skills"] = skills
        emp["updated_at"] = datetime.utcnow().isoformat()
        await self._save()
        return emp

    async def add_employee_project(self, employee_id: int, project: dict) -> dict:
        if self._data is None:
            await self._load_storage()
            
        emp = self._employees_by_id.get(employee_id)
        if not emp:
            raise ValueError("Employee not found")
            
        projects = emp.setdefault("projects", [])
        new_proj_id = max([p.get("id", 0) for p in projects]) + 1 if projects else 1
        
        new_project = {**project, "id": new_proj_id}
        projects.append(new_project)
        
        emp["updated_at"] = datetime.utcnow().isoformat()
        await self._save()
        return new_project

    async def update_employee_project(self, employee_id: int, project_id: int, payload: dict) -> dict:
        if self._data is None:
            await self._load_storage()
            
        emp = self._employees_by_id.get(employee_id)
        if not emp:
            raise ValueError("Employee not found")
            
        projects = emp.setdefault("projects", [])
        proj = next((p for p in projects if p.get("id") == project_id), None)
        if not proj:
            raise ValueError("Project not found")
            
        for k, v in payload.items():
            proj[k] = v
            
        emp["updated_at"] = datetime.utcnow().isoformat()
        await self._save()
        return proj

    async def add_employee_performance(self, employee_id: int, performance: dict) -> dict:
        if self._data is None:
            await self._load_storage()
            
        emp = self._employees_by_id.get(employee_id)
        if not emp:
            raise ValueError("Employee not found")
            
        perf_history = emp.setdefault("performance_history", [])
        new_perf_id = max([p.get("id", 0) for p in perf_history]) + 1 if perf_history else 1
        
        new_perf = {**performance, "id": new_perf_id}
        perf_history.append(new_perf)
        
        emp["updated_at"] = datetime.utcnow().isoformat()
        await self._save()
        return new_perf

    async def update_talent_insights(self, employee_id: int, insights: dict) -> dict:
        if self._data is None:
            await self._load_storage()
            
        emp = self._employees_by_id.get(employee_id)
        if not emp:
            raise ValueError("Employee not found")
            
        emp["talent_insights"] = insights
        emp["updated_at"] = datetime.utcnow().isoformat()
        await self._save()
        return emp

    # --- Analytics & Dashboard Snapshot ---
    async def get_analytics_snapshot(self) -> dict[str, Any]:
        if self._data is None:
            await self._load_storage()
            
        jobs = list(self._jobs_by_id.values())
        candidates = list(self._candidates_by_id.values())
        applications = self._data.get("applications", [])
        uploads = self._data.get("resume_data", [])
        
        # Single-pass over jobs
        total_jobs = len(jobs)
        active_jobs = 0
        for job in jobs:
            if job.get("status") == "Active":
                active_jobs += 1
                
        # Single-pass over candidates
        total_candidates = len(candidates)
        todays_interviews = 0
        shortlisted = 0
        rejected = 0
        hired_or_approved = 0
        for c in candidates:
            status = c.get("status")
            if status == "Interview Scheduled":
                todays_interviews += 1
            elif status in ("Shortlisted", "Approved"):
                shortlisted += 1
            elif status == "Rejected":
                rejected += 1
                
            if status in ("Shortlisted", "Approved", "Hired"):
                hired_or_approved += 1
                
        hiring_rate = min(100, int((hired_or_approved / max(total_candidates, 1)) * 100))
        
        # Single-pass over applications
        from collections import Counter
        funnel = Counter()
        for app in applications:
            funnel[app.get("status")] += 1
            
        return {
            "total_jobs": total_jobs,
            "active_jobs": active_jobs,
            "candidates": total_candidates,
            "todays_interviews": todays_interviews,
            "shortlisted": shortlisted,
            "rejected": rejected,
            "employees": 28,
            "hiring_rate": hiring_rate,
            "jobs": jobs,
            "candidates_list": candidates,
            "applications": applications,
            "uploads": uploads,
            "funnel": dict(funnel),
        }

    # --- Screening update helpers ---
    async def update_candidate_screening_result(self, candidate_id: int, status: str, match_score: int) -> None:
        if self._data is None:
            await self._load_storage()
        candidate = self._candidates_by_id.get(candidate_id)
        if candidate:
            candidate["status"] = status
            candidate["match_score"] = match_score
            candidate["updated_at"] = datetime.utcnow().isoformat()
            await self._save()

    async def upsert_application(self, candidate_id: int, job_id: int, status: str, match_score: int, ai_summary: str) -> None:
        if self._data is None:
            await self._load_storage()
        applications = self._data.setdefault("applications", [])
        app_record = next((a for a in applications if a["candidate_id"] == candidate_id and a["job_id"] == job_id), None)
        if app_record:
            app_record["status"] = status
            app_record["match_score"] = match_score
            app_record["ai_summary"] = ai_summary
            app_record["updated_at"] = datetime.utcnow().isoformat()
        else:
            new_id = max([a["id"] for a in applications]) + 1 if applications else 1
            app_record = {
                "id": new_id,
                "candidate_id": candidate_id,
                "job_id": job_id,
                "status": status,
                "match_score": match_score,
                "ai_summary": ai_summary,
                "recruiter_notes": "",
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat()
            }
            applications.append(app_record)
        await self._save()

    # --- Resume Upsert / Parse Async Helpers ---
    async def upsert_candidate_from_resume(self, parsed: Any, default_title: str = "") -> dict:
        import re
        if self._data is None:
            await self._load_storage()
        candidates = self._data.setdefault("candidates", [])
        email = parsed.email or f"{re.sub(r'[^a-z0-9]+', '.', parsed.name.lower()).strip('.') or 'candidate'}@example.com"
        
        candidate = next((c for c in candidates if c["email"] == email), None)
        skills_objs = self._skill_objects(parsed.skills)
        
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
            
        await self._save()
        return candidate

    async def parse_resume_file(self, file_path: str, candidate_id: int | None = None) -> Any:
        from backend.services.recruitment import extract_resume_text
        raw_text = extract_resume_text(file_path)
        return await self._persist_parsed_resume(raw_text, Path(file_path).name, file_path, candidate_id)

    async def parse_resume_text(self, raw_text: str, filename: str = "pasted_resume.txt", candidate_id: int | None = None) -> Any:
        return await self._persist_parsed_resume(raw_text, filename, "", candidate_id)

    async def _persist_parsed_resume(self, raw_text: str, filename: str, file_path: str = "", candidate_id: int | None = None) -> Any:
        if not raw_text.strip():
            raise ValueError("Resume text cannot be empty")
            
        from backend.services.recruitment import ollama_resume_parse
        parsed = ollama_resume_parse(raw_text)
        
        if candidate_id:
            candidate = await self.get_candidate(candidate_id)
            if not candidate:
                raise ValueError("Candidate not found")
        else:
            candidate = await self.upsert_candidate_from_resume(parsed, default_title="Applicant")
            
        mime_type = "text/plain" if not file_path else "application/octet-stream"
        record = await self.store_resume_record(
            candidate["id"],
            filename,
            mime_type,
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

# Global singleton instance
data_store = RecruitmentDataStore()


