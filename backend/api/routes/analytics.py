from __future__ import annotations

import logging
import asyncio
from fastapi import APIRouter

from backend.database.data_store import data_store
from backend.services.report_aggregation_service import (
    get_overview_kpis,
    get_pipeline_funnel,
    get_hiring_velocity,
    get_source_quality,
    get_interview_load,
    get_workforce_summary
)

logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("/overview")
async def get_overview():
    jobs = await data_store.list_jobs()
    cands = await data_store.list_candidates()
    ivs = await data_store.list_interviews()
    return get_overview_kpis(jobs, cands, ivs)

@router.get("/pipeline-funnel")
async def get_funnel(department: str = "All"):
    jobs = await data_store.list_jobs(department=department if department != "All" else "All")
    cands = await data_store.list_candidates()
    ivs = await data_store.list_interviews()
    apps = await data_store.list_applications()
    return get_pipeline_funnel(jobs, apps, ivs, cands, department)

@router.get("/hiring-velocity")
async def get_velocity(days: int = 30):
    cands = await data_store.list_candidates()
    ivs = await data_store.list_interviews()
    apps = await data_store.list_applications()
    return get_hiring_velocity(apps, ivs, cands, days)

@router.get("/source-quality")
async def get_quality(department: str = "All"):
    jobs = await data_store.list_jobs(department=department if department != "All" else "")
    cands = await data_store.list_candidates()
    apps = await data_store.list_applications()
    return get_source_quality(cands, apps, jobs, department)

@router.get("/interview-load")
async def get_load(days: int = 14):
    ivs = await data_store.list_interviews()
    return get_interview_load(ivs, days)

@router.get("/workforce-summary")
async def get_workforce():
    emps = await data_store.list_employees()
    return get_workforce_summary(emps)

@router.get("/dashboard-bundle")
async def get_dashboard_bundle(department: str = "All", days: int = 30):
    """
    Returns all dashboard metrics in one shot via concurrent aggregation.
    """
    jobs = await data_store.list_jobs(department=department if department != "All" else "All")
    cands = await data_store.list_candidates()
    ivs = await data_store.list_interviews()
    emps = await data_store.list_employees()
    apps = await data_store.list_applications()
    
    # In a real heavy app we might offload these to a thread pool executor.
    # Here they run sequentially since pandas over memory dicts is fast enough.
    overview = get_overview_kpis(jobs, cands, ivs)
    funnel = get_pipeline_funnel(jobs, apps, ivs, cands, department)
    velocity = get_hiring_velocity(apps, ivs, cands, days)
    quality = get_source_quality(cands, apps, jobs, department)
    load = get_interview_load(ivs, days)
    workforce = get_workforce_summary(emps)
    
    return {
        "overview": overview,
        "funnel": funnel,
        "velocity": velocity,
        "source_quality": quality,
        "interview_load": load,
        "workforce": workforce
    }

@router.get("/refresh")
async def refresh_analytics():
    # In-memory cache is mostly managed by frontend caching and data_store reads,
    # but we provide this to clear the cache if we implement a backend cache later.
    return {"status": "Cache refreshed"}
