from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, File, HTTPException, UploadFile

from backend.core.config import settings
from backend.database.session import session_scope
from backend.schemas.entities import ResumeUploadResponse
from backend.services.recruitment import list_recent_uploads, parse_resume_file

router = APIRouter()


@router.get("/history")
def get_upload_history(limit: int = 10) -> list[dict[str, object]]:
    with session_scope() as session:
        uploads = list_recent_uploads(session, limit=limit)
        return [
            {"id": upload.get("id"), "candidate_id": upload.get("candidate_id"), "filename": upload.get("filename"), "status": upload.get("status"), "created_at": upload.get("created_at")}
            for upload in uploads
        ]


@router.post("/upload", response_model=ResumeUploadResponse)
async def upload_resume(file: UploadFile = File(...)) -> ResumeUploadResponse:
    try:
        contents = await file.read()
        file_path = Path(settings.uploads_dir) / file.filename
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_bytes(contents)
        with session_scope() as session:
            result = parse_resume_file(session, str(file_path))
            return ResumeUploadResponse(id=0, candidate_id=0, filename=result.filename, status="Parsed", parsed_json=result.parsed.model_dump())
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
