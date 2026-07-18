from __future__ import annotations

from fastapi import APIRouter, HTTPException, File, UploadFile
from pydantic import BaseModel

from backend.schemas.entities import JobCreate, JobRead
from backend.database.data_store import data_store
from backend.services.recruitment import generate_job_description
from backend.services.ai_job_service import parse_document, generate_job_description as ai_generate_jd, regenerate_job_description as ai_regenerate_jd

router = APIRouter()

MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB

class RegenerateRequest(BaseModel):
    raw_text: str
    current_draft: dict

@router.post("/upload-and-generate")
async def upload_and_generate(file: UploadFile = File(...)):
    if not file.filename.lower().endswith((".pdf", ".docx", ".txt")):
        raise HTTPException(status_code=415, detail="Unsupported file format. Please upload PDF, DOCX, or TXT.")
        
    contents = await file.read()
    if len(contents) > MAX_FILE_SIZE:
        raise HTTPException(status_code=413, detail="File too large. Maximum size is 5MB.")
        
    try:
        raw_text = parse_document(contents, file.filename)
        draft = await ai_generate_jd(raw_text)
        return {"raw_text": raw_text, "draft": draft}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/{job_id}/regenerate")
async def regenerate_job(job_id: int, payload: RegenerateRequest):
    draft = await ai_regenerate_jd(payload.raw_text, payload.current_draft)
    return {"draft": draft}


@router.get("", response_model=list[JobRead])
async def get_jobs(search: str = "", department: str = "All", status: str = "All", sort_by: str = "updated_at") -> list[JobRead]:
    return await data_store.list_jobs(search=search, department=department, status=status, sort_by=sort_by)


@router.get("/{job_id}", response_model=JobRead)
async def get_job_by_id(job_id: int) -> JobRead:
    job = await data_store.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job


@router.post("", response_model=JobRead)
async def create_job(payload: JobCreate) -> JobRead:
    if payload.openings < 1:
        raise HTTPException(status_code=400, detail="Openings must be at least 1")
    return await data_store.create_job(payload)


@router.put("/{job_id}", response_model=JobRead)
async def update_job(job_id: int, payload: JobCreate) -> JobRead:
    try:
        return await data_store.update_job(job_id, payload)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.delete("/{job_id}")
async def delete_job(job_id: int) -> dict[str, str]:
    try:
        job = await data_store.get_job(job_id)
        if not job:
            raise ValueError("Job not found")
        await data_store.delete_job(job_id)
        return {"message": "deleted"}
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/{job_id}/archive", response_model=JobRead)
async def archive_job(job_id: int) -> JobRead:
    try:
        return await data_store.archive_job(job_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/{job_id}/clone", response_model=JobRead)
async def clone_job(job_id: int) -> JobRead:
    try:
        return await data_store.clone_job(job_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/generate-jd")
async def generate_jd(payload: JobCreate) -> dict[str, object]:
    try:
        return generate_job_description(payload)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

