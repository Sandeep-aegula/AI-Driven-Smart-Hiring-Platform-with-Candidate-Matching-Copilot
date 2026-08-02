#!/usr/bin/env python3
"""
Audit script to find all orphaned interviews (interviews with NULL application_id).
"""

import asyncio
import csv
from datetime import datetime
from pathlib import Path

from sqlalchemy import select

from backend.database.session import get_db_session
from backend.models.entities import Interview, Application, Candidate, Job


async def audit_orphaned_interviews():
    """Find all interviews with NULL application_id."""
    
    async with get_db_session() as session:
        # Query all interviews with NULL application_id
        stmt = select(Interview).where(Interview.application_id.is_(None))
        result = await session.execute(stmt)
        orphaned = result.scalars().all()
        
        print(f"Found {len(orphaned)} orphaned interviews (application_id IS NULL)")
        print("=" * 100)
        
        # Prepare data for CSV
        csv_rows = []
        
        for iv in orphaned:
            # Get candidate info
            candidate = None
            if iv.candidate_id:
                cand_result = await session.execute(
                    select(Candidate).where(Candidate.id == iv.candidate_id)
                )
                candidate = cand_result.scalar_one_or_none()
            
            # Get job info
            job = None
            if iv.job_id:
                job_result = await session.execute(
                    select(Job).where(Job.id == iv.job_id)
                )
                job = job_result.scalar_one_or_none()
            
            # Check if there's a matching application
            matching_apps = []
            if iv.candidate_id and iv.job_id:
                app_result = await session.execute(
                    select(Application).where(
                        Application.candidate_id == iv.candidate_id,
                        Application.job_id == iv.job_id
                    )
                )
                matching_apps = app_result.scalars().all()
            
            row = {
                "interview_id": iv.id,
                "candidate_id": iv.candidate_id,
                "candidate_name": candidate.name if candidate else "N/A",
                "candidate_email": candidate.email if candidate else "N/A",
                "job_id": iv.job_id,
                "job_title": job.title if job else "N/A",
                "job_department": job.department if job else "N/A",
                "scheduled_date": iv.date,
                "scheduled_time": iv.time,
                "round": iv.round,
                "round_number": iv.round_number,
                "status": iv.status,
                "decision": iv.decision,
                "created_at": iv.created_at.isoformat() if iv.created_at else "N/A",
                "updated_at": iv.updated_at.isoformat() if iv.updated_at else "N/A",
                "matching_applications_count": len(matching_apps),
                "matching_application_ids": ",".join(str(a.id) for a in matching_apps),
                "matching_application_statuses": ",".join(a.status for a in matching_apps),
            }
            csv_rows.append(row)
            
            # Print summary
            print(f"Interview ID: {iv.id}")
            print(f"  Candidate: {row['candidate_name']} ({row['candidate_email']}) [ID: {iv.candidate_id}]")
            print(f"  Job: {row['job_title']} ({row['job_department']}) [ID: {iv.job_id}]")
            print(f"  Scheduled: {iv.date} at {iv.time} (Round {iv.round_number}: {iv.round})")
            print(f"  Status: {iv.status}, Decision: {iv.decision or 'None'}")
            print(f"  Matching Applications: {len(matching_apps)}")
            for app in matching_apps:
                print(f"    - App ID: {app.id}, Status: {app.status}")
            print()
        
        # Write CSV report
        if csv_rows:
            report_dir = Path("storage/reports")
            report_dir.mkdir(parents=True, exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            csv_path = report_dir / f"orphaned_interviews_{timestamp}.csv"
            
            fieldnames = list(csv_rows[0].keys())
            with open(csv_path, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(csv_rows)
            
            print(f"CSV report written to: {csv_path}")
        
        return orphaned, csv_rows


if __name__ == "__main__":
    asyncio.run(audit_orphaned_interviews())