import logging
import uuid
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional

from backend.services.intent_router_service import process_copilot_message, CopilotResponse

logger = logging.getLogger(__name__)

router = APIRouter()

# In-memory history for sessions
_chat_history = {}

class ChatMessage(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    session_id: str
    message: str

class ActionConfirmRequest(BaseModel):
    session_id: str
    action_type: str
    action_payload: dict

@router.post("/chat", response_model=CopilotResponse)
async def chat_with_copilot(req: ChatRequest):
    if req.session_id not in _chat_history:
        _chat_history[req.session_id] = []
        
    history = _chat_history[req.session_id]
    
    # Process via Ollama
    response = await process_copilot_message(req.message, history)
    
    # Append to history
    history.append({"role": "user", "content": req.message})
    history.append({"role": "assistant", "content": response.reply})
    
    # Keep history bounded
    if len(history) > 20:
        _chat_history[req.session_id] = history[-20:]
        
    return response

@router.post("/action/confirm")
async def confirm_action(req: ActionConfirmRequest):
    """
    Executes a side-effect action that the user confirmed via the UI.
    """
    # For now, we simulate success since the frontend will display the actual effects.
    # In a full implementation, this would map to endpoints in candidates.py or emails.py.
    logger.info(f"Confirmed action: {req.action_type} with payload {req.action_payload}")
    
    if req.session_id in _chat_history:
        _chat_history[req.session_id].append({"role": "system", "content": f"Action {req.action_type} executed successfully."})
        
    return {"status": "success", "message": f"Action {req.action_type} completed."}

@router.get("/session/{session_id}/history")
async def get_history(session_id: str):
    return {"history": _chat_history.get(session_id, [])}

@router.get("/suggestions")
async def get_suggestions():
    return {
        "suggestions": [
            "How many open roles do we have?",
            "Who are the top candidates for the Data Scientist role?",
            "Draft a rejection email for candidate ID 1.",
            "What is our current hiring velocity?"
        ]
    }
