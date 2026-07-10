from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from backend.database.session import session_scope
from backend.services.recruitment import (
    list_interviews,
    create_interview_record,
    update_interview_status,
    add_interview_feedback,
    generate_interview_questions
)

router = APIRouter()

class InterviewCreate(BaseModel):
    candidate_id: int
    interviewer: str = "Ava Morgan"
    date: str
    time: str
    stage: str
    meeting_link: str = "https://meet.google.com/abc-defg-hij"

class InterviewFeedback(BaseModel):
    feedback_notes: str
    recommendation: str

class QuestionsRequest(BaseModel):
    stage: str
    skills: list[str]

@router.get("")
def get_interviews() -> list[dict]:
    with session_scope() as session:
        return list_interviews(session)

@router.post("")
def schedule_interview(payload: InterviewCreate) -> dict:
    with session_scope() as session:
        try:
            return create_interview_record(session, payload.model_dump())
        except Exception as exc:
            raise HTTPException(status_code=400, detail=str(exc))

@router.put("/{interview_id}/status")
def change_interview_status(interview_id: int, status: str) -> dict:
    with session_scope() as session:
        try:
            return update_interview_status(session, interview_id, status)
        except Exception as exc:
            raise HTTPException(status_code=400, detail=str(exc))

@router.post("/{interview_id}/feedback")
def log_interview_feedback(interview_id: int, payload: InterviewFeedback) -> dict:
    with session_scope() as session:
        try:
            return add_interview_feedback(session, interview_id, payload.feedback_notes, payload.recommendation)
        except Exception as exc:
            raise HTTPException(status_code=400, detail=str(exc))

@router.post("/generate-questions")
def make_questions(payload: QuestionsRequest) -> list[str]:
    try:
        return generate_interview_questions(payload.stage, payload.skills)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))
