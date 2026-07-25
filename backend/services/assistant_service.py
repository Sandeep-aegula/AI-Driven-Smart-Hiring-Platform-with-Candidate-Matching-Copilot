import json
import logging
import asyncio
import httpx
from pathlib import Path

logger = logging.getLogger(__name__)

OLLAMA_API_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "qwen2.5-coder:7b"

# Load prompts
PROMPTS_DIR = Path(__file__).parent.parent.parent / "frontend" / "prompts"

def _load_prompt(filename: str) -> str:
    path = PROMPTS_DIR / filename
    if path.exists():
        return path.read_text(encoding="utf-8")
    return ""

SYSTEM_PROMPT = _load_prompt("assistant_system_prompt.md")
WORKFLOW_PROMPT = _load_prompt("workflow.md")
FAQ_PROMPT = _load_prompt("faq.md")

FULL_SYSTEM_PROMPT = f"""
{SYSTEM_PROMPT}

==================================================
KNOWLEDGE BASE: WORKFLOWS
==================================================
{WORKFLOW_PROMPT}

==================================================
KNOWLEDGE BASE: FAQ
==================================================
{FAQ_PROMPT}
"""

async def chat(message: str, session_id: str, current_page: str, history: list[dict]) -> str:
    """
    Generate response for the floating AI assistant based on the knowledge base.
    """
    
    # Build prompt with history
    parts = [f"SYSTEM: {FULL_SYSTEM_PROMPT}"]
    
    if current_page:
        parts.append(f"SYSTEM: The user is currently viewing the '{current_page}' page.")
    
    for msg in history[-10:]:
        role = msg.get("role", "user").upper()
        content = msg.get("content", "")
        parts.append(f"{role}: {content}")
        
    parts.append(f"USER: {message}")
    parts.append("ASSISTANT:")
    
    final_prompt = "\n\n".join(parts)
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                OLLAMA_API_URL,
                json={
                    "model": MODEL_NAME,
                    "prompt": final_prompt,
                    "stream": False,
                    "options": {"temperature": 0.3, "num_predict": 512}
                },
                timeout=30.0
            )
            response.raise_for_status()
            result = response.json()
            return result.get("response", "").strip()
            
    except httpx.ConnectError as e:
        logger.error(f"Ollama connection error: {e}")
        from fastapi import HTTPException
        raise HTTPException(status_code=503, detail=f"AI Service (Ollama) is not running or unreachable. Error: {str(e)}")
    except httpx.TimeoutException as e:
        logger.error(f"Ollama timeout: {e}")
        from fastapi import HTTPException
        raise HTTPException(status_code=504, detail=f"Timeout after 30 seconds waiting for Ollama: {str(e)}")
    except httpx.HTTPStatusError as e:
        logger.error(f"Ollama HTTP error: {e}")
        from fastapi import HTTPException
        raise HTTPException(status_code=502, detail=f"Ollama returned an error: HTTP {e.response.status_code}")
    except Exception as e:
        logger.error(f"Error calling AI Assistant LLM: {e}")
        from fastapi import HTTPException
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")
