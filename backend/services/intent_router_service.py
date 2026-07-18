import json
import logging
import httpx
from pydantic import BaseModel

from backend.services.copilot_context_service import get_system_context

logger = logging.getLogger(__name__)

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "qwen2.5-coder:7b"

class CopilotResponse(BaseModel):
    reply: str
    action_required: bool = False
    action_type: str | None = None
    action_payload: dict | None = None

async def process_copilot_message(message: str, history: list[dict]) -> CopilotResponse:
    """
    Routes the message through Ollama to determine intent, answer the question, or stage an action.
    """
    context = await get_system_context()
    
    # Format history
    history_str = ""
    for msg in history[-5:]:  # Keep last 5 for context window limits
        role = msg.get("role", "user")
        content = msg.get("content", "")
        history_str += f"{role.upper()}: {content}\n"
        
    prompt = f"""You are HirePilot Copilot, an AI HR Assistant.
    
    {context}
    
    Recent Chat History:
    {history_str}
    
    USER MESSAGE: {message}
    
    INSTRUCTIONS:
    Analyze the user message. Determine if they are asking a question about the system data, or if they want to perform an action.
    Valid actions are: 
    - "DRAFT_EMAIL": drafting an email to a candidate. Requires candidate ID and context.
    - "SCHEDULE_INTERVIEW": scheduling an interview.
    - "NONE": no action needed, just answering a question.
    
    Respond in STRICT JSON format matching this schema:
    {{
        "reply": "Your conversational response here.",
        "action_required": boolean,
        "action_type": "DRAFT_EMAIL" or "SCHEDULE_INTERVIEW" or null,
        "action_payload": {{}} (include any extracted params like candidate_id, date, etc. if action is required, else null)
    }}
    """
    
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                OLLAMA_URL,
                json={
                    "model": MODEL_NAME,
                    "prompt": prompt,
                    "format": "json",
                    "stream": False,
                    "options": {"temperature": 0.2}
                },
                timeout=45.0
            )
            
            if resp.status_code == 200:
                data = resp.json()
                response_text = data.get("response", "{}")
                parsed = json.loads(response_text)
                return CopilotResponse(
                    reply=parsed.get("reply", "I processed your request."),
                    action_required=parsed.get("action_required", False),
                    action_type=parsed.get("action_type"),
                    action_payload=parsed.get("action_payload")
                )
            else:
                return CopilotResponse(reply="I'm having trouble connecting to my AI core.")
                
    except Exception as e:
        logger.error(f"Copilot inference error: {e}")
        return CopilotResponse(reply="Sorry, I encountered an internal error while thinking.")
