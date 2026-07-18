from __future__ import annotations

import logging
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
import os
from pydantic import BaseModel
from typing import Any

from backend.database.data_store import data_store
from backend.services.report_aggregation_service import (
    get_pipeline_funnel,
    get_hiring_velocity,
    get_source_quality,
    get_workforce_summary
)
from backend.services.export_service import generate_export, get_export_status

logger = logging.getLogger(__name__)

router = APIRouter()

class CustomExportRequest(BaseModel):
    entity: str  # "jobs", "candidates", "interviews", "employees"
    filters: dict = {}
    fields: list[str] = []
    group_by: str = ""

class ExportRequest(BaseModel):
    report_type: str
    format: str  # "pdf", "xlsx", "csv"
    payload: list[dict] | dict

@router.get("/recruitment-summary")
async def get_recruitment_summary(department: str = "All"):
    # Aggregated funnel report + velocity
    jobs = await data_store.list_jobs(department=department if department != "All" else "", status="All")
    cands = await data_store.list_candidates()
    ivs = await data_store.list_interviews()
    apps = data_store._data.get("applications", []) if data_store._data else []
    
    funnel = get_pipeline_funnel(jobs, apps, ivs, cands, department)
    velocity = get_hiring_velocity(apps, ivs, cands, days=30)
    source_quality = get_source_quality(cands, apps, jobs, department)
    
    return {
        "funnel": funnel,
        "velocity": velocity,
        "source_quality": source_quality
    }

@router.get("/job/{job_id}")
async def get_job_report(job_id: int):
    job = await data_store.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
        
    cands = await data_store.list_candidates(job_id=job_id)
    ivs = await data_store.list_interviews(job_id=job_id)
    
    return {
        "job": job,
        "pipeline": {
            "total_candidates": len(cands),
            "interviews": len(ivs),
            "hired": len([c for c in cands if c.get("status") == "Hired"])
        },
        "candidates": cands
    }

@router.get("/candidate/{candidate_id}")
async def get_candidate_report(candidate_id: int):
    c = await data_store.get_candidate(candidate_id)
    if not c:
        raise HTTPException(status_code=404, detail="Candidate not found")
        
    ivs = await data_store.list_interviews(candidate_id=candidate_id)
    return {
        "profile": c,
        "interviews": ivs
    }

@router.get("/employee/{employee_id}")
async def get_employee_report(employee_id: int):
    # Relies on the already fleshed out employee endpoint or repeats here
    e = await data_store.get_employee(employee_id)
    if not e:
        raise HTTPException(status_code=404, detail="Employee not found")
    return e

@router.post("/custom")
async def generate_custom_report(req: CustomExportRequest):
    data = []
    if req.entity == "jobs":
        data = await data_store.list_jobs()
    elif req.entity == "candidates":
        data = await data_store.list_candidates()
    elif req.entity == "interviews":
        data = await data_store.list_interviews()
    elif req.entity == "employees":
        data = await data_store.list_employees()
    else:
        raise HTTPException(status_code=400, detail="Invalid entity")
        
    # Basic filtering
    if req.filters:
        for k, v in req.filters.items():
            data = [d for d in data if str(d.get(k)) == str(v)]
            
    # Field selection
    if req.fields:
        filtered_data = []
        for d in data:
            filtered_data.append({f: d.get(f) for f in req.fields})
        data = filtered_data
        
    return data

@router.post("/export")
async def trigger_export(req: ExportRequest):
    export_id = await generate_export(req.report_type, req.format, req.payload)
    return {"export_id": export_id, "status": "processing"}

@router.get("/export/{export_id}/status")
async def check_export_status(export_id: str):
    status_info = get_export_status(export_id)
    if status_info["status"] == "not_found":
        raise HTTPException(status_code=404, detail="Export ID not found")
    return {"export_id": export_id, "status": status_info["status"]}

@router.get("/export/{export_id}/download")
async def download_export(export_id: str):
    status_info = get_export_status(export_id)
    if status_info["status"] != "completed" or not status_info.get("file_path"):
        raise HTTPException(status_code=400, detail="Export not ready or failed")
        
    file_path = status_info["file_path"]
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found on disk")
        
    filename = os.path.basename(file_path)
    return FileResponse(path=file_path, filename=filename, media_type="application/octet-stream")
