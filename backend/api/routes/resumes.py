import uuid
import asyncio
import aiofiles
from pathlib import Path
from typing import List, Optional
from fastapi import APIRouter, File, Form, HTTPException, UploadFile, BackgroundTasks
from sqlalchemy import desc, select
from backend.core.config import settings
from backend.database.session import get_db_session
from backend.database.data_store import data_store
from backend.models.entities import ResumeData
from backend.schemas.entities import CandidateCreate, CandidateRead, BatchUploadStatus, ResumeDraftResponse
from backend.scripts.services.resume_parser_service import extract_text_from_document
from backend.scripts.services.ai_resume_service import parse_resume_to_json, evaluate_candidate_match

router = APIRouter()

MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB
ALLOWED_EXTENSIONS = {".pdf", ".docx", ".txt"}

# In-memory tracker for bulk uploads
_batch_jobs = {}

# Semaphore to limit Ollama concurrency
_ai_semaphore = asyncio.Semaphore(5)

def validate_file(file: UploadFile) -> str:
    ext = Path(file.filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise ValueError(f"Unsupported file format: {ext}. Allowed: PDF, DOCX, TXT.")
    return ext


async def process_single_resume(file: UploadFile, job_id: Optional[int] = None) -> dict:
    validate_file(file)
    contents = await file.read()
    if len(contents) > MAX_FILE_SIZE:
        raise ValueError(f"File {file.filename} exceeds 5MB limit.")
        
    raw_text = extract_text_from_document(contents, file.filename)
    if not raw_text.strip():
        raise ValueError(f"No text extracted from {file.filename}.")
        
    async with _ai_semaphore:
        try:
            parsed_json = await parse_resume_to_json(raw_text)
            
            if job_id:
                job = await data_store.get_job(job_id)
                if job:
                    job_reqs = {
                        "title": job.get("title"),
                        "experience": job.get("experience_required"),
                        "required_skills": job.get("requirements", []) + job.get("required_skills", []),
                        "preferred_skills": job.get("preferred_skills", [])
                    }
                    eval_result = await evaluate_candidate_match(parsed_json, job_reqs)
                    parsed_json.update(eval_result)
        except Exception as e:
            # Fallback if AI fails: save what we have as raw text
            parsed_json = {"name": Path(file.filename).stem, "summary": "AI analysis pending/failed. See raw text.", "error": str(e)}

    # We must save a candidate draft now so it has an ID
    cand = await data_store.upsert_candidate_from_resume(
        type('obj', (object,), parsed_json)(),  # Quick hack to pass dict as obj since data_store expects obj.name
        default_title="Applicant"
    )
    
    # Actually, data_store expects a Pydantic model for upsert_candidate_from_resume (it accesses parsed.name etc)
    # Let's just create the candidate directly
    # Better: modify the dict to include the parsed fields, then create CandidateCreate
    payload = CandidateCreate(
        name=parsed_json.get("name") or Path(file.filename).stem,
        email=parsed_json.get("email") or f"{uuid.uuid4().hex[:8]}@example.com",
        phone=parsed_json.get("phone", ""),
        linkedin=parsed_json.get("linkedin", ""),
        github=parsed_json.get("github", ""),
        status="Applied",
        match_score=parsed_json.get("match_score", 0),
        skill_match_breakdown=parsed_json.get("skill_match_breakdown", {}),
        hire_recommendation=parsed_json.get("hire_recommendation", ""),
        summary=parsed_json.get("resume_summary", parsed_json.get("summary", ""))
    )
    
    cand = await data_store.create_candidate(payload)
    
    # Save the resume record to tie raw text
    await data_store.store_resume_record(
        candidate_id=cand["id"],
        filename=file.filename,
        mime_type=file.content_type,
        file_path="",
        parsed=parsed_json,
        raw_text=raw_text
    )
    
    return {"candidate": cand, "raw_text": raw_text, "parsed_json": parsed_json}


@router.post("/upload")
async def upload_resume(file: UploadFile = File(...), job_id: Optional[int] = Form(None)):
    try:
        result = await process_single_resume(file, job_id)
        return ResumeDraftResponse(
            candidate_id=result["candidate"]["id"],
            raw_text=result["raw_text"],
            parsed_json=result["parsed_json"]
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


async def background_batch_process(batch_id: str, files: List[UploadFile], job_id: Optional[int]):
    _batch_jobs[batch_id]["status"] = "processing"
    
    async def _safe_process(file):
        try:
            await process_single_resume(file, job_id)
            _batch_jobs[batch_id]["successful"] += 1
        except Exception:
            _batch_jobs[batch_id]["failed"] += 1
        finally:
            _batch_jobs[batch_id]["processed_files"] += 1

    tasks = [_safe_process(f) for f in files]
    await asyncio.gather(*tasks)
    
    _batch_jobs[batch_id]["is_complete"] = True
    _batch_jobs[batch_id]["status"] = "completed"


@router.post("/bulk-upload", response_model=BatchUploadStatus)
async def bulk_upload_resumes(
    background_tasks: BackgroundTasks,
    files: List[UploadFile] = File(...), 
    job_id: Optional[int] = Form(None)
):
    batch_id = uuid.uuid4().hex
    _batch_jobs[batch_id] = {
        "batch_id": batch_id,
        "total_files": len(files),
        "processed_files": 0,
        "successful": 0,
        "failed": 0,
        "is_complete": False,
        "status": "queued"
    }
    
    # We must read files into memory because FastAPI will close the file pointers after response
    memory_files = []
    for f in files:
        validate_file(f)
        contents = await f.read()
        if len(contents) > MAX_FILE_SIZE:
            raise HTTPException(status_code=413, detail=f"File {f.filename} exceeds 5MB.")
            
        class FakeUploadFile:
            def __init__(self, filename, content_type, contents):
                self.filename = filename
                self.content_type = content_type
                self._contents = contents
            async def read(self):
                return self._contents
                
        memory_files.append(FakeUploadFile(f.filename, f.content_type, contents))
        
    background_tasks.add_task(background_batch_process, batch_id, memory_files, job_id)
    return _batch_jobs[batch_id]


@router.get("/bulk-upload/{batch_id}/status", response_model=BatchUploadStatus)
async def get_batch_status(batch_id: str):
    if batch_id not in _batch_jobs:
        raise HTTPException(status_code=404, detail="Batch not found")
    return _batch_jobs[batch_id]


@router.get("/{candidate_id}/preview", response_model=ResumeDraftResponse)
async def preview_candidate(candidate_id: int):
    resume = await data_store.get_latest_candidate_resume(candidate_id)
    if not resume:
        raise HTTPException(status_code=404, detail="Resume data not found for candidate")
        
    return ResumeDraftResponse(
        candidate_id=candidate_id,
        raw_text=resume.get("extracted_text", ""),
        parsed_json=resume.get("parsed_json", {})
    )


@router.put("/{candidate_id}", response_model=CandidateRead)
async def update_candidate(candidate_id: int, payload: CandidateCreate):
    try:
        return await data_store.update_candidate(candidate_id, payload)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/history")
async def get_resume_history(limit: int = 50):
    """Get recent resume uploads with parsed data for the frontend history panel."""
    async with get_db_session() as session:
        stmt = select(ResumeData).order_by(desc(ResumeData.created_at)).limit(limit)
        res = await session.execute(stmt)
        resumes = res.scalars().all()
        history = []
        for r in resumes:
            history.append({
                "id": r.id,
                "candidate_id": r.candidate_id,
                "filename": r.filename,
                "name": r.name or "Unknown",
                "email": r.email or "",
                "extracted_text": r.extracted_text or "",
                "parsed_json": r.parsed_json or {},
                "created_at": str(r.created_at) if r.created_at else "",
                "status": r.status or "Parsed"
            })
        return history


@router.post("/parse-text")
async def parse_resume_text(text: str = Form(...), filename: str = Form("pasted_resume.txt")):
    """Parse resume text directly (for copy-paste scenarios)."""
    try:
        raw_text = text
        if not raw_text.strip():
            raise ValueError("No text provided.")
            
        async with _ai_semaphore:
            try:
                parsed_json = await parse_resume_to_json(raw_text)
            except Exception as e:
                parsed_json = {"name": filename, "summary": "AI analysis pending/failed. See raw text.", "error": str(e)}
        
        # Create candidate
        payload = CandidateCreate(
            name=parsed_json.get("name") or filename,
            email=parsed_json.get("email") or f"{uuid.uuid4().hex[:8]}@example.com",
            phone=parsed_json.get("phone", ""),
            linkedin=parsed_json.get("linkedin", ""),
            github=parsed_json.get("github", ""),
            status="Applied",
            match_score=parsed_json.get("match_score", 0),
            skill_match_breakdown=parsed_json.get("skill_match_breakdown", {}),
            hire_recommendation=parsed_json.get("hire_recommendation", ""),
            summary=parsed_json.get("resume_summary", parsed_json.get("summary", ""))
        )
        
        cand = await data_store.create_candidate(payload)
        
        # Save resume record
        await data_store.store_resume_record(
            candidate_id=cand["id"],
            filename=filename,
            mime_type="text/plain",
            file_path="",
            parsed=parsed_json,
            raw_text=raw_text
        )
        
        return ResumeDraftResponse(
            candidate_id=cand["id"],
            raw_text=raw_text,
            parsed_json=parsed_json
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
