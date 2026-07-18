import json
import logging
import httpx
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

OLLAMA_URL = "http://localhost:11434/api/generate"
OLLAMA_MODEL = "qwen2.5-coder:7b"
TIMEOUT_SECONDS = 30.0

async def parse_resume_to_json(raw_text: str) -> dict:
    """Parse raw resume text into a structured JSON profile."""
    prompt = f"""You are an expert HR AI. Extract information from the following resume text.
If a field is not found, leave string fields empty and array fields empty.

RAW TEXT:
{raw_text}

Respond ONLY with valid JSON exactly matching this structure:
{{
    "name": "Full Name",
    "email": "email@example.com",
    "phone": "Phone number",
    "github": "Github link or username",
    "linkedin": "Linkedin link or username",
    "portfolio": "Portfolio link",
    "skills": ["Skill 1", "Skill 2"],
    "experience": ["Company 1 - Role 1 - Dates", "Company 2 - Role 2"],
    "education": ["Degree - University - Dates"],
    "projects": ["Project 1 summary"],
    "certifications": ["Cert 1"],
    "languages": ["English", "Spanish"]
}}
"""
    return await _call_ollama_with_retry(prompt)


async def evaluate_candidate_match(parsed_json: dict, job_requirements: dict) -> dict:
    """Evaluate a parsed candidate against job requirements to produce a match score and recommendation."""
    prompt = f"""You are an expert HR AI. Evaluate this candidate's profile against the job requirements.

CANDIDATE PROFILE:
{json.dumps(parsed_json, indent=2)}

JOB REQUIREMENTS:
{json.dumps(job_requirements, indent=2)}

Analyze the match and respond ONLY with valid JSON exactly matching this structure:
{{
    "resume_summary": "A 2-3 sentence professional summary of the candidate's background.",
    "match_score": 85, 
    "skill_match_breakdown": {{
        "matched_skills": ["Skill 1", "Skill 2"],
        "missing_skills": ["Skill 3"],
        "match_percentage": 85
    }},
    "hire_recommendation": "Strong Hire", 
    "reason": "Why this recommendation was given."
}}
Note: 'match_score' must be an integer between 0 and 100. 'hire_recommendation' must be one of: "Strong Hire", "Hire", "Hold", "Reject".
"""
    return await _call_ollama_with_retry(prompt)


async def _call_ollama_with_retry(prompt: str, retries: int = 1) -> dict:
    """Make HTTP call to Ollama with a retry-once-on-timeout policy."""
    payload = {
        "model": OLLAMA_MODEL,
        "prompt": prompt,
        "stream": False,
        "format": "json"
    }
    
    for attempt in range(retries + 1):
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(OLLAMA_URL, json=payload, timeout=TIMEOUT_SECONDS)
                response.raise_for_status()
                
                result = response.json()
                content = result.get("response", "{}").strip()
                
                if content.startswith("```json"):
                    content = content[7:]
                if content.endswith("```"):
                    content = content[:-3]
                    
                return json.loads(content)
                
        except httpx.TimeoutException:
            if attempt < retries:
                logger.warning(f"Ollama API timed out. Retrying attempt {attempt + 1}/{retries}...")
                continue
            logger.error("Ollama API timed out on all attempts.")
            raise
        except Exception as e:
            logger.error(f"Ollama API error: {e}")
            raise
