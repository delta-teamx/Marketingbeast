"""Deterministic mock provider for local dev and tests (no API key needed)."""

from __future__ import annotations

from typing import Any

from app.services.llm.base import LLMResult, Message


class MockLLMProvider:
    model = "mock-llm"

    def generate(
        self,
        system: str,
        messages: list[Message],
        tools: list[dict[str, Any]] | None = None,
    ) -> LLMResult:
        last = messages[-1].content if messages else ""
        return LLMResult(
            text=f"[mock] received {len(messages)} message(s); last: {last[:80]}",
            model=self.model,
            raw={"system": system, "tools": tools or []},
        )
