#!/usr/bin/env python3
"""
Repair script to backfill application_id for orphaned interviews.
Only auto-links when match is unambiguous (exactly one matching application).
"""

import asyncio
import csv
from datetime import datetime
from pathlib import Path

from sqlalchemy import select, update

from backend.database.session import get_db_session
from backend.models.entities import Interview, Application, Candidate, Job


async def repair_orphaned_interviews():
    """Backfill application_id for orphaned interviews where match is unambiguous."""
    
    async with get_db_session() as session:
        # Query all interviews with NULL application_id
        stmt = select(Interview).where(Interview.application_id.is_(None))
        result = await session.execute(stmt)
        orphaned = result.scalars().all()
        
        print(f"Found {len(orphaned)} orphaned interviews")
        print("=" * 80)
        
        # Track changes for audit log
        audit_log = []
        auto_linked = 0
        ambiguous = 0
        true_orphans = 0
        
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
            
            # Find matching applications
            matching_apps = []
            if iv.candidate_id and iv.job_id:
                app_result = await session.execute(
                    select(Application).where(
                        Application.candidate_id == iv.candidate_id,
                        Application.job_id == iv.job_id
                    )
                )
                matching_apps = app_result.scalars().all()
            
            if len(matching_apps) == 1:
                # Unambiguous match - auto-link
                app = matching_apps[0]
                print(f"✅ Auto-linking Interview {iv.id} → Application {app.id}")
                print(f"   Candidate: {candidate.name if candidate else 'N/A'} (ID: {iv.candidate_id})")
                print(f"   Job: {job.title if job else 'N/A'} (ID: {iv.job_id})")
                print(f"   Application Status: {app.status}")
                
                # Update the interview
                iv.application_id = app.id
                await session.flush()
                
                audit_log.append({
                    "timestamp": datetime.now().isoformat(),
                    "action": "AUTO_LINKED",
                    "interview_id": iv.id,
                    "candidate_id": iv.candidate_id,
                    "candidate_name": candidate.name if candidate else "N/A",
                    "job_id": iv.job_id,
                    "job_title": job.title if job else "N/A",
                    "application_id": app.id,
                    "application_status": app.status,
                    "match_count": len(matching_apps),
                    "notes": "Unambiguous match: exactly one application for candidate+job"
                })
                auto_linked += 1
                
            elif len(matching_apps) > 1:
                # Ambiguous - flag for manual review
                print(f"⚠️  AMBIGUOUS: Interview {iv.id} has {len(matching_apps)} matching applications")
                print(f"   Candidate: {candidate.name if candidate else 'N/A'} (ID: {iv.candidate_id})")
                print(f"   Job: {job.title if job else 'N/A'} (ID: {iv.job_id})")
                for app in matching_apps:
                    print(f"     - App {app.id}: status={app.status}")
                
                audit_log.append({
                    "timestamp": datetime.now().isoformat(),
                    "action": "AMBIGUOUS_MANUAL_REVIEW",
                    "interview_id": iv.id,
                    "candidate_id": iv.candidate_id,
                    "candidate_name": candidate.name if candidate else "N/A",
                    "job_id": iv.job_id,
                    "job_title": job.title if job else "N/A",
                    "application_id": None,
                    "application_status": None,
                    "match_count": len(matching_apps),
                    "notes": f"Ambiguous: {len(matching_apps)} applications found. Manual review required."
                })
                ambiguous += 1
                
            else:
                # True orphan - no matching application
                print(f"❌ TRUE ORPHAN: Interview {iv.id} has NO matching application")
                print(f"   Candidate: {candidate.name if candidate else 'N/A'} (ID: {iv.candidate_id})")
                print(f"   Job: {job.title if job else 'N/A'} (ID: {iv.job_id})")
                
                audit_log.append({
                    "timestamp": datetime.now().isoformat(),
                    "action": "TRUE_ORPHAN_NO_APPLICATION",
                    "interview_id": iv.id,
                    "candidate_id": iv.candidate_id,
                    "candidate_name": candidate.name if candidate else "N/A",
                    "job_id": iv.job_id,
                    "job_title": job.title if job else "N/A",
                    "application_id": None,
                    "application_status": None,
                    "match_count": 0,
                    "notes": "No application exists for this candidate+job combination. Requires manual intervention."
                })
                true_orphans += 1
            
            print()
        
        # Commit all changes
        if auto_linked > 0:
            await session.commit()
            print(f"✅ Committed {auto_linked} auto-linked interviews")
        else:
            print("No auto-links to commit")
        
        # Write audit log
        if audit_log:
            report_dir = Path("storage/reports")
            report_dir.mkdir(parents=True, exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            csv_path = report_dir / f"interview_backfill_log_{timestamp}.csv"
            
            fieldnames = list(audit_log[0].keys())
            with open(csv_path, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(audit_log)
            
            print(f"\nAudit log written to: {csv_path}")
        
        # Summary
        print("\n" + "=" * 80)
        print("REPAIR SUMMARY")
        print("=" * 80)
        print(f"Total orphaned interviews: {len(orphaned)}")
        print(f"  ✅ Auto-linked: {auto_linked}")
        print(f"  ⚠️  Ambiguous (manual review): {ambiguous}")
        print(f"  ❌ True orphans (no application): {true_orphans}")
        
        return {
            "total": len(orphaned),
            "auto_linked": auto_linked,
            "ambiguous": ambiguous,
            "true_orphans": true_orphans,
            "audit_log": audit_log
        }


if __name__ == "__main__":
    asyncio.run(repair_orphaned_interviews())