import json
import logging
from typing import AsyncGenerator, Optional

import httpx

logger = logging.getLogger(__name__)

OLLAMA_URL = "http://localhost:11434/api/generate"
OLLAMA_CHAT_URL = "http://localhost:11434/api/chat"
MODEL_NAME = "qwen2.5-coder:7b"
SYSTEM_PROMPT = (
    "You are HirePilot AI. You are an AI recruitment assistant. "
    "Help with hiring, resumes, recruiting, HR analytics, interviews, job descriptions, "
    "employee management, candidate screening and professional communication. "
    "Keep responses concise and professional."
)


class OllamaServiceError(Exception):
    """Raised when Ollama service is unavailable or returns an error."""


class OllamaService:
    """Singleton-style service for interacting with the local Ollama instance."""

    def __init__(self) -> None:
        self._client: Optional[httpx.AsyncClient] = None

    @property
    def client(self) -> httpx.AsyncClient:
        """Reuse a single AsyncClient across requests."""
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(timeout=60.0)
        return self._client

    async def close(self) -> None:
        if self._client and not self._client.is_closed:
            await self._client.aclose()

    async def health_check(self) -> bool:
        try:
            resp = await self.client.get("http://localhost:11434/", timeout=2.0)
            return resp.status_code == 200
        except Exception:
            return False

    async def list_models(self) -> list[str]:
        try:
            resp = await self.client.get("http://localhost:11434/api/tags", timeout=5.0)
            if resp.status_code == 200:
                data = resp.json()
                return [m.get("name", "") for m in data.get("models", [])]
        except Exception as exc:
            logger.error("Failed to list Ollama models: %s", exc)
        return []

    async def ensure_model_available(self) -> None:
        models = await self.list_models()
        if MODEL_NAME not in models:
            raise OllamaServiceError(f"Model {MODEL_NAME} not found.")

    def _build_prompt(self, message: str, history: list[dict]) -> str:
        """Build a single prompt string with system context and conversation history."""
        parts = [f"SYSTEM: {SYSTEM_PROMPT}"]
        for msg in history[-10:]:
            role = msg.get("role", "user").upper()
            content = msg.get("content", "")
            parts.append(f"{role}: {content}")
        parts.append(f"USER: {message}")
        parts.append("ASSISTANT:")
        return "\n\n".join(parts)

    async def generate(
        self,
        message: str,
        history: list[dict],
        *,
        stream: bool = False,
    ) -> str:
        """
        Send a prompt to Ollama and return the assistant's response text.

        Raises:
            OllamaServiceError: if Ollama is unreachable or the model is missing.
        """
        await self.ensure_model_available()
        prompt = self._build_prompt(message, history)

        payload = {
            "model": MODEL_NAME,
            "prompt": prompt,
            "stream": stream,
            "options": {"temperature": 0.2, "num_predict": 1024},
        }

        try:
            if stream:
                return await self._generate_stream(prompt, payload)
            resp = await self.client.post(
                OLLAMA_URL,
                json=payload,
                timeout=120.0,
            )
        except httpx.ConnectError:
            raise OllamaServiceError("Ollama server is not running.")
        except httpx.TimeoutException:
            raise OllamaServiceError("Ollama request timed out.")
        except Exception as exc:
            logger.error("Ollama generate failed: %s", exc)
            raise OllamaServiceError("Failed to get response from AI service.")

        if resp.status_code == 404:
            raise OllamaServiceError(f"Model {MODEL_NAME} not found.")
        if resp.status_code != 200:
            raise OllamaServiceError(f"Ollama returned status {resp.status_code}.")

        data = resp.json()
        return data.get("response", "").strip()

    async def _generate_stream(
        self, prompt: str, payload: dict
    ) -> str:
        """Stream tokens from Ollama and return the full assembled text."""
        payload["stream"] = True
        full_text = ""
        try:
            async with self.client.stream(
                "POST", OLLAMA_URL, json=payload, timeout=120.0
            ) as resp:
                if resp.status_code == 404:
                    raise OllamaServiceError(f"Model {MODEL_NAME} not found.")
                if resp.status_code != 200:
                    raise OllamaServiceError(
                        f"Ollama returned status {resp.status_code}."
                    )
                async for line in resp.aiter_lines():
                    if not line:
                        continue
                    try:
                        chunk = json.loads(line)
                        token = chunk.get("response", "")
                        full_text += token
                    except json.JSONDecodeError:
                        continue
        except httpx.ConnectError:
            raise OllamaServiceError("Ollama server is not running.")
        except httpx.TimeoutException:
            raise OllamaServiceError("Ollama request timed out.")
        except Exception as exc:
            logger.error("Ollama stream failed: %s", exc)
            raise OllamaServiceError("Failed to stream response from AI service.")
        return full_text.strip()

    async def chat(
        self,
        message: str,
        history: list[dict],
    ) -> str:
        """High-level chat helper that builds prompt and returns response."""
        return await self.generate(message, history, stream=False)


# Module-level singleton used by FastAPI routes
ollama_service = OllamaService()
