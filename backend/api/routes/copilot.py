import logging
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from backend.scripts.services.chat_service import chat_service
from backend.scripts.services.context_retrieval_service import detect_intent, retrieve_context, build_rag_prompt

logger = logging.getLogger(__name__)
router = APIRouter()


class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None
    current_page: Optional[str] = None


class ChatResponse(BaseModel):
    response: str


@router.post("/chat", response_model=ChatResponse)
async def chat_with_copilot(req: ChatRequest):
    """
    Simple chat endpoint for the AI Copilot.

    Frontend sends:
        { "message": "...", "session_id": "optional-session-id" }

    Backend:
        - Maintains per-session conversation history
        - Calls Ollama with system prompt + history + latest message
        - Returns plain text response
    """
    session_id = req.session_id or "default"
    if not req.message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty.")

    try:
        # RAG context retrieval flow
        intents = await detect_intent(req.message)
        db_context = await retrieve_context(intents)
        rag_prompt = build_rag_prompt(req.message, db_context, req.current_page)
        
        reply = await chat_service.chat_rag(session_id, req.message, rag_prompt)
    except Exception as exc:
        logger.exception("Chat endpoint error: %s", exc)
        raise HTTPException(status_code=500, detail="Failed to process chat message.")

    return ChatResponse(response=reply)


@router.get("/session/{session_id}/history")
async def get_history(session_id: str):
    history = await chat_service.get_history(session_id)
    return {"history": history}


@router.get("/suggestions")
async def get_suggestions():
    return {
        "suggestions": [
            "Show top candidates for the Data Scientist role",
            "Write a rejection email for candidate ID 1",
            "Summarize the hiring pipeline status",
            "What is our current hiring velocity?",
            "Extract key skills from the latest uploaded resume",
            "Schedule interview feedback for tomorrow",
        ]
    }
