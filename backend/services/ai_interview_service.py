import json
import logging
import asyncio
import re
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


def _extract_json_array(text: str) -> list | None:
    """Extract a JSON array from text, handling common formatting issues."""
    if not text:
        return None
    
    # Try to find JSON array in the text
    text = text.strip()
    
    # Remove markdown code fences
    if text.startswith("```json"):
        text = text[7:]
    if text.startswith("```"):
        text = text[3:]
    if text.endswith("```"):
        text = text[:-3]
    text = text.strip()
    
    # Try direct parsing
    try:
        result = json.loads(text)
        if isinstance(result, list):
            return result
    except json.JSONDecodeError:
        pass
    
    # Try to find array brackets
    start = text.find('[')
    end = text.rfind(']')
    if start >= 0 and end > start:
        try:
            result = json.loads(text[start:end+1])
            if isinstance(result, list):
                return result
        except json.JSONDecodeError:
            pass
    
    # Try to find multiple objects and combine them
    # Look for patterns like {...}{...} or {...}, {...}
    objects = []
    depth = 0
    start_idx = -1
    for i, char in enumerate(text):
        if char == '{':
            if depth == 0:
                start_idx = i
            depth += 1
        elif char == '}':
            if depth > 0:
                depth -= 1
                if depth == 0 and start_idx >= 0:
                    try:
                        obj = json.loads(text[start_idx:i+1])
                        if isinstance(obj, dict):
                            objects.append(obj)
                    except json.JSONDecodeError:
                        pass
                    start_idx = -1
    
    if objects:
        return objects
    
    return None


async def generate_interview_questions(job_context: dict, candidate_context: dict, round_type: str, difficulty: str, count: int) -> list[dict]:
    candidate_skills = _skill_names(candidate_context.get("skills", []))
    resumes = candidate_context.get("resumes", [])
    latest_resume = resumes[-1] if resumes else {}
    resume_summary = latest_resume.get("summary") or candidate_context.get("summary", "")
    experience = latest_resume.get("experience") or candidate_context.get("experience", [])
    
    # Build a more explicit prompt with examples
    prompt = f"""You are an expert technical interviewer. Generate exactly {count} interview questions for a candidate.

JOB: {job_context.get('title')} - {job_context.get('department')}
ROUND TYPE: {round_type}
DIFFICULTY: {difficulty}
CANDIDATE SKILLS: {', '.join(candidate_skills) if candidate_skills else 'Unknown'}
CANDIDATE RESUME SUMMARY: {resume_summary or 'Not available'}
CANDIDATE EXPERIENCE: {json.dumps(experience, default=str)}

CRITICAL: You MUST respond with a valid JSON array containing exactly {count} objects. Each object must have exactly these three string fields:
- "question": The interview question
- "model_answer": A good answer the candidate should provide
- "evaluation_guideline": What the interviewer should look for

Example format:
[
  {{
    "question": "Describe a challenging bug you fixed recently.",
    "model_answer": "The candidate should describe the bug, their debugging process, and the solution.",
    "evaluation_guideline": "Look for systematic debugging, root cause analysis, and prevention measures."
  }},
  {{
    "question": "How do you optimize database queries?",
    "model_answer": "The candidate should mention indexing, query plans, caching, and avoiding N+1 queries.",
    "evaluation_guideline": "Look for practical experience with performance tuning."
  }}
]

Do NOT include any text before or after the JSON array. Do NOT use markdown formatting."""
    
    try:
        res = await asyncio.wait_for(_call_ollama(prompt, json_format=True), timeout=35.0)
    except (asyncio.TimeoutError, Exception) as exc:
        logger.warning("Interview-question generation failed: %s", exc)
        return fallback_question(job_context.get("title", ""), "AI generation unavailable")

    # Try to extract JSON array from response
    questions = _extract_json_array(res)
    
    if not questions or not isinstance(questions, list) or len(questions) == 0:
        logger.warning("Interview-question generation returned malformed JSON: %r", res)
        return fallback_question(job_context.get("title", ""), "AI returned malformed JSON")

    normalized = []
    for item in questions:
        if not isinstance(item, dict):
            logger.warning("Interview-question generation returned non-dict item: %r", item)
            continue
        # Validate required fields
        if not all(isinstance(item.get(key), str) and item[key].strip() for key in ("question", "model_answer", "evaluation_guideline")):
            logger.warning("Interview-question generation returned invalid question item: %r", item)
            continue
        normalized.append({key: item[key].strip() for key in ("question", "model_answer", "evaluation_guideline")})
    
    if not normalized:
        logger.warning("No valid questions after normalization")
        return fallback_question(job_context.get("title", ""), "AI returned malformed JSON")
    
    logger.info("Successfully generated %d interview questions", len(normalized))
    
    # If we got fewer questions than requested, pad with fallback
    while len(normalized) < count:
        fallback = fallback_question(job_context.get("title", ""), "AI generated insufficient questions")
        normalized.extend(fallback)
    
    return normalized[:count]
