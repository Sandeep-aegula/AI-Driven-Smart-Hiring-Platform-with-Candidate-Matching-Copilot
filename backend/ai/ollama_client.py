from __future__ import annotations

import json
import logging
from typing import Any

import httpx

from backend.core.config import settings

logger = logging.getLogger(__name__)


class OllamaClient:
    def __init__(self, base_url: str | None = None, model: str | None = None) -> None:
        self.base_url = (base_url or settings.ollama_base_url).rstrip("/")
        self.model = model or settings.ollama_model

    def generate(self, prompt: str, system: str | None = None, format_json: bool = False) -> str:
        payload: dict[str, Any] = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {"temperature": 0.2},
        }
        if system:
            payload["system"] = system
        if format_json:
            payload["format"] = "json"

        try:
            with httpx.Client(timeout=90.0) as client:
                response = client.post(f"{self.base_url}/api/generate", json=payload)
                response.raise_for_status()
                return response.json().get("response", "")
        except Exception as exc:  # pragma: no cover
            logger.exception("Ollama request failed")
            raise RuntimeError(f"Ollama request failed: {exc}") from exc

    @staticmethod
    def parse_json_response(response_text: str) -> dict[str, Any]:
        try:
            return json.loads(response_text)
        except json.JSONDecodeError:
            start = response_text.find("{")
            end = response_text.rfind("}")
            if start >= 0 and end > start:
                return json.loads(response_text[start : end + 1])
            raise
