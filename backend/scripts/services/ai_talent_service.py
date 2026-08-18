import json
import logging
import asyncio
import httpx

logger = logging.getLogger(__name__)

OLLAMA_API_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "qwen2.5-coder:7b"

async def generate_talent_insights(employee_data: dict) -> dict:
    """
    Generate comprehensive AI talent insights for an employee based on their
    profile, skills, projects, and performance history.
    """
    
    # We construct a highly structured prompt asking for JSON
    prompt = f"""
You are an expert HR Talent & Development Manager AI.
Analyze the following employee data and provide a comprehensive talent insight report.
You MUST reply with ONLY a valid JSON object. Do not include markdown code blocks or conversational text.

Employee Data:
Name: {employee_data.get('name')}
Designation: {employee_data.get('designation')}
Department: {employee_data.get('department')}
Status: {employee_data.get('status')}
Location: {employee_data.get('work_location')}
Skills: {json.dumps(employee_data.get('skills', []))}
Experience: {json.dumps(employee_data.get('experience', []))}
Certifications: {json.dumps(employee_data.get('certifications', []))}
Achievements: {json.dumps(employee_data.get('achievements', []))}
Projects: {json.dumps(employee_data.get('projects', []))}
Performance History: {json.dumps(employee_data.get('performance_history', []))}
Notes/Feedback: {json.dumps(employee_data.get('notes', []))}

Your response MUST perfectly match this JSON schema. For 'technical' and 'leadership', return a dictionary of skills and their evaluations.
{{
    "overall_score": 89,
    "overall_rating": "Excellent",
    "executive_summary": "Summary of their performance...",
    "technical": {{
        "SQL Proficiency": {{"score": 90}},
        "Tableau Competency": {{"score": 85}}
    }},
    "leadership": {{
        "Project Management": "Strong",
        "Team Leadership": "Developing"
    }},
    "career_growth": {{
        "promotion_readiness": "High",
        "next_role": "Senior Software Engineer"
    }},
    "strengths": ["Strength 1", "Strength 2"],
    "improvements": ["Area 1", "Area 2"],
    "recommended_training": ["Training 1", "Training 2"],
    "risk_level": "Low",
    "future_potential": "High"
}}
"""

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                OLLAMA_API_URL,
                json={
                    "model": MODEL_NAME,
                    "prompt": prompt,
                    "stream": False,
                    "format": "json"
                },
                timeout=45.0
            )
            response.raise_for_status()
            result = response.json()
            
            raw_response = result.get("response", "")
            
            # Clean up potential markdown formatting from Ollama
            clean_json = raw_response.strip()
            if clean_json.startswith("```json"):
                clean_json = clean_json[7:]
            if clean_json.startswith("```"):
                clean_json = clean_json[3:]
            if clean_json.endswith("```"):
                clean_json = clean_json[:-3]
                
            insights = json.loads(clean_json.strip())
            from datetime import datetime
            insights["last_generated"] = datetime.utcnow().isoformat()
            return insights
            
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse AI insights JSON: {e}")
        return _fallback_insights()
    except Exception as e:
        logger.error(f"Error calling AI for talent insights: {e}")
        return _fallback_insights()

def _fallback_insights() -> dict:
    return {
        "error": "Unable to generate AI insights. Please verify that the AI service is running."
    }
