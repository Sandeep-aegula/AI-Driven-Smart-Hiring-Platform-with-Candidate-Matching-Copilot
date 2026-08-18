"""
AI Interview module — isolated question generation, answer evaluation, and
final PASS/FAIL decision.

Reuses the existing configured Ollama backend (backend.core.config.settings)
rather than standing up a second AI architecture. Calls are made with an
async httpx client (the same safe pattern already used by
backend/services/ai_resume_service.py and ollama_service.py) so a slow LLM
call never blocks the FastAPI event loop for other requests.

This module does not read or write Candidate/Job/Resume/Interview rows
itself -- it only receives already-fetched dicts and returns text/JSON. All
existing-record I/O stays in backend/api/routes/ai_interviews.py, using the
existing data_store getters.
"""
from __future__ import annotations

import json
import logging
from difflib import SequenceMatcher

import httpx

from backend.core.config import settings

logger = logging.getLogger(__name__)

OLLAMA_GENERATE_URL = f"{settings.ollama_base_url.rstrip('/')}/api/generate"
TIMEOUT_SECONDS = 120.0


async def _ollama_generate(prompt: str, system: str, retries: int = 1) -> str:
    payload = {
        "model": settings.ollama_model,
        "prompt": prompt,
        "system": system,
        "stream": False,
        "format": "json",
        # num_predict bounds worst-case generation length (a runaway response
        # is a big chunk of the "some questions take way longer" variance on
        # local CPU inference). keep_alive keeps the model resident between
        # the ~8 sequential calls of one interview so a candidate who takes a
        # while to answer doesn't trigger a cold reload mid-interview.
        "options": {"temperature": 0.3, "num_predict": 350},
        "keep_alive": "10m",
    }
    last_error: Exception | None = None
    for attempt in range(retries + 1):
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(OLLAMA_GENERATE_URL, json=payload, timeout=TIMEOUT_SECONDS)
                response.raise_for_status()
                return response.json().get("response", "")
        except Exception as exc:
            last_error = exc
            logger.warning("AI Interview: Ollama call failed (attempt %s/%s): %s", attempt + 1, retries + 1, exc)
    raise RuntimeError(f"AI Interview: Ollama request failed after retries: {last_error}")


def _parse_json(text: str) -> dict:
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        start, end = text.find("{"), text.rfind("}")
        if start >= 0 and end > start:
            return json.loads(text[start:end + 1])
        raise


def _job_context(job: dict) -> str:
    return (
        f"Title: {job.get('title', '')}\n"
        f"Department: {job.get('department', '')}\n"
        f"Description: {job.get('description', '')}\n"
        f"Requirements: {', '.join(job.get('requirements') or [])}\n"
        f"Required Skills: {', '.join([s.get('name') if isinstance(s, dict) else s for s in job.get('skills', [])])}\n"
    )


def _candidate_context(candidate: dict, resume: dict | None) -> str:
    resume_text = ""
    if resume:
        resume_text = resume.get("extracted_text", "") or ""
        if not resume_text:
            resume_text = (
                f"Skills: {', '.join(resume.get('skills') or [])}\n"
                f"Experience: {', '.join(resume.get('experience') or [])}\n"
                f"Projects: {', '.join(resume.get('projects') or [])}\n"
            )
    if not resume_text:
        resume_text = f"Summary: {candidate.get('summary', '')}\nSkills: {', '.join([s.get('name') if isinstance(s, dict) else s for s in candidate.get('skills', [])])}"
    return resume_text[:4000]


def _avg_score(evaluation: dict | None) -> float | None:
    if not evaluation:
        return None
    scores = [
        evaluation.get(k) for k in
        ("relevance", "correctness", "job_relevance", "skill_demonstration", "completeness")
    ]
    scores = [s for s in scores if isinstance(s, (int, float))]
    return sum(scores) / len(scores) if scores else None


def _running_average(qa_history: list[dict]) -> float | None:
    """Average score across every answered question so far -- used to steer
    the next question's difficulty (see _difficulty_guidance)."""
    scores = [s for s in (_avg_score(qa.get("evaluation")) for qa in qa_history) if s is not None]
    return sum(scores) / len(scores) if scores else None


