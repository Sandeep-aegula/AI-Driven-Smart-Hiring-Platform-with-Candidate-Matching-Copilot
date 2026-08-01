import logging
from collections import OrderedDict
from typing import Optional

from backend.services.ollama_service import OllamaService, OllamaServiceError, ollama_service

logger = logging.getLogger(__name__)

# Bounded per-session history stored in memory.
# In production, replace with Redis/DB-backed sessions.
_session_histories: "OrderedDict[str, list[dict]]" = OrderedDict()
_MAX_HISTORY_LENGTH = 20
_MAX_SESSIONS = 100


class ChatService:
    """Business logic for the AI Copilot chat endpoint."""

    def __init__(self, ollama: OllamaService = ollama_service) -> None:
        self.ollama = ollama

    def _get_history(self, session_id: str) -> list[dict]:
        if session_id not in _session_histories:
            _session_histories[session_id] = []
            # Evict oldest session if we exceed the cap
            if len(_session_histories) > _MAX_SESSIONS:
                _session_histories.popitem(last=False)
        return _session_histories[session_id]

    def _append(self, session_id: str, role: str, content: str) -> None:
        history = self._get_history(session_id)
        history.append({"role": role, "content": content})
        # Keep history bounded per session
        if len(history) > _MAX_HISTORY_LENGTH:
            _session_histories[session_id] = history[-_MAX_HISTORY_LENGTH:]

    async def chat(self, session_id: str, message: str) -> str:
        """
        Process a user message and return the assistant's reply.

        Handles:
        - Session history retrieval and updates
        - Delegation to Ollama
        - Graceful error handling with user-friendly messages
        """
        if not message.strip():
            return "Please enter a message so I can help you."

        history = self._get_history(session_id)

        try:
            reply = await self.ollama.chat(message, history)
        except OllamaServiceError as exc:
            logger.warning("Chat error for session %s: %s", session_id, exc)
            return str(exc)
        except Exception as exc:
            logger.exception("Unexpected chat error for session %s", session_id)
            return "Sorry, I encountered an unexpected error. Please try again."

        self._append(session_id, "user", message)
        self._append(session_id, "assistant", reply)
        return reply

    async def chat_rag(self, session_id: str, original_message: str, rag_prompt: str) -> str:
        """
        Process a user message using a RAG prompt.
        """
        if not original_message.strip():
            return "Please enter a message so I can help you."

        history = self._get_history(session_id)

        try:
            reply = await self.ollama.chat_rag(rag_prompt, history)
        except OllamaServiceError as exc:
            logger.warning("Chat error for session %s: %s", session_id, exc)
            return str(exc)
        except Exception as exc:
            logger.exception("Unexpected chat error for session %s", session_id)
            return "Sorry, I encountered an unexpected error. Please try again."

        self._append(session_id, "user", original_message)
        self._append(session_id, "assistant", reply)
        return reply

    async def get_history(self, session_id: str) -> list[dict]:
        return list(self._get_history(session_id))

    def clear_history(self, session_id: str) -> None:
        _session_histories.pop(session_id, None)


# Module-level singleton used by FastAPI routes
chat_service = ChatService()
