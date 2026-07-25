from fastapi import APIRouter
from pydantic import BaseModel
from typing import List, Optional
from backend.services.assistant_service import chat

router = APIRouter()

class ChatMessage(BaseModel):
    role: str
    content: str

class AssistantChatRequest(BaseModel):
    session_id: str
    message: str
    history: List[ChatMessage] = []
    current_page: str = ""

class AssistantChatResponse(BaseModel):
    response: str

@router.post("/chat", response_model=AssistantChatResponse)
async def chat_with_assistant(req: AssistantChatRequest):
    history_dicts = [{"role": msg.role, "content": msg.content} for msg in req.history]
    
    res = await chat(
        message=req.message,
        session_id=req.session_id,
        current_page=req.current_page,
        history=history_dicts
    )
    
    return AssistantChatResponse(response=res)

@router.get("/suggestions")
async def get_suggestions():
    return {
        "suggestions": [
            "How do I upload resumes?",
            "Generate a Job Description",
            "How do I hire a candidate?",
            "Explain AI Screening",
            "Show Analytics features",
            "Employee AI Insights",
            "How to send Offer Letters"
        ]
    }
