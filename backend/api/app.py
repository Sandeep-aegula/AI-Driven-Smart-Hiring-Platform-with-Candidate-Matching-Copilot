from __future__ import annotations
from __future__ import annotations

import time
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.middleware.cors import CORSMiddleware

from backend.api.routes.ai_screening import router as screening_router
from backend.api.routes.auth import router as auth_router
from backend.api.routes.candidates import router as candidates_router
from backend.api.routes.communications import router as communications_router
from backend.api.routes.jobs import router as jobs_router
from backend.api.routes.resumes import router as resumes_router
from backend.api.routes.interviews import router as interviews_router
from backend.api.routes.employees import router as employees_router
from backend.api.routes.reports import router as reports_router
from backend.api.routes.analytics import router as analytics_router
from backend.api.routes.copilot import router as copilot_router
from backend.api.routes.applications import router as applications_router
from backend.api.routes.public import router as public_router
from backend.api.routes.onboarding import router as onboarding_router
from backend.core.config import settings
from backend.database.data_store import data_store
from backend.database.init_db import initialize_database

logger = logging.getLogger("backend.api")

@asynccontextmanager
async def lifespan(app: FastAPI):
    smtp_issues = settings.validate_smtp_configuration()
    if smtp_issues:
        logger.warning("SMTP configuration validation issues: %s", "; ".join(smtp_issues))
    else:
        logger.info("SMTP configuration validation passed.")
    await initialize_database()
    await data_store.initialize()
    yield

def create_app() -> FastAPI:
    app = FastAPI(title=settings.app_name, lifespan=lifespan)
    
    # Enable CORS for frontend requests (Streamlit default port is 8501)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # GZip compression for API responses
    app.add_middleware(GZipMiddleware, minimum_size=1000)
    
    # Basic response time logging middleware
    @app.middleware("http")
    async def log_response_time(request: Request, call_next):
        start_time = time.perf_counter()
        response = await call_next(request)
        duration = time.perf_counter() - start_time
        logger.info(f"API request: {request.method} {request.url.path} took {duration:.4f}s")
        response.headers["X-Response-Time"] = f"{duration:.4f}s"
        return response

    app.include_router(jobs_router, prefix="/jobs", tags=["jobs"])
    app.include_router(candidates_router, prefix="/candidates", tags=["candidates"])
    app.include_router(communications_router, prefix="/communications", tags=["communications"])
    app.include_router(resumes_router, prefix="/resumes", tags=["resumes"])
    app.include_router(screening_router, prefix="/ai-screening", tags=["ai-screening"])
    app.include_router(interviews_router, prefix="/interviews", tags=["interviews"])
    app.include_router(employees_router, prefix="/employees", tags=["employees"])
    app.include_router(onboarding_router, prefix="/onboarding", tags=["onboarding"])
    app.include_router(reports_router, prefix="/reports", tags=["reports"])
    app.include_router(analytics_router, prefix="/analytics", tags=["analytics"])
    app.include_router(copilot_router, prefix="/copilot", tags=["copilot"])
    app.include_router(public_router, prefix="/public", tags=["public"])
    app.include_router(applications_router, prefix="/applications", tags=["applications"])
    app.include_router(auth_router, prefix="/auth", tags=["auth"])
    
    from backend.api.routes.assistant import router as assistant_router
    app.include_router(assistant_router, prefix="/api/assistant", tags=["assistant"])

    @app.get("/health")
    async def health() -> dict[str, str]:
        return {"status": "ok", "database": "mysql"}

    return app


app = create_app()
