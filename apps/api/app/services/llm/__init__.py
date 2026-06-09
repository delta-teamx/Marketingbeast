"""LLM provider abstraction.

`get_llm_provider()` returns the configured provider (mock by default). Swap to
Claude by setting LLM_PROVIDER=anthropic and ANTHROPIC_API_KEY.
"""

from __future__ import annotations

from app.core.config import get_settings
from app.services.llm.base import LLMProvider
from app.services.llm.mock import MockLLMProvider


def get_llm_provider() -> LLMProvider:
    settings = get_settings()
    if settings.llm_provider == "anthropic":
        # Imported lazily so the `anthropic` SDK is only required when used.
        from app.services.llm.anthropic import ClaudeProvider

        return ClaudeProvider()
    return MockLLMProvider()


__all__ = ["LLMProvider", "MockLLMProvider", "get_llm_provider"]
