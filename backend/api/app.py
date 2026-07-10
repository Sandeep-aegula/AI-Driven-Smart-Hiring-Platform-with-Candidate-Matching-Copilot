from __future__ import annotations

from fastapi import FastAPI

from backend.api.routes.ai_screening import router as screening_router
from backend.api.routes.candidates import router as candidates_router
from backend.api.routes.jobs import router as jobs_router
from backend.api.routes.parser import router as parser_router
from backend.api.routes.resume import router as resume_router
from backend.api.routes.interviews import router as interviews_router
from backend.api.routes.employees import router as employees_router
from backend.core.config import settings
from backend.services.recruitment import initialize_database


def create_app() -> FastAPI:
    # Auto-initialize and seed database on startup
    initialize_database()
    
    app = FastAPI(title=settings.app_name)
    app.include_router(jobs_router, prefix="/jobs", tags=["jobs"])
    app.include_router(candidates_router, prefix="/candidates", tags=["candidates"])
    app.include_router(resume_router, prefix="/resume", tags=["resume"])
    app.include_router(parser_router, prefix="/parser", tags=["parser"])
    app.include_router(screening_router, prefix="/ai-screening", tags=["ai-screening"])
    app.include_router(interviews_router, prefix="/interviews", tags=["interviews"])
    app.include_router(employees_router, prefix="/employees", tags=["employees"])
    return app


app = create_app()
