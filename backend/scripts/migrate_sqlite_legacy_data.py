"""
One-off migration: import the legacy ai_recruitment_copilot.db (SQLite, pre-MySQL
era of this repo) into the live MySQL database used by the running app.

Safe to run once. Re-running will duplicate rows (no idempotency guard) except for
Skills, which are looked up/created by name.

Usage:
    venv\\Scripts\\python.exe -m backend.scripts.migrate_sqlite_legacy_data
"""
from __future__ import annotations

import json
import os
import sqlite3
import sys
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from sqlalchemy import select

from backend.database.session import get_db_session
from backend.models.entities import (
    Skill, Job, Candidate, ResumeData, Application, Interview, Employee, Activity,
)

SQLITE_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "ai_recruitment_copilot.db",
)


def _loads(value, default):
    if value is None:
        return default
    if isinstance(value, (list, dict)):
        return value
    try:
        return json.loads(value)
    except (json.JSONDecodeError, TypeError):
        return default


def _parse_dt(value):
    if not value:
        return None
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M:%S.%f"):
        try:
            return datetime.strptime(value, fmt)
        except ValueError:
            continue
    return None


async def migrate() -> None:
    if not os.path.exists(SQLITE_PATH):
        print(f"No legacy SQLite file found at {SQLITE_PATH}; nothing to migrate.")
        return

    con = sqlite3.connect(SQLITE_PATH)
    con.row_factory = sqlite3.Row
    cur = con.cursor()

    async with get_db_session() as session:
        # ---- Skills (dedupe by name against whatever already exists) ----
        skill_id_map: dict[int, int] = {}
        cur.execute("SELECT * FROM skills")
        for row in cur.fetchall():
            row = dict(row)
            result = await session.execute(select(Skill).where(Skill.name == row["name"]))
            skill = result.scalar_one_or_none()
            if not skill:
                skill = Skill(name=row["name"], category=row.get("category") or "General")
                session.add(skill)
                await session.flush()
            skill_id_map[row["id"]] = skill.id
        print(f"Skills: {len(skill_id_map)} mapped")

        # ---- job_skills / candidate_skills junctions (loaded now, applied after jobs/candidates exist) ----
        cur.execute("SELECT job_id, skill_id FROM job_skills")
        job_skill_links = cur.fetchall()
        cur.execute("SELECT candidate_id, skill_id FROM candidate_skills")
        candidate_skill_links = cur.fetchall()

        # ---- Jobs ----
        job_id_map: dict[int, int] = {}
        cur.execute("SELECT * FROM jobs")
        for row in cur.fetchall():
            row = dict(row)
            job = Job(
                title=row["title"],
                department=row["department"],
                location=row["location"] or "Remote",
                experience_min=row["experience_min"] or 0,
                experience_max=row["experience_max"] or 0,
                salary_min=row["salary_min"] or 0,
                salary_max=row["salary_max"] or 0,
                employment_type=row["employment_type"] or "Full-time",
                hiring_manager=row["hiring_manager"] or "",
                deadline=row["deadline"] or "",
                status=row["status"] or "Active",
                description=row["description"] or "",
                responsibilities=_loads(row["responsibilities"], []),
                requirements=_loads(row["requirements"], []),
                preferred_skills=_loads(row["preferred_skills"], []),
                nice_to_have_skills=_loads(row["nice_to_have_skills"], []),
                applications_count=row["applications_count"] or 0,
            )
            session.add(job)
            await session.flush()
            job_id_map[row["id"]] = job.id
        print(f"Jobs: {len(job_id_map)} migrated")

        for link in job_skill_links:
            job = await session.get(Job, job_id_map.get(link["job_id"]))
            new_skill_id = skill_id_map.get(link["skill_id"])
            if job and new_skill_id:
                skill = await session.get(Skill, new_skill_id)
                if skill and skill not in job.skills:
                    job.skills.append(skill)

        # ---- Candidates ----
        candidate_id_map: dict[int, int] = {}
        cur.execute("SELECT * FROM candidates")
        for row in cur.fetchall():
            row = dict(row)
            candidate = Candidate(
                name=row["name"],
                email=row["email"],
                phone=row["phone"] or "",
                linkedin=row["linkedin"] or "",
                github=row["github"] or "",
                portfolio=row["portfolio"] or "",
                current_title=row["current_title"] or "",
                years_experience=row["years_experience"] or 0,
                location=row["location"] or "",
                status=row["status"] or "New",
                match_score=row["match_score"] or 0,
                tags=_loads(row["tags"], []),
                notes=_loads(row["notes"], []),
                avatar_url=row["avatar_url"] or "",
                summary=row["summary"] or "",
            )
            session.add(candidate)
            await session.flush()
            candidate_id_map[row["id"]] = candidate.id
        print(f"Candidates: {len(candidate_id_map)} migrated")

        for link in candidate_skill_links:
            candidate = await session.get(Candidate, candidate_id_map.get(link["candidate_id"]))
            new_skill_id = skill_id_map.get(link["skill_id"])
            if candidate and new_skill_id:
                skill = await session.get(Skill, new_skill_id)
                if skill and skill not in candidate.skills:
                    candidate.skills.append(skill)

        # ---- Resume data ----
        cur.execute("SELECT * FROM resume_data")
        resume_count = 0
        for row in cur.fetchall():
            row = dict(row)
            new_candidate_id = candidate_id_map.get(row["candidate_id"])
            if not new_candidate_id:
                continue
            session.add(ResumeData(
                candidate_id=new_candidate_id,
                filename=row["filename"] or "",
                mime_type=row["mime_type"] or "",
                file_path=row["file_path"] or "",
                extracted_text=row["extracted_text"] or "",
                parsed_json=_loads(row["parsed_json"], {}),
                name=row["name"] or "",
                email=row["email"] or "",
                phone=row["phone"] or "",
                linkedin=row["linkedin"] or "",
                github=row["github"] or "",
                portfolio=row["portfolio"] or "",
                education=_loads(row["education"], []),
                skills=_loads(row["skills"], []),
                experience=_loads(row["experience"], []),
                projects=_loads(row["projects"], []),
                certifications=_loads(row["certifications"], []),
                languages=_loads(row["languages"], []),
                achievements=_loads(row["achievements"], []),
                status=row["status"] or "Uploaded",
            ))
            resume_count += 1
        print(f"Resume data: {resume_count} migrated")

        # ---- Applications ----
        application_count = 0
        cur.execute("SELECT * FROM applications")
        for row in cur.fetchall():
            row = dict(row)
            new_candidate_id = candidate_id_map.get(row["candidate_id"])
            new_job_id = job_id_map.get(row["job_id"])
            if not new_candidate_id or not new_job_id:
                continue
            session.add(Application(
                candidate_id=new_candidate_id,
                job_id=new_job_id,
                status=row["status"] or "submitted",
                match_score=row["match_score"] or 0,
                ai_summary=row["ai_summary"] or "",
                recruiter_notes=row["recruiter_notes"] or "",
            ))
            application_count += 1
        print(f"Applications: {application_count} migrated")

        # ---- Interviews ----
        interview_count = 0
        cur.execute("SELECT * FROM interviews")
        for row in cur.fetchall():
            row = dict(row)
            new_candidate_id = candidate_id_map.get(row["candidate_id"])
            if not new_candidate_id:
                continue
            session.add(Interview(
                candidate_id=new_candidate_id,
                job_id=job_id_map.get(row["job_id"]) if row["job_id"] else None,
                date=row["date"] or "",
                time=row["time"] or "",
                duration=row["duration"] or 60,
                round=row["round"] or "",
                type=row["type"] or "Online",
                meeting_platform=row["meeting_platform"] or "Google Meet",
                meeting_link=row["meeting_link"] or "",
                panel_members=_loads(row["panel_members"], []),
                recruiter_name=row["recruiter_name"] or "",
                status=row["status"] or "Scheduled",
                feedback=_loads(row["feedback"], {}),
                decision=row["decision"] or "",
            ))
            interview_count += 1
        print(f"Interviews: {interview_count} migrated")

        # ---- Employees ----
        employee_count = 0
        cur.execute("SELECT * FROM employees")
        for row in cur.fetchall():
            row = dict(row)
            session.add(Employee(
                candidate_id=candidate_id_map.get(row["candidate_id"]) if row["candidate_id"] else None,
                name=row["name"] or "",
                email=row["email"] or "",
                phone=row["phone"] or "",
                department=row["department"] or "",
                designation=row["designation"] or "",
                joining_date=row["joining_date"] or "",
                status=row["status"] or "Active",
                work_location=row["work_location"] or "Remote",
                reporting_manager=row["reporting_manager"] or "",
                current_project=row["current_project"] or "",
                avatar_url=row["avatar_url"] or "",
                skills=_loads(row["skills"], []),
                projects=_loads(row["projects"], []),
                performance_history=_loads(row["performance_history"], []),
                talent_insights=_loads(row["talent_insights"], {}),
                notes=_loads(row["notes"], []),
            ))
            employee_count += 1
        print(f"Employees: {employee_count} migrated")

        # ---- Activities ----
        activity_count = 0
        cur.execute("SELECT * FROM activities")
        for row in cur.fetchall():
            row = dict(row)
            session.add(Activity(
                icon=row["icon"] or "",
                title=row["title"] or "",
                description=row["description"] or "",
                time=row["time"] or "",
            ))
            activity_count += 1
        print(f"Activities: {activity_count} migrated")

        await session.commit()

    con.close()
    print("\nMigration complete.")


if __name__ == "__main__":
    import asyncio
    asyncio.run(migrate())
