"""Claude provider — real Anthropic Messages API calls.

The `anthropic` SDK is imported lazily in `__init__` so it's only required when
this provider is actually selected (LLM_PROVIDER=anthropic, or =auto with a key).
"""

from __future__ import annotations

from typing import Any

from app.core.config import get_settings
from app.core.logging import get_logger
from app.services.llm.base import LLMResult, Message

logger = get_logger(__name__)


class ClaudeProvider:
    def __init__(self) -> None:
        settings = get_settings()
        if not settings.anthropic_api_key:
            raise RuntimeError("ANTHROPIC_API_KEY is required for the anthropic provider")

        # Imported here so the SDK is only a hard dependency when used.
        from anthropic import Anthropic

        self._client = Anthropic(api_key=settings.anthropic_api_key, timeout=60.0, max_retries=2)
        self.model = settings.llm_model
        self.temperature = settings.llm_temperature
        self.max_tokens = settings.llm_max_tokens

    def generate(
        self,
        system: str,
        messages: list[Message],
        tools: list[dict[str, Any]] | None = None,
    ) -> LLMResult:
        api_messages = [{"role": m.role, "content": m.content} for m in messages]
        kwargs: dict[str, Any] = {
            "model": self.model,
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
            "system": system,
            "messages": api_messages,
        }
        if tools:
            kwargs["tools"] = tools

        resp = self._client.messages.create(**kwargs)

        # Concatenate the text blocks of the response (ignore tool-use blocks).
        text = "".join(
            block.text for block in resp.content if getattr(block, "type", None) == "text"
        )
        return LLMResult(
            text=text,
            model=resp.model,
            raw={
                "id": resp.id,
                "stop_reason": resp.stop_reason,
                "usage": {
                    "input_tokens": resp.usage.input_tokens,
                    "output_tokens": resp.usage.output_tokens,
                },
            },
        )
