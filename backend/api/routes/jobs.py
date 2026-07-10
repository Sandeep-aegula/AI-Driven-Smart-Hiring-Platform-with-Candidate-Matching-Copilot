from __future__ import annotations

from fastapi import APIRouter, HTTPException

from backend.database.session import session_scope
from backend.schemas.entities import JobCreate, JobRead
from backend.services.recruitment import archive_job_record, clone_job_record, create_job_record, delete_job_record, generate_job_description, get_job, list_jobs, update_job_record

router = APIRouter()


@router.get("", response_model=list[JobRead])
def get_jobs(search: str = "", department: str = "All", status: str = "All", sort_by: str = "updated_at") -> list[JobRead]:
    with session_scope() as session:
        return list_jobs(session, search=search, department=department, status=status, sort_by=sort_by)


@router.get("/{job_id}", response_model=JobRead)
def get_job_by_id(job_id: int) -> JobRead:
    with session_scope() as session:
        job = get_job(session, job_id)
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        return job


@router.post("", response_model=JobRead)
def create_job(payload: JobCreate) -> JobRead:
    with session_scope() as session:
        return create_job_record(session, payload)


@router.put("/{job_id}", response_model=JobRead)
def update_job(job_id: int, payload: JobCreate) -> JobRead:
    with session_scope() as session:
        try:
            return update_job_record(session, job_id, payload)
        except ValueError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.delete("/{job_id}")
def delete_job(job_id: int) -> dict[str, str]:
    with session_scope() as session:
        try:
            delete_job_record(session, job_id)
            return {"message": "deleted"}
        except ValueError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/{job_id}/archive", response_model=JobRead)
def archive_job(job_id: int) -> JobRead:
    with session_scope() as session:
        try:
            return archive_job_record(session, job_id)
        except ValueError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/{job_id}/clone", response_model=JobRead)
def clone_job(job_id: int) -> JobRead:
    with session_scope() as session:
        try:
            return clone_job_record(session, job_id)
        except ValueError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/generate-jd")
def generate_jd(payload: JobCreate) -> dict[str, object]:
    try:
        return generate_job_description(payload)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
