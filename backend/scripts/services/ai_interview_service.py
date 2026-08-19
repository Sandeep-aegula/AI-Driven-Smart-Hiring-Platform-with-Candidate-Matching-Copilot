import json
import logging
import asyncio
import re
from backend.scripts.services.ai_candidate_service import _call_ollama

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


def _extract_json_array(text) -> list | None:
    """Extract a JSON array from text, handling common formatting issues.

    ``text`` may be a raw string (markdown-fenced JSON), an already-parsed
    list, or a dict (e.g. from the Ollama JSON-mode response or an error
    sentinel).  All three cases are handled gracefully.
    """
    # Already a list — nothing to extract.
    if isinstance(text, list):
        return text if text else None

    # Dict returned by _call_ollama (e.g. error sentinel or structured response).
    if isinstance(text, dict):
        # Error sentinel from _call_ollama: {"error": "...", "stale": True}
        if "error" in text:
            logger.warning("_extract_json_array received error dict: %s", text)
            return None

        # Pattern 1: LLM returned {"questions": [...]} wrapper.
        if isinstance(text.get("questions"), list):
            logger.info("_extract_json_array: auto-recovered {questions:[...]} wrapper dict")
            return text["questions"] if text["questions"] else None

        # Pattern 2: LLM returned a single question object instead of an array.
        if all(k in text for k in ("question", "model_answer", "evaluation_guideline")):
            logger.info("_extract_json_array: auto-recovered single question object — wrapped in list")
            return [text]

        # Pattern 3: Wrapper dict with a string/list value in a known key.
        for key in ("response", "content", "text", "message"):
            value = text.get(key)
            if isinstance(value, str) and value.strip():
                return _extract_json_array(value)  # recurse on the string
            if isinstance(value, list):
                return value if value else None

        # None of the recoverable patterns matched.
        logger.warning(
            "_extract_json_array: truly malformed dict (no questions/question/wrapper key): %s",
            text,
        )
        return None

    if not isinstance(text, str) or not text:
        return None

    # --- String path (original logic, unchanged) ---
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
    prompt = f"""You are an expert technical interviewer. Generate exactly {count} interview question(s) for a candidate.

JOB: {job_context.get('title')} - {job_context.get('department')}
ROUND TYPE: {round_type}
DIFFICULTY: {difficulty}
CANDIDATE SKILLS: {', '.join(candidate_skills) if candidate_skills else 'Unknown'}
CANDIDATE RESUME SUMMARY: {resume_summary or 'Not available'}
CANDIDATE EXPERIENCE: {json.dumps(experience, default=str)}

OUTPUT RULES — READ CAREFULLY:
1. Your response MUST be a JSON ARRAY [ ... ] — even if only 1 question is requested.
2. NEVER return a bare object {{ ... }} at the top level. ALWAYS wrap in [ ].
3. Each element of the array must be an object with EXACTLY these three string keys:
   - "question": the interview question text
   - "model_answer": a strong answer the candidate should give
   - "evaluation_guideline": what the interviewer should look for
4. Do NOT add any text, explanation, or markdown before or after the JSON array.
5. Do NOT use ```json fences.

EXACT OUTPUT FORMAT (copy this structure, fill in your content):
[
  {{
    "question": "Describe a challenging bug you fixed recently.",
    "model_answer": "The candidate should describe the bug, their debugging process, and the solution.",
    "evaluation_guideline": "Look for systematic debugging, root cause analysis, and prevention measures."
  }},
  {{
    "question": "How do you optimize slow database queries?",
    "model_answer": "The candidate should mention indexing, query plans, caching, and avoiding N+1 queries.",
    "evaluation_guideline": "Look for practical experience with profiling and performance tuning."
  }}
]

Generate exactly {count} question(s) following the format above."""
    
    try:
        question_schema = {
    "type": "array",
    "minItems": count,
    "maxItems": count,
    "items": {
        "type": "object",
        "properties": {
            "question": {"type": "string"},
            "model_answer": {"type": "string"},
            "evaluation_guideline": {"type": "string"}
        },
        "required": ["question", "model_answer", "evaluation_guideline"]
           }
           }
        
        
        
        res = await asyncio.wait_for(
    _call_ollama(prompt, json_format=True, schema=question_schema, num_predict=300 * count),
    timeout=150.0
)
        # res = await asyncio.wait_for(_call_ollama(prompt, json_format=True), timeout=35.0)
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
    
    # # If we got fewer questions than requested, pad with fallback
    # while len(normalized) < count:
    #     fallback = fallback_question(job_context.get("title", ""), "AI generated insufficient questions")
    #     normalized.extend(fallback)
    
    # return normalized[:count]
        # If we got fewer questions than requested, retry once before padding with fallback
    if len(normalized) < count:
        missing = count - len(normalized)
        retry_prompt = prompt + f"\n\nYour previous response only contained {len(normalized)} question(s). You MUST return exactly {count} questions, no fewer."
        try:
            # res2 = await asyncio.wait_for(_call_ollama(retry_prompt, json_format=True), timeout=35.0)
            res2 = await asyncio.wait_for(
    _call_ollama(retry_prompt, json_format=True, schema=question_schema, num_predict=300 * (count - len(normalized))),
    timeout=150.0
)
            more = _extract_json_array(res2) or []
            for item in more:
                if len(normalized) >= count:
                    break
                if isinstance(item, dict) and all(
                    isinstance(item.get(key), str) and item[key].strip()
                    for key in ("question", "model_answer", "evaluation_guideline")
                ):
                    normalized.append({key: item[key].strip() for key in ("question", "model_answer", "evaluation_guideline")})
        except Exception as exc:
            logger.warning("Retry for missing questions failed: %s", exc)

    # Only pad with fallback if the retry still didn't fill the gap, and never repeat identical text
    idx = 1
    while len(normalized) < count:
        fallback = fallback_question(job_context.get("title", ""), f"AI generated insufficient questions — filler {idx}/{count - len(normalized) + idx - 1}")
        normalized.extend(fallback)
        idx += 1

    return normalized[:count]