def _difficulty_guidance(running_avg: float | None) -> str:
    """Adaptive hardness: the next question gets harder after strong
    answers, easier after weak ones, and stays moderate for a first/average
    answer -- so difficulty tracks how the interview is actually going
    rather than being fixed up front."""
    if running_avg is None:
        return "- Difficulty: moderate (this is early in the interview)."
    if running_avg >= 7.5:
        return "- Difficulty: the candidate has answered strongly so far -- ask a noticeably HARDER, more in-depth question."
    if running_avg >= 5:
        return "- Difficulty: the candidate is doing okay so far -- keep difficulty MODERATE, slightly more challenging."
    return "- Difficulty: the candidate has been struggling so far -- ask an EASIER, more approachable question."


# Last-resort, role-agnostic questions used ONLY if the model keeps
# producing duplicates after every retry -- guarantees the candidate is
# never asked the same question twice in one interview, even in the worst
# case. Kept well above any realistic target_question_count so there's
# always an unused one left.
_FALLBACK_QUESTIONS = [
    "Tell me about a challenging project you worked on and how you handled it.",
    "What do you consider your key strengths for this role?",
    "Describe a time you had to learn a new skill quickly for work.",
    "How do you prioritize tasks when you're under a tight deadline?",
    "Tell me about a time you disagreed with a teammate and how you resolved it.",
    "What interests you most about this position?",
    "Describe a mistake you made at work and what you learned from it.",
    "How do you stay current with developments in your field?",
    "Tell me about a time you had to work with a difficult stakeholder or client.",
    "What's a piece of feedback you received that changed how you work?",
    "Walk me through how you'd approach a problem you've never seen before.",
    "What does success look like to you in this role?",
]


def _normalize_question(text: str) -> str:
    return " ".join((text or "").lower().split())


def _is_duplicate_question(candidate_q: str, asked: list[str]) -> bool:
    """True if candidate_q is (near-)identical to a question already asked.
    Catches both exact repeats and trivial rewordings (e.g. punctuation or a
    tacked-on "Can you tell me..." prefix) that a small local model tends to
    produce when it "repeats" a question rather than always emitting a
    byte-for-byte copy."""
    norm_candidate = _normalize_question(candidate_q)
    if not norm_candidate:
        return False
    for prior in asked:
        norm_prior = _normalize_question(prior)
        if not norm_prior:
            continue
        if norm_candidate == norm_prior:
            return True
        if SequenceMatcher(None, norm_candidate, norm_prior).ratio() >= 0.85:
            return True
    return False


