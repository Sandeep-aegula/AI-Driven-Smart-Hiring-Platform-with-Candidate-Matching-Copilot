"""services/llm_service.py - LLM service for AI Assistant. Service for communicating with LLM providers. """
from typing import Optional, List, Dict, Any
import httpx


class LLMService:
    """Service for communicating with LLM providers."""

    def __init__(self):
        self.backend_url = "http://localhost:8000"
        self._client: Optional[httpx.Client] = None

    def _get_client(self) -> httpx.Client:
        """Get or create the API client."""
        if self._client is None:
            self._client = httpx.Client(timeout=120.0)
        return self._client

    def chat(self, message: str, history: List[Dict[str, str]], context: Optional[Dict[str, Any]] = None) -> str:
        """Send a chat message to the backend AI service.

        Args:
            message: The user's message
            history: Conversation history
            context: Additional context (current page, etc.)

        Returns:
            The AI's response text
        """
        try:
            client = self._get_client()
            payload = {
                "message": message.strip(),
                "history": history[-10:],  # Send last 10 messages for context
                "context": context or {},
            }
            response = client.post(
                f"{self.backend_url}/copilot/chat",
                json=payload,
                timeout=120.0,
            )
            if response.status_code == 200:
                data = response.json()
                return data.get("response", "I received an empty response.")
            else:
                return f"Error: Backend returned status {response.status_code}"
        except Exception as e:
            return f"I'm having trouble connecting to the AI service: {str(e)}"


# Singleton instance
llm_service = LLMService()
