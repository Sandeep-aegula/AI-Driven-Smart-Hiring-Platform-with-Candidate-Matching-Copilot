import io
import json
import logging
import httpx
from fastapi import HTTPException
from pydantic import ValidationError
from backend.schemas.entities import AIGeneratedJobDraft

logger = logging.getLogger(__name__)

OLLAMA_URL = "http://localhost:11434/api/generate"
OLLAMA_MODEL = "qwen2.5-coder:7b"
TIMEOUT_SECONDS = 30.0

def parse_document(file_bytes: bytes, filename: str) -> str:
    """Extract text from PDF, DOCX, or TXT."""
    ext = filename.split(".")[-1].lower()
    
    if ext == "txt":
        try:
            return file_bytes.decode("utf-8")
        except UnicodeDecodeError:
            # Fallback for some windows encodings
            return file_bytes.decode("latin-1")
            
    elif ext == "pdf":
        import fitz  # PyMuPDF
        try:
            # fitz.open(stream=...) for in-memory bytes
            doc = fitz.open(stream=file_bytes, filetype="pdf")
            text = ""
            for page in doc:
                text += page.get_text()
            return text
        except Exception as e:
            logger.error(f"Error parsing PDF: {e}")
            raise ValueError("Failed to parse PDF document")
            
    elif ext == "docx":
        import docx
        try:
            doc = docx.Document(io.BytesIO(file_bytes))
            return "\n".join([p.text for p in doc.paragraphs])
        except Exception as e:
            logger.error(f"Error parsing DOCX: {e}")
            raise ValueError("Failed to parse DOCX document")
            
    else:
        raise ValueError(f"Unsupported file extension: {ext}")


async def generate_job_description(raw_text: str) -> dict:
    """Send text to Ollama and ask it to output a structured JSON job description draft."""
    prompt = f"""You are an expert HR Recruiter. I am providing you with raw text extracted from a job requisition document.
Extract and polish the information into a structured JSON job description.

RAW TEXT:
{raw_text}

Respond ONLY with valid JSON exactly matching this structure, and no other text or markdown block formatting.
{{
    "required_skills": ["skill1", "skill2"],
    "preferred_skills": ["skill3"],
    "experience_required": "e.g., 3-5 years",
    "education_requirements": "e.g., Bachelor's in CS",
    "responsibilities": ["resp1", "resp2"],
    "qualifications": ["qual1", "qual2"],
    "job_description": "A well written, polished 2-3 paragraph summary of the role."
}}
"""
    return await _call_ollama(prompt)


async def regenerate_job_description(raw_text: str, current_draft: dict) -> dict:
    """Ask Ollama to regenerate or improve the draft."""
    prompt = f"""You are an expert HR Recruiter. I am providing you with raw text from a job requisition, along with a current draft of the job description.
Please improve the draft, fix any missing information based on the raw text, and return an updated structured JSON job description.

RAW TEXT:
{raw_text}

CURRENT DRAFT:
{json.dumps(current_draft, indent=2)}

Respond ONLY with valid JSON exactly matching this structure, and no other text or markdown block formatting.
{{
    "required_skills": ["skill1", "skill2"],
    "preferred_skills": ["skill3"],
    "experience_required": "e.g., 3-5 years",
    "education_requirements": "e.g., Bachelor's in CS",
    "responsibilities": ["resp1", "resp2"],
    "qualifications": ["qual1", "qual2"],
    "job_description": "A well written, polished 2-3 paragraph summary of the role."
}}
"""
    return await _call_ollama(prompt)


async def _call_ollama(prompt: str) -> dict:
    payload = {
        "model": OLLAMA_MODEL,
        "prompt": prompt,
        "stream": False,
        "format": "json"
    }
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(OLLAMA_URL, json=payload, timeout=TIMEOUT_SECONDS)
            response.raise_for_status()
            
            result = response.json()
            content = result.get("response", "{}")
            
            # Clean up the markdown JSON block if the model included it despite instructions
            content = content.strip()
            if content.startswith("```json"):
                content = content[7:]
            if content.endswith("```"):
                content = content[:-3]
                
            parsed_json = json.loads(content)
            
            # Validate output matches the expected Pydantic schema
            valid_draft = AIGeneratedJobDraft(**parsed_json)
            return valid_draft.model_dump()
            
    except httpx.TimeoutException:
        logger.error("Ollama API timed out")
        raise HTTPException(status_code=504, detail="AI generation timed out (exceeded 30 seconds). Please try again.")
    except Exception as e:
        logger.error(f"Ollama API error or parse error: {e}")
        raise HTTPException(status_code=502, detail=f"AI generation failed: {str(e)}")
