import asyncio
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from backend.database.session import get_db_session
from backend.models.entities import Candidate, Application, Job

async def check_database():
    async with get_db_session() as session:
        # Get candidates
        result = await session.execute(select(Candidate))
        candidates = result.scalars().all()
        print("Candidates:")
        for c in candidates:
            print(f"  ID: {c.id}, Name: {c.name}, Email: {c.email}, Status: {c.status}")

        # Get applications with related job and candidate
        result = await session.execute(
            select(Application)
            .options(
                selectinload(Application.candidate),
                selectinload(Application.job)
            )
        )
        applications = result.scalars().all()
        print("\nApplications:")
        for a in applications:
            print(f"  ID: {a.id}, Candidate: {a.candidate.name if a.candidate else 'None'}, Job: {a.job.title if a.job else 'None'}, Status: {a.status}")

        # Get jobs
        result = await session.execute(select(Job))
        jobs = result.scalars().all()
        print("\nJobs:")
        for j in jobs:
            print(f"  ID: {j.id}, Title: {j.title}, Status: {j.status}, Applications Count: {j.applications_count}")

if __name__ == "__main__":
    asyncio.run(check_database())