async def evaluate_and_generate_next(
    job: dict, candidate: dict, resume: dict | None,
    question: str, answer_transcript: str, qa_history: list[dict],
) -> dict:
    """Evaluate the just-given answer AND generate the next question in a
    single LLM call, instead of two sequential calls. This halves per-turn
    latency (the dominant cause of the wait growing turn over turn), and
    only the last few exchanges are fed back in (not the whole growing
    transcript) so prompt size -- and therefore latency -- stays roughly flat
    across the interview instead of creeping up every question."""
    recent = qa_history[-3:]
    history_text = "\n".join(
        f"- Q: {qa.get('question', '')}\n"
        f"  A: {qa.get('answer_transcript', '') or '(no answer captured)'}"
        for qa in recent
    ) or "(none yet)"
    # `question` (the one just answered) is NOT yet in qa_history at this
    # point -- it's still being evaluated in this same call -- so it must be
    # added explicitly here. Leaving it out meant the most-recently-asked
    # question (the one a model is most likely to echo back) was never on
    # the "don't repeat" list, which was causing back-to-back repeats.
    asked_questions = [qa.get("question", "") for qa in qa_history] + [question]
    already_asked = "\n".join(f"- {q}" for q in asked_questions if q) or "(none yet)"
    difficulty_guidance = _difficulty_guidance(_running_average(qa_history))

    def _build_prompt(extra_note: str = "") -> str:
        return f"""You are conducting a short, spoken screening interview for this role.

JOB DESCRIPTION:
{_job_context(job)}

CANDIDATE RESUME:
{_candidate_context(candidate, resume)}

QUESTION JUST ASKED: {question}
CANDIDATE'S ANSWER (transcribed from speech, may contain minor transcription errors): {answer_transcript or "(no answer captured)"}

Recent exchange(s) for context:
{history_text}

Questions already asked (never repeat one of these, including the one just asked above):
{already_asked}

TASK 1: Rate the candidate's answer above internally on a 0-10 scale for each of: relevance, correctness, job_relevance, skill_demonstration, completeness.

TASK 2: Generate ONE new interview question that continues the interview. Rules:
{difficulty_guidance}
- Specific to this job description and/or this candidate's resume.
- Short and direct (one sentence), quick to answer out loud.
- Do not repeat a question already asked, and do not just reword one of them.
{extra_note}
Respond ONLY with strict JSON:
{{"evaluation": {{"relevance": 0, "correctness": 0, "job_relevance": 0, "skill_demonstration": 0, "completeness": 0, "notes": "one short internal note"}}, "next_question": "..."}}
"""

    last_evaluation: dict = {}
    extra_note = ""
    # Several attempts: the model occasionally echoes an already-asked
    # question despite the instruction, so on a detected duplicate we retry
    # with an explicit callout naming the rejected question.
    for attempt in range(4):
        try:
            raw = await _ollama_generate(_build_prompt(extra_note), system="You are a concise technical interviewer and a strict but fair evaluator. Output valid JSON only.")
            data = _parse_json(raw)
            evaluation = data.get("evaluation") or {}
            next_question = (data.get("next_question") or "").strip()
            if not next_question:
                raise ValueError("empty next_question")
        except Exception:
            logger.exception("AI Interview: combined evaluate+next-question generation failed (attempt %s/4)", attempt + 1)
            continue

        last_evaluation = evaluation
        if not _is_duplicate_question(next_question, asked_questions):
            return {"evaluation": evaluation, "next_question": next_question}

        logger.warning("AI Interview: generated a duplicate/near-duplicate question, retrying: %r", next_question)
        extra_note = f'- Your last suggestion, "{next_question}", was too similar to one already asked -- pick a different topic entirely.\n'

    # Hard guarantee: never send the candidate a repeat, even in the worst
    # case where the model keeps echoing prior questions. Fall back to a
    # role-agnostic question the model hasn't (and can't have) produced.
    for fallback_q in _FALLBACK_QUESTIONS:
        if not _is_duplicate_question(fallback_q, asked_questions):
            logger.warning("AI Interview: exhausted retries, using a fallback question instead of risking a repeat.")
            return {"evaluation": last_evaluation, "next_question": fallback_q}

    raise RuntimeError("Unable to generate a non-repeating next question.")


async def generate_question(job: dict, candidate: dict, resume: dict | None, qa_history: list[dict]) -> str:
    """Generate the next short, job-specific, resume-specific interview
    question. Uses the previous answer (if any) to produce a natural
    follow-up when useful."""
    history_text = ""
    if qa_history:
        prior = qa_history[-1]
        history_text = (
            f"\nThe candidate was just asked: \"{prior.get('question', '')}\"\n"
            f"They answered: \"{prior.get('answer_transcript', '') or '(no answer captured)'}\"\n"
            "If it makes sense, ask a short natural follow-up. Otherwise move to a new area."
        )

    already_asked = "\n".join(f"- {qa.get('question', '')}" for qa in qa_history) or "(none yet)"

    prompt = f"""You are conducting a short, spoken screening interview for this role.

JOB DESCRIPTION:
{_job_context(job)}

CANDIDATE RESUME:
{_candidate_context(candidate, resume)}

Questions already asked:
{already_asked}
{history_text}

Generate ONE new interview question. Rules:
- Short and direct (one sentence).
- Specific to this job description and/or this candidate's resume.
- Quick to answer out loud (not a multi-part question).
- Do not repeat a question already asked.

Respond ONLY with strict JSON: {{"question": "..."}}
"""
    try:
        raw = await _ollama_generate(prompt, system="You are a concise technical interviewer. Output valid JSON only.")
        data = _parse_json(raw)
        question = (data.get("question") or "").strip()
        if question:
            return question
    except Exception:
        logger.exception("AI Interview: question generation failed")
    raise RuntimeError("Unable to generate the next question.")


