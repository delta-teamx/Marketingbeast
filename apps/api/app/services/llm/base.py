"""The LLMProvider interface. All content/audit/reply generation goes through this."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol, runtime_checkable


@dataclass
class Message:
    role: str  # "user" | "assistant"
    content: str


@dataclass
class LLMResult:
    text: str
    model: str
    raw: dict[str, Any] = field(default_factory=dict)


@runtime_checkable
class LLMProvider(Protocol):
    """Abstraction over an LLM. Implementations: MockLLMProvider, ClaudeProvider."""

    def generate(
        self,
        system: str,
        messages: list[Message],
        tools: list[dict[str, Any]] | None = None,
    ) -> LLMResult:
        ...

    async def agenerate(
        self,
        system: str,
        messages: list[Message],
        tools: list[dict[str, Any]] | None = None,
    ) -> LLMResult:
        """Non-blocking variant — used inside async request handlers so a real
        provider's network round-trip never blocks the event loop."""
        ...
