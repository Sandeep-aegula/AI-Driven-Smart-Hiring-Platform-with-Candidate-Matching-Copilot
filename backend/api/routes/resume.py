from __future__ import annotations

from pathlib import Path
import aiofiles

from fastapi import APIRouter, File, HTTPException, UploadFile
from pydantic import BaseModel, Field

from backend.core.config import settings
from backend.schemas.entities import ResumeUploadResponse
from backend.database.data_store import data_store

router = APIRouter()


class ResumeTextRequest(BaseModel):
    text: str = Field(min_length=1)
    filename: str = "pasted_resume.txt"


@router.get("/history")
async def get_upload_history(limit: int = 10) -> list[dict[str, object]]:
    return await data_store.list_recent_uploads(limit=limit)


@router.post("/upload", response_model=ResumeUploadResponse)
async def upload_resume(file: UploadFile = File(...)) -> ResumeUploadResponse:
    try:
        contents = await file.read()
        file_path = Path(settings.uploads_dir) / file.filename
        file_path.parent.mkdir(parents=True, exist_ok=True)
        async with aiofiles.open(file_path, "wb") as f:
            await f.write(contents)
            
        result = await data_store.parse_resume_file(str(file_path))
        return ResumeUploadResponse(
            id=result.resume_id,
            candidate_id=result.candidate_id,
            filename=result.filename,
            status="Parsed",
            parsed_json=result.parsed.model_dump() if hasattr(result.parsed, "model_dump") else result.parsed,
        )
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/parse-text", response_model=ResumeUploadResponse)
async def parse_text_resume(payload: ResumeTextRequest) -> ResumeUploadResponse:
    try:
        result = await data_store.parse_resume_text(payload.text, payload.filename)
        return ResumeUploadResponse(
            id=result.resume_id,
            candidate_id=result.candidate_id,
            filename=result.filename,
            status="Parsed",
            parsed_json=result.parsed.model_dump() if hasattr(result.parsed, "model_dump") else result.parsed,
        )
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


