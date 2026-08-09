"""
AI Interview module — isolated repository for ai_interview_sessions.

Deliberately separate from backend/database/data_store.py so the AI
Interview module's data access never touches the existing data_store class.
The only place this module writes to an EXISTING table (interviews.status)
is via data_store.update_interview(), called from the router -- never here.
"""
from __future__ import annotations

from sqlalchemy import select

from backend.database.session import get_db_session
from backend.models.ai_interview_entities import AIInterviewSession


def _to_dict(session_row: AIInterviewSession) -> dict:
    return {
        "id": session_row.id,
        "interview_id": session_row.interview_id,
        "status": session_row.status,
        "questions": session_row.questions,
        "current_index": session_row.current_index,
        "target_question_count": session_row.target_question_count,
        "result": session_row.result,
        "final_evaluation": session_row.final_evaluation,
    }


async def get_active_session_for_interview(interview_id: int) -> dict | None:
    async with get_db_session() as db:
        stmt = (
            select(AIInterviewSession)
            .where(AIInterviewSession.interview_id == interview_id)
            .order_by(AIInterviewSession.id.desc())
        )
        res = await db.execute(stmt)
        row = res.scalars().first()
        return _to_dict(row) if row else None


async def get_session(session_id: int) -> dict | None:
    async with get_db_session() as db:
        row = await db.get(AIInterviewSession, session_id)
        return _to_dict(row) if row else None


async def delete_session(session_id: int) -> None:
    async with get_db_session() as db:
        row = await db.get(AIInterviewSession, session_id)
        if row:
            await db.delete(row)


async def create_session(interview_id: int, first_question: str, target_question_count: int = 8) -> dict:
    async with get_db_session() as db:
        row = AIInterviewSession(
            interview_id=interview_id,
            status="in_progress",
            questions=[{"question": first_question, "answer_transcript": None, "evaluation": None}],
            current_index=0,
            target_question_count=target_question_count,
            result="",
        )
        db.add(row)
        await db.flush()
        await db.refresh(row)
        return _to_dict(row)


async def record_answer_and_advance(session_id: int, answer_transcript: str, evaluation: dict, next_question: str | None) -> dict:
    """Store the transcript+evaluation for the current question, and either
    append the next question (advancing current_index) or leave it as-is if
    the caller is about to mark the session completed instead."""
    async with get_db_session() as db:
        row = await db.get(AIInterviewSession, session_id)
        if not row:
            raise ValueError("AI interview session not found")

        questions = list(row.questions)
        idx = row.current_index
        questions[idx] = {
            **questions[idx],
            "answer_transcript": answer_transcript,
            "evaluation": evaluation,
        }

        if next_question:
            questions.append({"question": next_question, "answer_transcript": None, "evaluation": None})
            row.current_index = idx + 1

        row.questions = questions
        await db.flush()
        await db.refresh(row)
        return _to_dict(row)


async def complete_session(session_id: int, result: str, final_evaluation: dict) -> dict:
    async with get_db_session() as db:
        row = await db.get(AIInterviewSession, session_id)
        if not row:
            raise ValueError("AI interview session not found")
        row.status = "completed"
        row.result = result
        row.final_evaluation = final_evaluation
        await db.flush()
        await db.refresh(row)
        return _to_dict(row)
