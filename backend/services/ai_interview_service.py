import json
import logging
import asyncio
from backend.services.ai_candidate_service import _call_ollama

logger = logging.getLogger(__name__)

def fallback_question(job_title: str, reason: str | None = None) -> list[dict]:
    role = job_title or "target role"
    suffix = f" ({reason})" if reason else ""
    return [{
        "question": f"[Fallback] Tell me about the experience that best prepares you for the {role} role.{suffix}",
        "model_answer": "The candidate should connect a relevant project or responsibility to the role, explain their contribution, and describe the outcome.",
        "evaluation_guideline": "Look for concrete examples, ownership, role relevance, and clear communication."
    }]


def _skill_names(skills: list) -> list[str]:
    return [skill.get("name", "") if isinstance(skill, dict) else str(skill) for skill in skills if skill]


async def generate_interview_questions(job_context: dict, candidate_context: dict, round_type: str, difficulty: str, count: int) -> list[dict]:
    candidate_skills = _skill_names(candidate_context.get("skills", []))
    resumes = candidate_context.get("resumes", [])
    latest_resume = resumes[-1] if resumes else {}
    resume_summary = latest_resume.get("summary") or candidate_context.get("summary", "")
    experience = latest_resume.get("experience") or candidate_context.get("experience", [])
    prompt = f"""You are an expert technical interviewer. Generate a list of {count} interview questions for a candidate.
    
JOB: {job_context.get('title')} - {job_context.get('department')}
ROUND TYPE: {round_type}
DIFFICULTY: {difficulty}
CANDIDATE SKILLS: {', '.join(candidate_skills) if candidate_skills else 'Unknown'}
CANDIDATE RESUME SUMMARY: {resume_summary or 'Not available'}
CANDIDATE EXPERIENCE: {json.dumps(experience, default=str)}

For each question, provide a model answer and a brief evaluation guideline.
Respond EXACTLY in this JSON format (an array of objects):
[
    {{
        "question": "The interview question",
        "model_answer": "A good answer the candidate should provide",
        "evaluation_guideline": "What the interviewer should look for"
    }}
]
"""
    try:
        res = await asyncio.wait_for(_call_ollama(prompt, json_format=True), timeout=35.0)
    except (asyncio.TimeoutError, Exception) as exc:
        logger.warning("Interview-question generation failed: %s", exc)
        return fallback_question(job_context.get("title", ""), "AI generation unavailable")

    if not isinstance(res, list) or not res:
        logger.warning("Interview-question generation returned malformed JSON: %r", res)
        return fallback_question(job_context.get("title", ""), "AI returned malformed JSON")

    normalized = []
    for item in res:
        if not isinstance(item, dict) or not all(isinstance(item.get(key), str) and item[key].strip() for key in ("question", "model_answer", "evaluation_guideline")):
            logger.warning("Interview-question generation returned an invalid question item")
            return fallback_question(job_context.get("title", ""), "AI returned malformed JSON")
        normalized.append({key: item[key].strip() for key in ("question", "model_answer", "evaluation_guideline")})
    return normalized