async def evaluate_answer(job: dict, candidate: dict, resume: dict | None, question: str, answer_transcript: str) -> dict:
    """Internal-only evaluation of one answer. Never shown to the candidate."""
    prompt = f"""You are evaluating a candidate's spoken interview answer.

JOB DESCRIPTION:
{_job_context(job)}

CANDIDATE RESUME:
{_candidate_context(candidate, resume)}

QUESTION: {question}
CANDIDATE ANSWER (transcribed from speech, may contain minor transcription errors): {answer_transcript or "(no answer captured)"}

Rate this answer internally on a 0-10 scale for each of:
- relevance
- correctness
- job_relevance
- skill_demonstration
- completeness

Respond ONLY with strict JSON:
{{"relevance": 0, "correctness": 0, "job_relevance": 0, "skill_demonstration": 0, "completeness": 0, "notes": "one short internal note"}}
"""
    try:
        raw = await _ollama_generate(prompt, system="You are a strict but fair technical interview evaluator. Output valid JSON only.")
        return _parse_json(raw)
    except Exception:
        logger.exception("AI Interview: answer evaluation failed")
        return {"relevance": 0, "correctness": 0, "job_relevance": 0, "skill_demonstration": 0, "completeness": 0, "notes": "Evaluation failed."}


async def final_decision(job: dict, candidate: dict, qa_history: list[dict]) -> dict:
    """Aggregate all Q&A + per-answer evaluations into a final PASS/FAIL."""
    transcript_block = "\n\n".join(
        f"Q{i + 1}: {qa.get('question', '')}\n"
        f"A{i + 1}: {qa.get('answer_transcript', '') or '(no answer captured)'}\n"
        f"Internal scores: {json.dumps(qa.get('evaluation', {}))}"
        for i, qa in enumerate(qa_history)
    )

    prompt = f"""You are making a final hiring-screen decision after a short AI interview.

JOB DESCRIPTION:
{_job_context(job)}

CANDIDATE RESUME:
{_candidate_context(candidate, None)}

FULL INTERVIEW TRANSCRIPT AND INTERNAL SCORES:
{transcript_block}

Based on overall relevance, correctness, job fit, skill demonstration, and completeness across all answers,
decide a final result of exactly "PASS" or "FAIL".

Respond ONLY with strict JSON: {{"result": "PASS", "summary": "one short internal paragraph explaining why"}}
("result" must be exactly "PASS" or "FAIL")
"""
    try:
        raw = await _ollama_generate(prompt, system="You are a fair, consistent hiring-screen decision maker. Output valid JSON only.")
        data = _parse_json(raw)
        result = str(data.get("result", "")).strip().upper()
        if result not in {"PASS", "FAIL"}:
            # Fall back to a simple average-score threshold if the model didn't
            # follow the exact PASS/FAIL contract.
            result = _fallback_result(qa_history)
        return {"result": result, "summary": data.get("summary", "")}
    except Exception:
        logger.exception("AI Interview: final decision failed")
        return {"result": _fallback_result(qa_history), "summary": "AI decision unavailable; used fallback scoring."}


def _fallback_result(qa_history: list[dict]) -> str:
    if not qa_history:
        return "FAIL"
    totals = []
    for qa in qa_history:
        ev = qa.get("evaluation") or {}
        scores = [ev.get(k, 0) for k in ("relevance", "correctness", "job_relevance", "skill_demonstration", "completeness")]
        if scores:
            totals.append(sum(scores) / len(scores))
    avg = sum(totals) / len(totals) if totals else 0
    return "PASS" if avg >= 6 else "FAIL"
