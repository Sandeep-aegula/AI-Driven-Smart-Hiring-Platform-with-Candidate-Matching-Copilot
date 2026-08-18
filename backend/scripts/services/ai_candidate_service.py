import json
import logging
import httpx
from typing import Optional, Dict, Any, List

logger = logging.getLogger(__name__)

OLLAMA_URL = "http://localhost:11434/api/generate"
OLLAMA_MODEL = "qwen2.5-coder:7b"
TIMEOUT_SECONDS = 30.0


async def _call_ollama(prompt: str, json_format: bool = True) -> Any:
    payload = {
        "model": OLLAMA_MODEL,
        "prompt": prompt,
        "stream": False
    }
    if json_format:
        payload["format"] = "json"
        
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(OLLAMA_URL, json=payload, timeout=TIMEOUT_SECONDS)
            response.raise_for_status()
            result = response.json()
            content = result.get("response", "").strip()
            
            if json_format:
                if content.startswith("```json"):
                    content = content[7:]
                if content.endswith("```"):
                    content = content[:-3]
                return json.loads(content)
            return content
    except Exception as e:
        logger.error(f"Ollama API error: {e}")
        return {"error": "AI unavailable", "stale": True} if json_format else "[AI Unavailable. Using cached/stale data.]"


async def generate_ranking_explanation(candidate: dict, job_context: dict) -> str:
    prompt = f"""You are an expert HR AI. Based on the candidate's profile and the job requirements, write a 2-3 sentence explanation of why this candidate is a good or poor fit for the role.

CANDIDATE:
{json.dumps({k: candidate.get(k) for k in ['name', 'skills', 'experience', 'education', 'match_score']}, indent=2)}

JOB:
{json.dumps(job_context, indent=2)}

Respond with plain text only, no JSON, no formatting.
"""
    result = await _call_ollama(prompt, json_format=False)
    return result


async def analyze_skill_gap(candidate: dict, job_context: dict) -> dict:
    prompt = f"""You are an expert HR AI. Analyze the skill gap between the candidate and the job requirements.

CANDIDATE SKILLS: {json.dumps(candidate.get('skills', []))}
JOB REQUIREMENTS: {json.dumps(job_context.get('requirements', []) + job_context.get('preferred_skills', []))}

Respond EXACTLY in this JSON format:
{{
    "matched_skills": ["Skill 1", "Skill 2"],
    "missing_skills": ["Skill 3"],
    "match_percentage": 85,
    "improvement_suggestions": "Suggest what the candidate needs to learn or improve."
}}
"""
    result = await _call_ollama(prompt, json_format=True)
    if "error" in result:
        return {
            "matched_skills": [],
            "missing_skills": [],
            "match_percentage": candidate.get("match_score", 0),
            "improvement_suggestions": result["error"]
        }
    return result


async def compare_candidates(candidates: List[dict], job_context: dict) -> dict:
    c_data = []
    for c in candidates:
        c_data.append({
            "name": c.get("name"),
            "skills": c.get("skills"),
            "match_score": c.get("match_score"),
            "experience": c.get("experience", []),
        })
        
    prompt = f"""You are an expert HR AI. Compare these candidates for the given job.

JOB: {json.dumps(job_context, indent=2)}

CANDIDATES:
{json.dumps(c_data, indent=2)}

Respond EXACTLY in this JSON format:
{{
    "comparison_table": [
        {{
            "name": "Candidate Name",
            "strengths": "1-2 short bullet points",
            "weaknesses": "1-2 short bullet points"
        }}
    ],
    "recommendation": "A short paragraph explaining who is the best fit and why."
}}
"""
    return await _call_ollama(prompt, json_format=True)


async def draft_email(candidate: dict, job_context: dict, email_type: str) -> dict:
    prompt = f"""You are an expert HR AI. Draft an email to a candidate.
Type of email: {email_type}

CANDIDATE: {candidate.get('name')}
JOB: {job_context.get('title')}

Respond EXACTLY in this JSON format:
{{
    "subject": "Email Subject",
    "body": "The full body of the email. Use professional tone. Address the candidate by name."
}}
"""
    return await _call_ollama(prompt, json_format=True)
