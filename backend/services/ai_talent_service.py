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
Skills: {json.dumps(employee_data.get('skills', []))}
Projects: {json.dumps(employee_data.get('projects', []))}
Performance History: {json.dumps(employee_data.get('performance_history', []))}

Your response MUST perfectly match this JSON schema:
{{
    "executive_summary": "A 2-3 sentence high-level summary of the employee's current standing and value.",
    "technical_assessment": "Analysis of their technical skills and project contributions.",
    "professional_assessment": "Analysis of their professional growth based on performance metrics.",
    "leadership_assessment": "Analysis of leadership potential or demonstrated leadership.",
    "communication_assessment": "Assessment of communication based on role and feedback.",
    "collaboration_assessment": "Teamwork and collaboration analysis.",
    "learning_and_adaptability": "How well they learn and adapt to new projects/skills.",
    "productivity_insights": "Analysis of their productivity metrics.",
    "career_growth": {{
        "promotion_readiness": "High/Medium/Low",
        "suggested_next_role": "String",
        "roadmap": ["Step 1", "Step 2", "Step 3"]
    }},
    "recommendations": ["Recommendation 1", "Recommendation 2", "Recommendation 3"],
    "overall_talent_score": 85, // Integer 0-100
    "rating": "Exceptional" // One of: Needs Improvement, Meets Expectations, Exceeds Expectations, Exceptional
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
            return insights
            
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse AI insights JSON: {e}")
        return _fallback_insights()
    except Exception as e:
        logger.error(f"Error calling AI for talent insights: {e}")
        return _fallback_insights()

def _fallback_insights() -> dict:
    return {
        "executive_summary": "AI Insights are currently unavailable. Please check the AI service.",
        "technical_assessment": "N/A",
        "professional_assessment": "N/A",
        "leadership_assessment": "N/A",
        "communication_assessment": "N/A",
        "collaboration_assessment": "N/A",
        "learning_and_adaptability": "N/A",
        "productivity_insights": "N/A",
        "career_growth": {
            "promotion_readiness": "Unknown",
            "suggested_next_role": "Unknown",
            "roadmap": []
        },
        "recommendations": ["Review manually due to AI timeout."],
        "overall_talent_score": 0,
        "rating": "Unknown",
        "error": "AI timeout or parsing failure"
    }
