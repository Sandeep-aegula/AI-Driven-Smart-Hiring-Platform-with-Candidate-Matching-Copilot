import asyncio
import json
import sys
import os
from datetime import datetime
from typing import Any

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database.session import engine, get_db_session
from backend.database.base import Base
from backend.models.entities import (
    Skill, Job, Candidate, Application, ResumeData, Interview, Employee, Activity
)


async def migrate_json_to_mysql():
    """Migrate all data from storage.json to MySQL."""

    # Load JSON data
    storage_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "storage.json")

    if not os.path.exists(storage_path):
        print(f"storage.json not found at {storage_path}")
        return

    with open(storage_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    skills_data = data.get("skills", [])
    jobs_data = data.get("jobs", [])
    candidates_data = data.get("candidates", [])
    applications_data = data.get("applications", [])
    resume_data = data.get("resume_data", [])
    interviews_data = data.get("interviews", [])
    employees_data = data.get("employees", [])
    activities_data = data.get("activities", [])

    print(f"Loaded data: {len(skills_data)} skills, {len(jobs_data)} jobs, {len(candidates_data)} candidates")
    print(f"  {len(applications_data)} applications, {len(resume_data)} resumes, {len(interviews_data)} interviews")
    print(f"  {len(employees_data)} employees, {len(activities_data)} activities")

    async with get_db_session() as session:
        # ============================================================
        # 1. MIGRATE SKILLS
        # ============================================================
        print("\n1. Migrating skills...")
        skill_map = {}  # JSON skill name -> DB skill ID

        for skill_json in skills_data:
            stmt = select(Skill).where(Skill.name == skill_json["name"])
            result = await session.execute(stmt)
            skill = result.scalar_one_or_none()

            if not skill:
                skill = Skill(
                    name=skill_json["name"],
                    category=skill_json.get("category", "General"),
                )
                session.add(skill)
                await session.flush()

            skill_map[skill_json["name"]] = skill.id

        print(f"  Migrated {len(skill_map)} skills")

        # ============================================================
        # 2. MIGRATE JOBS
        # ============================================================
        print("\n2. Migrating jobs...")
        job_id_map = {}  # JSON job ID -> DB job ID

        for job_json in jobs_data:
            stmt = select(Job).where(Job.id == job_json["id"])
            result = await session.execute(stmt)
            job = result.scalar_one_or_none()

            if not job:
                job = Job(
                    id=job_json["id"],
                    title=job_json["title"],
                    department=job_json["department"],
                    location=job_json.get("location", "Remote"),
                    experience_min=job_json.get("experience_min", 0),
                    experience_max=job_json.get("experience_max", 0),
                    salary_min=job_json.get("salary_min", 0),
                    salary_max=job_json.get("salary_max", 0),
                    employment_type=job_json.get("employment_type", "Full-time"),
                    hiring_manager=job_json.get("hiring_manager", ""),
                    deadline=job_json.get("deadline", ""),
                    status=job_json.get("status", "Active"),
                    description=job_json.get("description", ""),
                    responsibilities=job_json.get("responsibilities", []),
                    requirements=job_json.get("requirements", []),
                    preferred_skills=job_json.get("preferred_skills", []),
                    nice_to_have_skills=job_json.get("nice_to_have_skills", []),
                    benefits=job_json.get("benefits", []),
                    openings=job_json.get("openings", 1),
                    work_mode=job_json.get("work_mode", "Remote"),
                    required_skills=job_json.get("required_skills", []),
                    technical_skills=job_json.get("technical_skills", []),
                    soft_skills=job_json.get("soft_skills", []),
                    qualifications=job_json.get("qualifications", []),
                    additional_requirements=job_json.get("additional_requirements", []),
                    experience_required=job_json.get("experience_required", ""),
                    salary_range=job_json.get("salary_range", ""),
                    applications_count=job_json.get("applications_count", 0),
                )

                # Parse created_at/updated_at
                for field in ["created_at", "updated_at"]:
                    if job_json.get(field):
                        try:
                            setattr(job, field, datetime.fromisoformat(job_json[field].replace("Z", "+00:00")))
                        except:
                            pass

                # Link skills
                job_skills = job_json.get("skills", [])
                for skill_json in job_skills:
                    skill_id = skill_map.get(skill_json["name"])
                    if skill_id:
                        stmt = select(Skill).where(Skill.id == skill_id)
                        res = await session.execute(stmt)
                        skill = res.scalar_one_or_none()
                        if skill:
                            job.skills.append(skill)

                session.add(job)
                await session.flush()

            job_id_map[job_json["id"]] = job.id

        print(f"  Migrated {len(job_id_map)} jobs")

        # ============================================================
        # 3. MIGRATE CANDIDATES
        # ============================================================
        print("\n3. Migrating candidates...")
        candidate_id_map = {}  # JSON candidate ID -> DB candidate ID

        for cand_json in candidates_data:
            stmt = select(Candidate).where(Candidate.id == cand_json["id"])
            result = await session.execute(stmt)
            candidate = result.scalar_one_or_none()

            if not candidate:
                candidate = Candidate(
                    id=cand_json["id"],
                    name=cand_json["name"],
                    email=cand_json["email"],
                    phone=cand_json.get("phone", ""),
                    linkedin=cand_json.get("linkedin", ""),
                    github=cand_json.get("github", ""),
                    portfolio=cand_json.get("portfolio", ""),
                    current_title=cand_json.get("current_title", ""),
                    years_experience=cand_json.get("years_experience", 0),
                    location=cand_json.get("location", ""),
                    status=cand_json.get("status", "New"),
                    match_score=cand_json.get("match_score", 0),
                    tags=cand_json.get("tags", []),
                    notes=cand_json.get("notes", []),
                    avatar_url=cand_json.get("avatar_url", ""),
                    summary=cand_json.get("summary", ""),
                )

                # Parse timestamps
                for field in ["created_at", "updated_at"]:
                    if cand_json.get(field):
                        try:
                            setattr(candidate, field, datetime.fromisoformat(cand_json[field].replace("Z", "+00:00")))
                        except:
                            pass

                # Link skills
                cand_skills = cand_json.get("skills", [])
                for skill_json in cand_skills:
                    if isinstance(skill_json, dict):
                        skill_name = skill_json.get("name")
                    else:
                        skill_name = skill_json
                    skill_id = skill_map.get(skill_name)
                    if skill_id:
                        stmt = select(Skill).where(Skill.id == skill_id)
                        res = await session.execute(stmt)
                        skill = res.scalar_one_or_none()
                        if skill:
                            candidate.skills.append(skill)

                session.add(candidate)
                await session.flush()

            candidate_id_map[cand_json["id"]] = candidate.id

        print(f"  Migrated {len(candidate_id_map)} candidates")

        # ============================================================
        # 4. MIGRATE APPLICATIONS
        # ============================================================
        print("\n4. Migrating applications...")

        for app_json in applications_data:
            stmt = select(Application).where(Application.id == app_json["id"])
            result = await session.execute(stmt)
            app = result.scalar_one_or_none()

            if not app:
                # Map candidate and job IDs
                cand_id = candidate_id_map.get(app_json["candidate_id"])
                job_id = job_id_map.get(app_json["job_id"])

                if cand_id and job_id:
                    app = Application(
                        id=app_json["id"],
                        candidate_id=cand_id,
                        job_id=job_id,
                        status=app_json.get("status", "Applied"),
                        match_score=app_json.get("match_score", 0),
                        ai_summary=app_json.get("ai_summary", ""),
                        recruiter_notes=app_json.get("recruiter_notes", ""),
                    )

                    for field in ["created_at", "updated_at"]:
                        if app_json.get(field):
                            try:
                                setattr(app, field, datetime.fromisoformat(app_json[field].replace("Z", "+00:00")))
                            except:
                                pass

                    session.add(app)

        print(f"  Migrated {len(applications_data)} applications")

        # ============================================================
        # 5. MIGRATE RESUME DATA
        # ============================================================
        print("\n5. Migrating resume data...")

        for resume_json in resume_data:
            stmt = select(ResumeData).where(ResumeData.id == resume_json["id"])
            result = await session.execute(stmt)
            resume = result.scalar_one_or_none()

            if not resume:
                cand_id = candidate_id_map.get(resume_json["candidate_id"])
                if cand_id:
                    resume = ResumeData(
                        id=resume_json["id"],
                        candidate_id=cand_id,
                        filename=resume_json.get("filename", ""),
                        mime_type=resume_json.get("mime_type", ""),
                        file_path=resume_json.get("file_path", ""),
                        extracted_text=resume_json.get("extracted_text", ""),
                        parsed_json=resume_json.get("parsed_json", {}),
                        name=resume_json.get("name", ""),
                        email=resume_json.get("email", ""),
                        phone=resume_json.get("phone", ""),
                        linkedin=resume_json.get("linkedin", ""),
                        github=resume_json.get("github", ""),
                        portfolio=resume_json.get("portfolio", ""),
                        education=resume_json.get("education", []),
                        skills=resume_json.get("skills", []),
                        experience=resume_json.get("experience", []),
                        projects=resume_json.get("projects", []),
                        certifications=resume_json.get("certifications", []),
                        languages=resume_json.get("languages", []),
                        achievements=resume_json.get("achievements", []),
                        status=resume_json.get("status", "Parsed"),
                    )

                    if resume_json.get("created_at"):
                        try:
                            resume.created_at = datetime.fromisoformat(resume_json["created_at"].replace("Z", "+00:00"))
                        except:
                            pass

                    session.add(resume)

        print(f"  Migrated {len(resume_data)} resume records")

        # ============================================================
        # 6. MIGRATE INTERVIEWS
        # ============================================================
        print("\n6. Migrating interviews...")

        for iv_json in interviews_data:
            stmt = select(Interview).where(Interview.id == iv_json["id"])
            result = await session.execute(stmt)
            iv = result.scalar_one_or_none()

            if not iv:
                cand_id = candidate_id_map.get(iv_json.get("candidate_id"))
                job_id = job_id_map.get(iv_json.get("job_id")) if iv_json.get("job_id") else None

                if cand_id:
                    iv = Interview(
                        id=iv_json["id"],
                        candidate_id=cand_id,
                        job_id=job_id,
                        date=iv_json.get("date", ""),
                        time=iv_json.get("time", ""),
                        duration=iv_json.get("duration", 60),
                        round=iv_json.get("round", iv_json.get("stage", "")),
                        type=iv_json.get("type", "Online"),
                        meeting_platform=iv_json.get("meeting_platform", "Google Meet"),
                        meeting_link=iv_json.get("meeting_link", ""),
                        panel_members=iv_json.get("panel_members", []),
                        recruiter_name=iv_json.get("recruiter_name", ""),
                        status=iv_json.get("status", "Scheduled"),
                        feedback=iv_json.get("feedback", {}),
                        decision=iv_json.get("decision", ""),
                    )

                    for field in ["created_at", "updated_at"]:
                        if iv_json.get(field):
                            try:
                                setattr(iv, field, datetime.fromisoformat(iv_json[field].replace("Z", "+00:00")))
                            except:
                                pass

                    session.add(iv)

        print(f"  Migrated {len(interviews_data)} interviews")

        # ============================================================
        # 7. MIGRATE EMPLOYEES
        # ============================================================
        print("\n7. Migrating employees...")

        for emp_json in employees_data:
            stmt = select(Employee).where(Employee.id == emp_json["id"])
            result = await session.execute(stmt)
            emp = result.scalar_one_or_none()

            if not emp:
                # Find candidate_id by email
                cand_id = None
                email = emp_json.get("email")
                if email:
                    stmt = select(Candidate).where(Candidate.email == email).limit(1)

                emp = Employee(
                    id=emp_json["id"],
                    candidate_id=cand_id,
                    name=emp_json.get("name", ""),
                    email=emp_json.get("email", ""),
                    phone=emp_json.get("phone", ""),
                    department=emp_json.get("department", ""),
                    designation=emp_json.get("designation", emp_json.get("role", "")),
                    joining_date=emp_json.get("joining_date", ""),
                    status=emp_json.get("status", "Active"),
                    work_location=emp_json.get("work_location", "Remote"),
                    reporting_manager=emp_json.get("reporting_manager", emp_json.get("manager", "")),
                    current_project=emp_json.get("current_project", ""),
                    avatar_url=emp_json.get("avatar_url", ""),
                    skills=emp_json.get("skills", []),
                    projects=emp_json.get("projects", []),
                    performance_history=emp_json.get("performance_history", []),
                    talent_insights=emp_json.get("talent_insights", {}),
                    notes=emp_json.get("notes", []),
                )

                for field in ["created_at", "updated_at"]:
                    if emp_json.get(field):
                        try:
                            setattr(emp, field, datetime.fromisoformat(emp_json[field].replace("Z", "+00:00")))
                        except:
                            pass

                session.add(emp)

        print(f"  Migrated {len(employees_data)} employees")

        # ============================================================
        # 8. MIGRATE ACTIVITIES
        # ============================================================
        print("\n8. Migrating activities...")

        for act_json in activities_data:
            stmt = select(Activity).where(Activity.id == act_json.get("id", 0))
            result = await session.execute(stmt)
            act = result.scalar_one_or_none()

            if not act:
                act = Activity(
                    id=act_json.get("id", 0) if act_json.get("id") else None,
                    icon=act_json.get("icon", ""),
                    title=act_json.get("title", ""),
                    description=act_json.get("description", ""),
                    time=act_json.get("time", ""),
                )

                if act_json.get("created_at"):
                    try:
                        act.created_at = datetime.fromisoformat(act_json["created_at"].replace("Z", "+00:00"))
                    except:
                        pass

                session.add(act)

        print(f"  Migrated {len(activities_data)} activities")

        # Commit all changes
        await session.commit()
        print("\n✓ Migration completed successfully!")


async def verify_migration():
    """Verify the migration by counting records in each table."""
    async with get_db_session() as session:
        print("\n=== Migration Verification ===")

        tables = [
            ("skills", Skill),
            ("jobs", Job),
            ("candidates", Candidate),
            ("applications", Application),
            ("resume_data", ResumeData),
            ("interviews", Interview),
            ("employees", Employee),
            ("activities", Activity),
        ]

        for table_name, model in tables:
            result = await session.execute(select(model))
            count = len(result.scalars().all())
            print(f"  {table_name}: {count} records")


async def main():
    print("Starting JSON to MySQL migration...")
    await migrate_json_to_mysql()
    await verify_migration()


if __name__ == "__main__":
    asyncio.run(main())
