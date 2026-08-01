import asyncio
import json
import os
from pathlib import Path

from backend.database.session import engine
from backend.models.entities import Base, Job, Candidate, Application, ResumeData, Interview, Employee, Activity, Skill, HRUser
from sqlalchemy.ext.asyncio import AsyncSession
from backend.api.routes.auth import get_password_hash

async def migrate_data():
    # 1. Create Tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
        
    print("Database tables created.")

    # 2. Load JSON Data
    storage_path = Path("storage.json")
    if not storage_path.exists():
        print("storage.json not found. Creating schema only.")
        return

    with open(storage_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    # 3. Insert Data
    async with AsyncSession(engine) as session:
        # Skills
        skill_dict = {}
        for s in data.get("skills", []):
            skill = Skill(id=s["id"], name=s["name"], category=s.get("category", "General"))
            session.add(skill)
            skill_dict[s["id"]] = skill
        
        # Jobs
        for j in data.get("jobs", []):
            j_skills = j.pop("skills", [])
            # Convert datetime strings to actual date/time if needed, or rely on defaults if skipped
            job = Job(
                id=j["id"], title=j["title"], department=j["department"], location=j.get("location", "Remote"),
                experience_min=j.get("experience_min", 0), experience_max=j.get("experience_max", 0),
                salary_min=j.get("salary_min", 0), salary_max=j.get("salary_max", 0),
                employment_type=j.get("employment_type", "Full-time"), status=j.get("status", "Active"),
                description=j.get("description", ""), applications_count=j.get("applications_count", 0),
                responsibilities=j.get("responsibilities", []), requirements=j.get("requirements", []),
                preferred_skills=j.get("preferred_skills", []), nice_to_have_skills=j.get("nice_to_have_skills", [])
            )
            # Add skills relationships
            for js in j_skills:
                if js["id"] in skill_dict:
                    job.skills.append(skill_dict[js["id"]])
            session.add(job)
            
        # Candidates
        for c in data.get("candidates", []):
            c_skills = c.pop("skills", [])
            cand = Candidate(
                id=c["id"], name=c["name"], email=c["email"], phone=c.get("phone", ""),
                linkedin=c.get("linkedin", ""), github=c.get("github", ""), portfolio=c.get("portfolio", ""),
                current_title=c.get("current_title", ""), years_experience=c.get("years_experience", 0),
                location=c.get("location", ""), status=c.get("status", "New"), match_score=c.get("match_score", 0),
                tags=c.get("tags", []), notes=c.get("notes", []), avatar_url=c.get("avatar_url", ""),
                summary=c.get("summary", "")
            )
            for cs in c_skills:
                if isinstance(cs, dict) and cs.get("id") in skill_dict:
                    cand.skills.append(skill_dict[cs["id"]])
            session.add(cand)

        # Applications
        for a in data.get("applications", []):
            app = Application(
                id=a["id"], candidate_id=a["candidate_id"], job_id=a["job_id"], status=a.get("status", "Applied"),
                match_score=a.get("match_score", 0), ai_summary=a.get("ai_summary", ""),
                recruiter_notes=a.get("recruiter_notes", "")
            )
            session.add(app)
            
        # Resumes
        for r in data.get("resume_data", []):
            res = ResumeData(
                id=r["id"], candidate_id=r["candidate_id"], filename=r.get("filename", ""),
                mime_type=r.get("mime_type", ""), file_path=r.get("file_path", ""),
                extracted_text=r.get("extracted_text", ""), parsed_json=r.get("parsed_json", {}),
                name=r.get("name", ""), email=r.get("email", ""), phone=r.get("phone", ""),
                linkedin=r.get("linkedin", ""), github=r.get("github", ""), portfolio=r.get("portfolio", ""),
                education=r.get("education", []), skills=r.get("skills", []), experience=r.get("experience", []),
                projects=r.get("projects", []), certifications=r.get("certifications", []),
                languages=r.get("languages", []), achievements=r.get("achievements", []), status=r.get("status", "Parsed")
            )
            session.add(res)
            
        # Interviews
        for i in data.get("interviews", []):
            iv = Interview(
                id=i["id"], candidate_id=i.get("candidate_id"), job_id=i.get("job_id"), date=i.get("date", ""),
                time=i.get("time", ""), duration=i.get("duration", 60), round=i.get("round", ""),
                type=i.get("type", "Online"), meeting_platform=i.get("meeting_platform", "Google Meet"),
                meeting_link=i.get("meeting_link", ""), panel_members=i.get("panel_members", []),
                recruiter_name=i.get("recruiter_name", ""), status=i.get("status", "Scheduled"),
                feedback=i.get("feedback", {}), decision=i.get("decision", "")
            )
            session.add(iv)
            
        # Employees
        for e in data.get("employees", []):
            emp = Employee(
                id=e["id"], candidate_id=e.get("candidate_id"), name=e["name"], email=e.get("email", ""),
                phone=e.get("phone", ""), department=e.get("department", ""), designation=e.get("role", e.get("designation", "")),
                joining_date=e.get("joining_date", ""), status=e.get("status", "Active"), work_location=e.get("work_location", "Remote"),
                reporting_manager=e.get("manager", e.get("reporting_manager", "")), current_project=e.get("current_project", ""),
                avatar_url=e.get("avatar_url", ""), skills=e.get("skills", []), projects=e.get("projects", []),
                performance_history=e.get("performance_history", []), talent_insights=e.get("talent_insights", {}), notes=e.get("notes", [])
            )
            session.add(emp)
            
        # Activities
        for a in data.get("activities", []):
            act = Activity(
                icon=a.get("icon", ""), title=a.get("title", ""), description=a.get("description", ""), time=a.get("time", "")
            )
            session.add(act)

        # Default HR User
        hr = HRUser(
            email="admin@hirepilot.com",
            password_hash=get_password_hash("password123"),
            name="HR Admin"
        )
        session.add(hr)

        await session.commit()
        print("Data migration successful. Created default HR admin: admin@hirepilot.com / password123")

if __name__ == "__main__":
    asyncio.run(migrate_data())
