import asyncio
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from backend.database.session import get_db_session
from backend.models.entities import Candidate, Application, Job, Resume, ResumeParseResult, ApplicationScore

async def check_details():
    async with get_db_session() as session:
        # Get application with relationships
        result = await session.execute(
            select(Application)
            .options(
                selectinload(Application.candidate),
                selectinload(Application.job),
                selectinload(Application.resumes),
                selectinload(Application.parse_results),
                selectinload(Application.scores),
            )
            .where(Application.id == 14)
        )
        app = result.scalar_one_or_none()
        if not app:
            print("Application not found")
            return
        print(f"Application ID: {app.id}")
        print(f"Status: {app.status}")
        print(f"Candidate: {app.candidate.name if app.candidate else 'None'} ({app.candidate.email})")
        print(f"Job: {app.job.title if app.job else 'None'}")
        print(f"Resumes count: {len(app.resumes)}")
        if app.resumes:
            r = app.resumes[0]
            print(f"  Resume ID: {r.id}")
            print(f"  Original filename: {r.original_filename}")
            print(f"  Stored filename: {r.stored_filename}")
            print(f"  Storage path: {r.storage_path}")
            print(f"  MIME type: {r.mime_type}")
            print(f"  File size: {r.file_size}")
            print(f"  File hash: {r.file_hash}")
        print(f"Parse results count: {len(app.parse_results)}")
        if app.parse_results:
            pr = app.parse_results[0]
            print(f"  Parser status: {pr.parser_status}")
            print(f"  Extracted name: {pr.extracted_name}")
            print(f"  Extracted email: {pr.extracted_email}")
            print(f"  Extracted phone: {pr.extracted_phone}")
            print(f"  Extracted skills: {pr.extracted_skills}")
            print(f"  Parsed at: {pr.parsed_at}")
        print(f"Scores count: {len(app.scores)}")
        if app.scores:
            s = app.scores[0]
            print(f"  ATS score: {s.ats_score}")
            print(f"  Skills score: {s.skills_score}")
            print(f"  Experience score: {s.experience_score}")
            print(f"  Education score: {s.education_score}")
            print(f"  Keyword score: {s.keyword_score}")
            print(f"  Job match score: {s.job_match_score}")
            print(f"  Recommendation: {s.recommendation}")
            print(f"  Strengths: {s.strengths}")
            print(f"  Gaps: {s.gaps}")
            print(f"  Scored at: {s.scored_at}")

if __name__ == "__main__":
    asyncio.run(check_details())
