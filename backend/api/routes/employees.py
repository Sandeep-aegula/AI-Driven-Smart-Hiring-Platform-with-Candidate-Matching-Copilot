from __future__ import annotations

from fastapi import APIRouter, HTTPException

from backend.database.session import session_scope
from backend.services.recruitment import (
    list_employees,
    get_employee
)

router = APIRouter()

@router.get("")
def get_employees() -> list[dict]:
    with session_scope() as session:
        return list_employees(session)

@router.get("/{employee_id}")
def get_employee_details(employee_id: int) -> dict:
    with session_scope() as session:
        emp = get_employee(session, employee_id)
        if not emp:
            raise HTTPException(status_code=404, detail="Employee not found")
        return emp
