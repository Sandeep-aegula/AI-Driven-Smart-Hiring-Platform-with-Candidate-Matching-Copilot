from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, File, HTTPException, UploadFile

from backend.core.config import settings
from backend.database.session import session_scope
from backend.schemas.entities import ResumeParseResponse
from backend.services.recruitment import parse_resume_file

router = APIRouter()


@router.post("/parse", response_model=ResumeParseResponse)
async def parse_resume(file: UploadFile = File(...)) -> ResumeParseResponse:
    try:
        contents = await file.read()
        file_path = Path(settings.uploads_dir) / file.filename
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_bytes(contents)
        with session_scope() as session:
            result = parse_resume_file(session, str(file_path))
            return result.parsed
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
