from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, File, HTTPException, UploadFile
from pydantic import BaseModel, Field

from backend.core.config import settings
from backend.database.session import session_scope
from backend.schemas.entities import ResumeUploadResponse
from backend.services.recruitment import list_recent_uploads, parse_resume_file, parse_resume_text

router = APIRouter()


class ResumeTextRequest(BaseModel):
    text: str = Field(min_length=1)
    filename: str = "pasted_resume.txt"


@router.get("/history")
def get_upload_history(limit: int = 10) -> list[dict[str, object]]:
    with session_scope() as session:
        return list_recent_uploads(session, limit=limit)


@router.post("/upload", response_model=ResumeUploadResponse)
async def upload_resume(file: UploadFile = File(...)) -> ResumeUploadResponse:
    try:
        contents = await file.read()
        file_path = Path(settings.uploads_dir) / file.filename
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_bytes(contents)
        with session_scope() as session:
            result = parse_resume_file(session, str(file_path))
            return ResumeUploadResponse(
                id=result.resume_id,
                candidate_id=result.candidate_id,
                filename=result.filename,
                status="Parsed",
                parsed_json=result.parsed.model_dump(),
            )
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/parse-text", response_model=ResumeUploadResponse)
def parse_text_resume(payload: ResumeTextRequest) -> ResumeUploadResponse:
    try:
        with session_scope() as session:
            result = parse_resume_text(session, payload.text, payload.filename)
            return ResumeUploadResponse(
                id=result.resume_id,
                candidate_id=result.candidate_id,
                filename=result.filename,
                status="Parsed",
                parsed_json=result.parsed.model_dump(),
            )
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

