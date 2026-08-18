import asyncio
import os
import sys
from datetime import datetime

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from sqlalchemy import select
from backend.database.session import get_db_session
from backend.models.entities import (
    Candidate,
    Job,
    Application,
    Onboarding,
    OnboardingStatus,
    OnboardingDocumentRequirement,
    OnboardingDocument,
    OnboardingDocumentStatus,
    ApplicationWorkflowStatus
)

async def seed_onboarding_candidate():
    async with get_db_session() as session:
        test_email = "onboarding.test@hirepilot.local"
        
        # Check if candidate exists
        stmt = select(Candidate).where(Candidate.email == test_email)
        result = await session.execute(stmt)
        candidate = result.scalar_one_or_none()
        
        created = False
        if not candidate:
            print("Candidate not found. Creating candidate...")
            candidate = Candidate(
                name="Onboarding Test Candidate",
                email=test_email,
                phone="9876543210",
                location="Remote",
                status="Hired"
            )
            session.add(candidate)
            await session.flush()
            created = True
        else:
            print("Candidate already exists.")
            
        # Get or create Job
        stmt = select(Job).where(Job.title == "Frontend Developer", Job.department == "Engineering")
        result = await session.execute(stmt)
        job = result.scalar_one_or_none()
        
        if not job:
            job = Job(
                title="Frontend Developer",
                department="Engineering",
                location="Remote",
                work_mode="Remote",
                status="Active"
            )
            session.add(job)
            await session.flush()
            
        # Get or create Application
        stmt = select(Application).where(Application.candidate_id == candidate.id, Application.job_id == job.id)
        result = await session.execute(stmt)
        application = result.scalar_one_or_none()
        
        now = datetime.utcnow()
        if not application:
            application = Application(
                candidate_id=candidate.id,
                job_id=job.id,
                status=ApplicationWorkflowStatus.hired.value,
                final_decision="Selected",
                final_decision_at=now,
                final_selected_by="System Seed"
            )
            session.add(application)
            await session.flush()
        else:
            application.status = ApplicationWorkflowStatus.hired.value
            application.final_decision = "Selected"
            application.final_decision_at = application.final_decision_at or now
            
        # Get or create Onboarding
        stmt = select(Onboarding).where(Onboarding.application_id == application.id)
        result = await session.execute(stmt)
        onboarding = result.scalar_one_or_none()
        
        if not onboarding:
            onboarding = Onboarding(
                candidate_id=candidate.id,
                application_id=application.id,
                job_id=job.id,
                department=job.department,
                designation=job.title,
                joining_date=now.date().isoformat(),
                selected_at=now,
                status=OnboardingStatus.pending.value,
                ready_for_onboarding=False
            )
            session.add(onboarding)
            await session.flush()
            
            # Create default document requirements and documents
            from backend.scripts.services.onboarding_workflow_service import DEFAULT_DOCUMENT_TYPES
            for doc_type, doc_name, required, order in DEFAULT_DOCUMENT_TYPES:
                req = OnboardingDocumentRequirement(
                    onboarding_id=onboarding.id,
                    document_type=doc_type,
                    document_name=doc_name,
                    required=required,
                    display_order=order,
                    is_custom=False
                )
                session.add(req)
                await session.flush()
                
                # Add dummy document for required ones to simulate upload
                if required:
                    doc = OnboardingDocument(
                        onboarding_id=onboarding.id,
                        requirement_id=req.id,
                        original_filename=f"dummy_{doc_type}.pdf",
                        stored_filename=f"dummy_{doc_type}_{candidate.id}.pdf",
                        storage_path="/tmp/dummy",
                        status=OnboardingDocumentStatus.uploaded.value,
                        is_current=True
                    )
                    session.add(doc)
            
            onboarding.status = OnboardingStatus.documents_uploaded.value
        
        await session.commit()
        
        print("\n--- Seed Verification ---")
        print(f"Candidate ID: {candidate.id}")
        print(f"Application ID: {application.id}")
        print(f"Job ID: {job.id}")
        print(f"Onboarding ID: {onboarding.id}")
        print(f"Application Status: {application.status}")
        print(f"Final Decision: {application.final_decision}")
        print(f"Onboarding Status: {onboarding.status}")
        print("-------------------------\n")

if __name__ == "__main__":
    asyncio.run(seed_onboarding_candidate())