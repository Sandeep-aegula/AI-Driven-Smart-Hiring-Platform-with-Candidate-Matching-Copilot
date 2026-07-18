from __future__ import annotations

import logging
from fastapi import APIRouter, HTTPException

from backend.database.data_store import data_store
from backend.services.ai_talent_service import generate_talent_insights

logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("")
async def get_employees(
    search: str = "",
    department: str = "All",
    designation: str = "All",
    status: str = "All",
    limit: int = 100,
    offset: int = 0
) -> list[dict]:
    return await data_store.list_employees(
        search=search,
        department=department,
        designation=designation,
        status=status,
        limit=limit,
        offset=offset
    )

@router.get("/{employee_id}")
async def get_employee_details(employee_id: int) -> dict:
    emp = await data_store.get_employee(employee_id)
    if not emp:
        raise HTTPException(status_code=404, detail="Employee not found")
    return emp

@router.put("/{employee_id}")
async def update_employee_details(employee_id: int, payload: dict) -> dict:
    try:
        return await data_store.update_employee(employee_id, payload)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.put("/{employee_id}/skills")
async def update_employee_skills(employee_id: int, payload: list[dict]) -> dict:
    try:
        return await data_store.update_employee_skills(employee_id, payload)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.post("/{employee_id}/projects")
async def add_employee_project(employee_id: int, payload: dict) -> dict:
    try:
        return await data_store.add_employee_project(employee_id, payload)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.put("/{employee_id}/projects/{project_id}")
async def update_employee_project(employee_id: int, project_id: int, payload: dict) -> dict:
    try:
        return await data_store.update_employee_project(employee_id, project_id, payload)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.post("/{employee_id}/performance")
async def add_employee_performance(employee_id: int, payload: dict) -> dict:
    try:
        return await data_store.add_employee_performance(employee_id, payload)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.get("/{employee_id}/performance-summary")
async def get_employee_performance_summary(employee_id: int) -> dict:
    emp = await data_store.get_employee(employee_id)
    if not emp:
        raise HTTPException(status_code=404, detail="Employee not found")
        
    history = emp.get("performance_history", [])
    
    # Calculate aggregated score
    if not history:
        return {"overall_score": 0, "history": []}
        
    total_score = sum(p.get("kpi_score", 0) for p in history)
    avg_score = total_score / len(history)
    
    return {
        "overall_score": round(avg_score, 1),
        "history": sorted(history, key=lambda x: (x.get("year", 0), ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"].index(x.get("month", "Jan")) if x.get("month") in ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"] else 0))
    }

@router.post("/{employee_id}/talent-insights")
async def get_talent_insights(employee_id: int) -> dict:
    emp = await data_store.get_employee(employee_id)
    if not emp:
        raise HTTPException(status_code=404, detail="Employee not found")
        
    # Generate insights via AI
    insights = await generate_talent_insights(emp)
    
    try:
        await data_store.update_talent_insights(employee_id, insights)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
        
    return insights

@router.post("/{employee_id}/notes")
async def add_employee_note(employee_id: int, payload: dict) -> dict:
    emp = await data_store.get_employee(employee_id)
    if not emp:
        raise HTTPException(status_code=404, detail="Employee not found")
        
    notes = emp.setdefault("notes", [])
    notes.append(payload)
    
    try:
        return await data_store.update_employee(employee_id, {"notes": notes})
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.get("/{employee_id}/report")
async def generate_employee_report(employee_id: int) -> dict:
    emp = await data_store.get_employee(employee_id)
    if not emp:
        raise HTTPException(status_code=404, detail="Employee not found")
        
    # Return assembled payload (Module 7 export hook)
    return {
        "employee_id": employee_id,
        "profile": {
            "name": emp.get("name"),
            "department": emp.get("department"),
            "designation": emp.get("designation"),
            "status": emp.get("status"),
            "joining_date": emp.get("joining_date")
        },
        "skills": emp.get("skills", []),
        "projects": emp.get("projects", []),
        "performance_history": emp.get("performance_history", []),
        "talent_insights": emp.get("talent_insights", {})
    }
