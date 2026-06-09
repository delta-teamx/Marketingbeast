"""Claude provider (stub).

Wired up in Phase 3. Kept minimal here so the interface is real but the
`anthropic` SDK is only imported when this provider is selected.
"""

from __future__ import annotations

from typing import Any

from app.core.config import get_settings
from app.services.llm.base import LLMResult, Message


class ClaudeProvider:
    def __init__(self) -> None:
        settings = get_settings()
        if not settings.anthropic_api_key:
            raise RuntimeError("ANTHROPIC_API_KEY is required for the anthropic provider")
        self.model = settings.llm_model
        self.temperature = settings.llm_temperature
        # SDK client construction is deferred to Phase 3.

    def generate(
        self,
        system: str,
        messages: list[Message],
        tools: list[dict[str, Any]] | None = None,
    ) -> LLMResult:
        raise NotImplementedError("ClaudeProvider is wired up in Phase 3")
