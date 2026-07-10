from __future__ import annotations

from fastapi import APIRouter, HTTPException

from backend.database.session import session_scope
from backend.schemas.entities import ApplicationCreate, CandidateCreate, CandidateRead
from backend.services.recruitment import add_candidate_note, create_application_record, create_candidate_record, get_candidate, list_candidates, update_candidate_record, update_candidate_status

router = APIRouter()


@router.get("", response_model=list[CandidateRead])
def get_candidates(search: str = "", status: str = "All", skill: str = "All") -> list[CandidateRead]:
    with session_scope() as session:
        return list_candidates(session, search=search, status=status, skill=skill)


@router.get("/{candidate_id}", response_model=CandidateRead)
def get_candidate_by_id(candidate_id: int) -> CandidateRead:
    with session_scope() as session:
        candidate = get_candidate(session, candidate_id)
        if not candidate:
            raise HTTPException(status_code=404, detail="Candidate not found")
        return candidate


@router.post("", response_model=CandidateRead)
def create_candidate(payload: CandidateCreate) -> CandidateRead:
    with session_scope() as session:
        return create_candidate_record(session, payload)


@router.put("/{candidate_id}", response_model=CandidateRead)
def update_candidate(candidate_id: int, payload: CandidateCreate) -> CandidateRead:
    with session_scope() as session:
        try:
            return update_candidate_record(session, candidate_id, payload)
        except ValueError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/{candidate_id}/notes", response_model=CandidateRead)
def note_candidate(candidate_id: int, note: str) -> CandidateRead:
    with session_scope() as session:
        try:
            return add_candidate_note(session, candidate_id, note)
        except ValueError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/{candidate_id}/status", response_model=CandidateRead)
def status_candidate(candidate_id: int, status: str) -> CandidateRead:
    with session_scope() as session:
        try:
            return update_candidate_status(session, candidate_id, status)
        except ValueError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/{candidate_id}/applications", response_model=dict[str, int | str])
def application_candidate(candidate_id: int, payload: ApplicationCreate) -> dict[str, int | str]:
    with session_scope() as session:
        try:
            application = create_application_record(session, payload.model_copy(update={"candidate_id": candidate_id}))
            return {"id": application.id, "status": application.status}
        except Exception as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
