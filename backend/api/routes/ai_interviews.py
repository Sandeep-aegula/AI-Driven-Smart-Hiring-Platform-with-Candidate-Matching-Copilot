"""
AI Interview module — isolated API router.

Mounted at /api/ai-interviews (backend/api/app.py). This is the ONLY new
backend surface for the AI Interview feature.

Reads: candidate / job / resume / existing interview data via the existing
data_store getters (read-only, no changes to those methods).

Writes:
  - New rows in the isolated `ai_interview_sessions` table (this module's
    own data), via backend/database/ai_interview_repository.py.
  - Exactly one write to an existing table: on interview completion, the
    existing interview's `status` column is set to "PASS" or "FAIL" via the
    existing data_store.update_interview() method. Nothing else about the
    existing interview record is touched.

Two ways to submit an answer:
  - POST /sessions/{id}/answer-text  (JSON {"transcript": "..."}) -- the
    PRIMARY path used by the live interview screen, where the candidate's
    speech is already transcribed live in the browser (Web Speech API).
  - POST /sessions/{id}/answer  (multipart audio upload) -- kept as a
    fallback/retry path for browsers without live speech recognition
    support; transcribes server-side via the isolated STT service.
Both funnel through the same _process_answer() so evaluation/next-question/
completion logic is not duplicated.
"""
from __future__ import annotations

import logging

from fastapi import APIRouter, File, HTTPException, UploadFile
from pydantic import BaseModel

from backend.database import ai_interview_repository as repo
from backend.database.data_store import data_store
from backend.services import ai_interview_session_service as session_service
from backend.services.ai_interview_stt_service import transcribe_answer

logger = logging.getLogger(__name__)
router = APIRouter()


class AnswerTextRequest(BaseModel):
    transcript: str


async def _job_via_application(application_id: int) -> dict | None:
    """Read-only fallback: resolve a job through the existing application
    record rather than the interview's own (possibly missing/out-of-sync)
    job_id. Uses the existing Application model directly (read-only query)
    rather than adding a new data_store method."""
    from backend.database.session import get_db_session
    from backend.models.entities import Application

    async with get_db_session() as db:
        app_row = await db.get(Application, application_id)
    if app_row and app_row.job_id:
        return await data_store.get_job(app_row.job_id)
    return None


async def _load_context(interview_id: int) -> dict:
    """Read-only fetch of the existing interview + its candidate/job/resume.
    Restricted to interviews scheduled with Round = "AI Interview"."""
    iv = await data_store.get_interview(interview_id)
    if not iv:
        raise HTTPException(status_code=404, detail="Interview not found")
    if iv.get("round") != "AI Interview":
        raise HTTPException(status_code=400, detail="This interview is not scheduled as an AI Interview")

    candidate = await data_store.get_candidate(iv.get("candidate_id"))
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found")

    job = await data_store.get_job(iv.get("job_id")) if iv.get("job_id") else None
    if not job and iv.get("application_id"):
        # Every AI Interview is scheduled against a real application (a
        # required field on the existing interview record), and every
        # application is required to reference a job. Fall back to it so a
        # missing/out-of-sync interview.job_id can never silently drop the
        # job description used for question generation or displayed as
        # "Unknown".
        job = await _job_via_application(iv["application_id"])
    resume = await data_store.get_latest_candidate_resume(iv.get("candidate_id"))

    required_skills = []
    if job:
        required_skills = list(job.get("requirements", []) or [])
        required_skills += [s.get("name") if isinstance(s, dict) else s for s in job.get("skills", []) or []]

    return {"interview": iv, "candidate": candidate, "job": job, "resume": resume, "required_skills": required_skills}


@router.get("/{interview_id}/context")
async def get_interview_context(interview_id: int):
    """Read-only: candidate, job, resume, required skills for an existing
    AI Interview round. Does not modify Candidates/Jobs/Resume data."""
    ctx = await _load_context(interview_id)
    return {
        "interview": ctx["interview"],
        "candidate": ctx["candidate"],
        "job": ctx["job"],
        "resume": ctx["resume"],
        "required_skills": ctx["required_skills"],
    }


