"""
AI Interview module — isolated data model.

This is the ONLY new table added for the AI Interview feature. It references
the existing `interviews` table by id (interview_id) rather than duplicating
any candidate/job/interview data. No existing table is altered here.

The only write this module makes to an existing table is the final PASS/FAIL
result, applied to the existing `interviews.status` column via the existing
data_store.update_interview() method -- see
backend/services/ai_interview_session_service.py.
"""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, JSON, String, func
from sqlalchemy.orm import Mapped, mapped_column

from backend.database.base import Base


class AIInterviewSession(Base):
    __tablename__ = "ai_interview_sessions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    # Reference to the existing interview record. Not a duplicate -- the
    # candidate/job/round/date/time/status all continue to live only on the
    # existing `interviews` row.
    interview_id: Mapped[int] = mapped_column(
        ForeignKey("interviews.id", ondelete="CASCADE"), nullable=False, index=True
    )

    # in_progress | completed
    status: Mapped[str] = mapped_column(String(30), default="in_progress")

    # [{"question": str, "answer_transcript": str | None,
    #   "evaluation": {...} | None}, ...] -- AI-generated questions,
    # candidate transcripts, and internal (not candidate-facing) evaluations.
    questions: Mapped[list[dict]] = mapped_column(JSON, default=list)

    current_index: Mapped[int] = mapped_column(Integer, default=0)
    target_question_count: Mapped[int] = mapped_column(Integer, default=5)

    # "" while in progress, then "PASS" or "FAIL" once completed. Mirrors
    # (but is independent of) the value written back to interviews.status.
    result: Mapped[str] = mapped_column(String(20), default="")
    final_evaluation: Mapped[dict] = mapped_column(JSON, default=dict)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
