from __future__ import annotations

from pathlib import Path
import aiofiles

from fastapi import APIRouter, File, HTTPException, UploadFile

from backend.core.config import settings
from backend.schemas.entities import ResumeParseResponse
from backend.database.data_store import data_store

router = APIRouter()


@router.post("/parse", response_model=ResumeParseResponse)
async def parse_resume(file: UploadFile = File(...)) -> ResumeParseResponse:
    try:
        contents = await file.read()
        file_path = Path(settings.uploads_dir) / file.filename
        file_path.parent.mkdir(parents=True, exist_ok=True)
        async with aiofiles.open(file_path, "wb") as f:
            await f.write(contents)
            
        result = await data_store.parse_resume_file(str(file_path))
        return result.parsed
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