@router.post("/{interview_id}/session")
async def start_or_resume_session(interview_id: int, fresh: bool = False):
    """Create or resume an AI interview session (generating the first
    question if none exists yet).

    Two distinct callers share this endpoint with different intent:
      - The candidate explicitly starting an interview (Instructions screen
        -> "Start Interview") passes fresh=True: any existing *in-progress*
        session is discarded and replaced with a brand new one, so every
        deliberate "start" begins fresh rather than silently resuming
        half-finished progress from a previous abandoned attempt.
      - The live interview screen recovering from a lost browser session
        (e.g. an accidental page refresh mid-interview) calls this with the
        default fresh=False: it must resume the existing in-progress
        session unchanged, not wipe the candidate's progress just because
        the tab reloaded.

    A completed session is always returned as-is either way (nothing to
    restart -- and the "Start AI Interview" button that leads here is
    already hidden once the interview record shows PASS/FAIL, so this is
    mostly a defensive guard)."""
    existing = await repo.get_active_session_for_interview(interview_id)
    if existing:
        if existing["status"] == "completed" or not fresh:
            return existing
        await repo.delete_session(existing["id"])

    ctx = await _load_context(interview_id)
    try:
        first_question = await session_service.generate_question(ctx["job"] or {}, ctx["candidate"], ctx["resume"], [])
    except Exception:
        raise HTTPException(status_code=502, detail="Unable to generate the next question.")

    return await repo.create_session(interview_id, first_question)


@router.get("/sessions/{session_id}")
async def get_session(session_id: int):
    session = await repo.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="AI interview session not found")
    return session


async def _process_answer(session_id: int, transcript: str) -> dict:
    """Shared logic: evaluate the current answer, then either return the
    next question or -- on the final question -- complete the session and
    write PASS/FAIL back to the existing interview record (the only allowed
    write outside this module)."""
    session = await repo.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="AI interview session not found")
    if session["status"] != "in_progress":
        raise HTTPException(status_code=400, detail="This AI interview has already been completed.")

    if not transcript.strip():
        raise HTTPException(status_code=422, detail="No voice response detected. Please try again.")

    ctx = await _load_context(session["interview_id"])
    current_index = session["current_index"]
    current_question = session["questions"][current_index]["question"]
    qa_before = session["questions"][:current_index]

    is_final = (current_index + 1) >= session["target_question_count"]

    if is_final:
        # Only the current answer needs evaluating -- there's no next
        # question to generate, so this stays a single call as before.
        evaluation = await session_service.evaluate_answer(ctx["job"] or {}, ctx["candidate"], ctx["resume"], current_question, transcript)
        qa_so_far = qa_before + [
            {"question": current_question, "answer_transcript": transcript, "evaluation": evaluation}
        ]

        await repo.record_answer_and_advance(session_id, transcript, evaluation, next_question=None)
        decision = await session_service.final_decision(ctx["job"] or {}, ctx["candidate"], qa_so_far)
        result = decision.get("result", "FAIL")

        await repo.complete_session(session_id, result, decision)

        # The ONLY write to an existing table made by this module: set the
        # existing interview's existing `status` field to PASS/FAIL.
        await data_store.update_interview(session["interview_id"], {"status": result})

        return {
            "transcript": transcript,
            "completed": True,
            "result": result,
            "question_number": current_index + 1,
            "total_questions": session["target_question_count"],
        }

    # Evaluate the answer AND generate the (difficulty-adapted) next question
    # in one combined LLM call -- roughly half the wait of doing these as two
    # sequential calls, and the wait no longer grows every question since
    # only the last few exchanges are fed back into the prompt.
    try:
        outcome = await session_service.evaluate_and_generate_next(
            ctx["job"] or {}, ctx["candidate"], ctx["resume"], current_question, transcript, qa_before
        )
    except Exception:
        raise HTTPException(status_code=502, detail="Unable to generate the next question.")

    evaluation = outcome["evaluation"]
    next_question = outcome["next_question"]

    updated = await repo.record_answer_and_advance(session_id, transcript, evaluation, next_question=next_question)

    return {
        "transcript": transcript,
        "completed": False,
        "next_question": next_question,
        "question_number": updated["current_index"] + 1,
        "total_questions": session["target_question_count"],
    }


@router.post("/sessions/{session_id}/answer-text")
async def submit_answer_text(session_id: int, payload: AnswerTextRequest):
    """Primary answer path for the live interview screen: the candidate's
    speech has already been transcribed live in the browser (Web Speech
    API); this just evaluates it and advances the session."""
    return await _process_answer(session_id, payload.transcript)


@router.post("/sessions/{session_id}/answer")
async def submit_answer_audio(session_id: int, audio: UploadFile = File(...)):
    """Fallback answer path (recorded audio, server-side transcription) for
    browsers without live speech recognition support."""
    audio_bytes = await audio.read()
    if not audio_bytes:
        raise HTTPException(status_code=422, detail="No voice response detected. Please try again.")

    try:
        transcript = await transcribe_answer(audio_bytes)
    except Exception:
        raise HTTPException(status_code=502, detail="We couldn't process your response. Please try again.")

    return await _process_answer(session_id, transcript)
