from __future__ import annotations

import logging
import os
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from fastapi.responses import FileResponse
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.core.config import settings
from backend.database.session import get_db
from backend.models.entities import (
    Onboarding,
    OnboardingDocumentRequirement,
    OnboardingDocument,
    Candidate,
    Application,
    Job,
    OnboardingStatus,
    OnboardingDocumentStatus,
)

logger = logging.getLogger(__name__)
router = APIRouter()

ALLOWED_EXTENSIONS = {".pdf", ".png", ".jpg", ".jpeg", ".docx"}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB

DEFAULT_DOCUMENT_TYPES = [
    ("Government ID", "Government ID", True, 1),
    ("Address Proof", "Address Proof", True, 2),
    ("Educational Certificates", "Educational Certificates", True, 3),
    ("Previous Employment Documents", "Previous Employment Documents", False, 4),
    ("Offer Acceptance", "Offer Acceptance Letter", True, 5),
    ("Tax or Payroll Documents", "Tax/PAN/Aadhar Documents", False, 6),
    ("Passport Photograph", "Passport Size Photo", True, 7),
]


def _validate_file(file: UploadFile) -> None:
    """Validate file extension and size."""
    if not file.filename:
        raise ValueError("Filename is required")

    ext = Path(file.filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise ValueError(
            f"File type '{ext}' not allowed. "
            f"Allowed types: {', '.join(ALLOWED_EXTENSIONS)}"
        )


def _generate_safe_filename(original_filename: str) -> str:
    """Generate a unique safe filename."""
    ext = Path(original_filename).suffix.lower()
    unique_name = f"{uuid.uuid4().hex}{ext}"
    return unique_name


@router.get("")
async def list_onboarding_candidates(
    search: str = "",
    job_id: Optional[int] = None,
    status: str = "All",
    verification_status: str = "All",
    db: AsyncSession = Depends(get_db),
) -> list[dict]:
    """List all onboarding candidates with filters."""
    query = select(Onboarding).options(
        selectinload(Onboarding.candidate),
        selectinload(Onboarding.application),
        selectinload(Onboarding.job),
        selectinload(Onboarding.document_requirements).selectinload(
            OnboardingDocumentRequirement.documents
        ),
    )

    if search:
        query = query.join(Candidate).where(
            Candidate.name.contains(search) | Candidate.email.contains(search)
        )

    if job_id:
        query = query.where(Onboarding.job_id == job_id)

    if status != "All":
        query = query.where(Onboarding.status == status)

    result = await db.execute(query)
    onboardings = result.scalars().all()

    response = []
    for onboarding in onboardings:
        # Calculate document completion
        total_required = sum(1 for req in onboarding.document_requirements if req.required)
        verified_count = 0

        for req in onboarding.document_requirements:
            if not req.required:
                continue
            current_docs = [d for d in req.documents if d.is_current]
            if current_docs and current_docs[0].status == OnboardingDocumentStatus.verified.value:
                verified_count += 1

        completion_percentage = (verified_count / total_required * 100) if total_required > 0 else 0

        response.append({
            "id": onboarding.id,
            "candidate_id": onboarding.candidate_id,
            "candidate_name": onboarding.candidate.name,
            "candidate_email": onboarding.candidate.email,
            "candidate_phone": onboarding.candidate.phone,
            "job_id": onboarding.job_id,
            "job_title": onboarding.job.title,
            "department": onboarding.department or onboarding.job.department,
            "designation": onboarding.designation,
            "joining_date": onboarding.joining_date,
            "status": onboarding.status,
            "completion_percentage": round(completion_percentage, 1),
            "total_required": total_required,
            "verified_count": verified_count,
            "created_at": onboarding.created_at.isoformat() if onboarding.created_at else None,
        })

    return response


@router.get("/{onboarding_id}")
async def get_onboarding_details(
    onboarding_id: int,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Get detailed onboarding information including documents."""
    query = select(Onboarding).options(
        selectinload(Onboarding.candidate),
        selectinload(Onboarding.application),
        selectinload(Onboarding.job),
        selectinload(Onboarding.document_requirements).selectinload(
            OnboardingDocumentRequirement.documents
        ),
    ).where(Onboarding.id == onboarding_id)

    result = await db.execute(query)
    onboarding = result.scalar_one_or_none()

    if not onboarding:
        raise HTTPException(status_code=404, detail="Onboarding record not found")

    # Build document requirements response
    requirements_list = []
    total_required = 0
    uploaded_count = 0
    verified_count = 0
    pending_count = 0
    rejected_count = 0
    missing_count = 0

    for req in onboarding.document_requirements:
        current_docs = [d for d in req.documents if d.is_current]
        current_doc = current_docs[0] if current_docs else None

        doc_status = OnboardingDocumentStatus.missing.value
        if current_doc:
            doc_status = current_doc.status
            if req.required:
                if current_doc.status == OnboardingDocumentStatus.uploaded.value:
                    uploaded_count += 1
                    pending_count += 1
                elif current_doc.status == OnboardingDocumentStatus.verified.value:
                    verified_count += 1
                elif current_doc.status == OnboardingDocumentStatus.rejected.value:
                    rejected_count += 1
                elif current_doc.status == OnboardingDocumentStatus.reupload_requested.value:
                    pending_count += 1
        else:
            if req.required:
                missing_count += 1

        if req.required:
            total_required += 1

        # Get all versions for history
        all_versions = sorted(req.documents, key=lambda d: d.version, reverse=True)

        requirements_list.append({
            "requirement_id": req.id,
            "document_type": req.document_type,
            "document_name": req.document_name,
            "required": req.required,
            "is_custom": req.is_custom,
            "display_order": req.display_order,
            "current_status": doc_status,
            "current_document": {
                "document_id": current_doc.id,
                "version": current_doc.version,
                "original_filename": current_doc.original_filename,
                "mime_type": current_doc.mime_type,
                "file_size": current_doc.file_size,
                "uploaded_at": current_doc.uploaded_at.isoformat() if current_doc.uploaded_at else None,
                "verified_at": current_doc.verified_at.isoformat() if current_doc.verified_at else None,
                "verified_by": current_doc.verified_by,
                "rejected_at": current_doc.rejected_at.isoformat() if current_doc.rejected_at else None,
                "rejected_by": current_doc.rejected_by,
                "rejection_reason": current_doc.rejection_reason,
                "reupload_message": current_doc.reupload_message,
            } if current_doc else None,
            "version_history": [
                {
                    "document_id": doc.id,
                    "version": doc.version,
                    "original_filename": doc.original_filename,
                    "status": doc.status,
                    "uploaded_at": doc.uploaded_at.isoformat() if doc.uploaded_at else None,
                    "verified_at": doc.verified_at.isoformat() if doc.verified_at else None,
                    "verified_by": doc.verified_by,
                    "rejected_at": doc.rejected_at.isoformat() if doc.rejected_at else None,
                    "rejected_by": doc.rejected_by,
                    "rejection_reason": doc.rejection_reason,
                }
                for doc in all_versions
            ],
        })

    completion_percentage = (verified_count / total_required * 100) if total_required > 0 else 0
    ready_for_onboarding = (
        total_required > 0
        and verified_count == total_required
        and missing_count == 0
    )

    return {
        "id": onboarding.id,
        "candidate": {
            "id": onboarding.candidate.id,
            "name": onboarding.candidate.name,
            "email": onboarding.candidate.email,
            "phone": onboarding.candidate.phone,
            "location": onboarding.candidate.location,
        },
        "application_id": onboarding.application_id,
        "job": {
            "id": onboarding.job.id,
            "title": onboarding.job.title,
            "department": onboarding.job.department,
        },
        "department": onboarding.department or onboarding.job.department,
        "designation": onboarding.designation,
        "joining_date": onboarding.joining_date,
        "status": onboarding.status,
        "created_at": onboarding.created_at.isoformat() if onboarding.created_at else None,
        "updated_at": onboarding.updated_at.isoformat() if onboarding.updated_at else None,
        "progress": {
            "total_required": total_required,
            "uploaded": uploaded_count,
            "verified": verified_count,
            "pending": pending_count,
            "rejected": rejected_count,
            "missing": missing_count,
            "completion_percentage": round(completion_percentage, 1),
            "ready_for_onboarding": ready_for_onboarding,
        },
        "document_requirements": requirements_list,
    }


@router.post("")
async def create_onboarding(
    candidate_id: int,
    application_id: int,
    job_id: int,
    department: str = "",
    designation: str = "",
    joining_date: str = "",
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Create a new onboarding record."""
    # Check for duplicate
    existing = await db.execute(
        select(Onboarding).where(
            and_(
                Onboarding.candidate_id == candidate_id,
                Onboarding.application_id == application_id,
                Onboarding.status != OnboardingStatus.onboarding_completed.value,
            )
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=400,
            detail="Active onboarding record already exists for this candidate and application",
        )

    # Create onboarding record
    onboarding = Onboarding(
        candidate_id=candidate_id,
        application_id=application_id,
        job_id=job_id,
        department=department,
        designation=designation,
        joining_date=joining_date,
        status=OnboardingStatus.pending.value,
    )
    db.add(onboarding)
    await db.flush()

    # Add default document requirements
    for doc_type, doc_name, required, order in DEFAULT_DOCUMENT_TYPES:
        requirement = OnboardingDocumentRequirement(
            onboarding_id=onboarding.id,
            document_type=doc_type,
            document_name=doc_name,
            required=required,
            display_order=order,
            is_custom=False,
        )
        db.add(requirement)

    await db.commit()
    await db.refresh(onboarding)

    return {"id": onboarding.id, "message": "Onboarding record created successfully"}


@router.post("/{onboarding_id}/requirements")
async def add_document_requirement(
    onboarding_id: int,
    document_type: str = Form(...),
    document_name: str = Form(...),
    required: bool = Form(True),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Add a custom document requirement."""
    # Verify onboarding exists
    onboarding = await db.get(Onboarding, onboarding_id)
    if not onboarding:
        raise HTTPException(status_code=404, detail="Onboarding record not found")

    # Get max display order
    result = await db.execute(
        select(func.max(OnboardingDocumentRequirement.display_order)).where(
            OnboardingDocumentRequirement.onboarding_id == onboarding_id
        )
    )
    max_order = result.scalar() or 0

    requirement = OnboardingDocumentRequirement(
        onboarding_id=onboarding_id,
        document_type=document_type,
        document_name=document_name,
        required=required,
        display_order=max_order + 1,
        is_custom=True,
    )
    db.add(requirement)
    await db.commit()
    await db.refresh(requirement)

    return {
        "requirement_id": requirement.id,
        "message": "Document requirement added successfully",
    }


@router.patch("/{onboarding_id}/requirements/{requirement_id}")
async def update_document_requirement(
    onboarding_id: int,
    requirement_id: int,
    required: Optional[bool] = None,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Update a document requirement."""
    requirement = await db.get(OnboardingDocumentRequirement, requirement_id)
    if not requirement or requirement.onboarding_id != onboarding_id:
        raise HTTPException(status_code=404, detail="Requirement not found")

    if required is not None:
        requirement.required = required

    await db.commit()
    return {"message": "Requirement updated successfully"}


@router.delete("/{onboarding_id}/requirements/{requirement_id}")
async def delete_document_requirement(
    onboarding_id: int,
    requirement_id: int,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Delete a custom document requirement (only if no documents uploaded)."""
    requirement = await db.get(OnboardingDocumentRequirement, requirement_id)
    if not requirement or requirement.onboarding_id != onboarding_id:
        raise HTTPException(status_code=404, detail="Requirement not found")

    if not requirement.is_custom:
        raise HTTPException(
            status_code=400,
            detail="Cannot delete default document requirements",
        )

    if requirement.documents:
        raise HTTPException(
            status_code=400,
            detail="Cannot delete requirement with uploaded documents",
        )

    await db.delete(requirement)
    await db.commit()
    return {"message": "Requirement deleted successfully"}


@router.post("/documents/{requirement_id}/upload")
async def upload_document(
    requirement_id: int,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Upload a document for a requirement."""
    requirement = await db.get(OnboardingDocumentRequirement, requirement_id)
    if not requirement:
        raise HTTPException(status_code=404, detail="Requirement not found")

    # Validate file
    try:
        _validate_file(file)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    # Read file
    file_content = await file.read()
    file_size = len(file_content)

    if file_size > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=400,
            detail=f"File size exceeds maximum allowed size of {MAX_FILE_SIZE // (1024 * 1024)}MB",
        )

    # Mark previous versions as not current
    for doc in requirement.documents:
        doc.is_current = False

    # Get next version number
    max_version = max((d.version for d in requirement.documents), default=0)
    new_version = max_version + 1

    # Generate safe filename and save
    safe_filename = _generate_safe_filename(file.filename)
    upload_dir = Path(settings.uploads_dir) / "onboarding"
    upload_dir.mkdir(parents=True, exist_ok=True)

    file_path = upload_dir / safe_filename
    with open(file_path, "wb") as f:
        f.write(file_content)

    # Create document record
    document = OnboardingDocument(
        onboarding_id=requirement.onboarding_id,
        requirement_id=requirement_id,
        version=new_version,
        original_filename=file.filename,
        stored_filename=safe_filename,
        storage_path=str(file_path),
        mime_type=file.content_type or "",
        file_size=file_size,
        status=OnboardingDocumentStatus.uploaded.value,
        is_current=True,
    )
    db.add(document)

    # Update onboarding status if still pending
    onboarding = await db.get(Onboarding, requirement.onboarding_id)
    if onboarding and onboarding.status == OnboardingStatus.pending.value:
        onboarding.status = OnboardingStatus.documents_uploaded.value

    await db.commit()
    await db.refresh(document)

    return {
        "document_id": document.id,
        "version": document.version,
        "message": "Document uploaded successfully",
    }


@router.get("/documents/{document_id}/download")
async def download_document(
    document_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Download a document."""
    document = await db.get(OnboardingDocument, document_id)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    file_path = Path(document.storage_path)
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found on disk")

    return FileResponse(
        path=file_path,
        filename=document.original_filename,
        media_type=document.mime_type or "application/octet-stream",
    )


@router.post("/documents/{document_id}/verify")
async def verify_document(
    document_id: int,
    verified_by: str = Form("HR"),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Mark a document as verified."""
    document = await db.get(OnboardingDocument, document_id)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    if not document.is_current:
        raise HTTPException(
            status_code=400,
            detail="Only current document versions can be verified",
        )

    if document.status == OnboardingDocumentStatus.verified.value:
        return {"message": "Document is already verified"}

    document.status = OnboardingDocumentStatus.verified.value
    document.verified_at = datetime.utcnow()
    document.verified_by = verified_by

    # Update onboarding status
    onboarding = await db.get(Onboarding, document.onboarding_id)
    if onboarding:
        # Check if all required documents are verified
        query = select(OnboardingDocumentRequirement).options(
            selectinload(OnboardingDocumentRequirement.documents)
        ).where(OnboardingDocumentRequirement.onboarding_id == onboarding.id)

        result = await db.execute(query)
        requirements = result.scalars().all()

        all_verified = True
        for req in requirements:
            if not req.required:
                continue
            current_docs = [d for d in req.documents if d.is_current]
            if not current_docs or current_docs[0].status != OnboardingDocumentStatus.verified.value:
                all_verified = False
                break

        if all_verified:
            onboarding.status = OnboardingStatus.documents_verified.value
        else:
            onboarding.status = OnboardingStatus.under_review.value

    await db.commit()
    return {"message": "Document verified successfully"}


@router.post("/documents/{document_id}/reject")
async def reject_document(
    document_id: int,
    rejection_reason: str = Form(...),
    rejected_by: str = Form("HR"),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Reject a document."""
    document = await db.get(OnboardingDocument, document_id)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    if not document.is_current:
        raise HTTPException(
            status_code=400,
            detail="Only current document versions can be rejected",
        )

    if not rejection_reason.strip():
        raise HTTPException(status_code=400, detail="Rejection reason is required")

    document.status = OnboardingDocumentStatus.rejected.value
    document.rejected_at = datetime.utcnow()
    document.rejected_by = rejected_by
    document.rejection_reason = rejection_reason

    # Update onboarding status
    onboarding = await db.get(Onboarding, document.onboarding_id)
    if onboarding:
        onboarding.status = OnboardingStatus.documents_rejected.value

    await db.commit()
    return {"message": "Document rejected successfully"}


@router.post("/documents/{document_id}/request-reupload")
async def request_document_reupload(
    document_id: int,
    reupload_message: str = Form(...),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Request candidate to re-upload a document."""
    document = await db.get(OnboardingDocument, document_id)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    if not document.is_current:
        raise HTTPException(
            status_code=400,
            detail="Only current document versions can have re-upload requested",
        )

    if not reupload_message.strip():
        raise HTTPException(status_code=400, detail="Re-upload message is required")

    document.status = OnboardingDocumentStatus.reupload_requested.value
    document.reupload_message = reupload_message

    # Update onboarding status
    onboarding = await db.get(Onboarding, document.onboarding_id)
    if onboarding:
        onboarding.status = OnboardingStatus.documents_incomplete.value

    await db.commit()
    return {"message": "Re-upload requested successfully"}


@router.get("/{onboarding_id}/progress")
async def get_onboarding_progress(
    onboarding_id: int,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Get onboarding progress summary."""
    onboarding = await db.get(Onboarding, onboarding_id)
    if not onboarding:
        raise HTTPException(status_code=404, detail="Onboarding record not found")

    query = select(OnboardingDocumentRequirement).options(
        selectinload(OnboardingDocumentRequirement.documents)
    ).where(OnboardingDocumentRequirement.onboarding_id == onboarding_id)

    result = await db.execute(query)
    requirements = result.scalars().all()

    total_required = 0
    verified = 0
    uploaded = 0
    missing = 0
    rejected = 0

    for req in requirements:
        if not req.required:
            continue

        total_required += 1
        current_docs = [d for d in req.documents if d.is_current]

        if not current_docs:
            missing += 1
        else:
            doc = current_docs[0]
            if doc.status == OnboardingDocumentStatus.verified.value:
                verified += 1
            elif doc.status == OnboardingDocumentStatus.rejected.value:
                rejected += 1
            elif doc.status in [OnboardingDocumentStatus.uploaded.value, OnboardingDocumentStatus.under_review.value]:
                uploaded += 1

    completion_percentage = (verified / total_required * 100) if total_required > 0 else 0
    ready_for_onboarding = total_required > 0 and verified == total_required and missing == 0

    return {
        "total_required": total_required,
        "verified": verified,
        "uploaded": uploaded,
        "missing": missing,
        "rejected": rejected,
        "completion_percentage": round(completion_percentage, 1),
        "ready_for_onboarding": ready_for_onboarding,
    }
