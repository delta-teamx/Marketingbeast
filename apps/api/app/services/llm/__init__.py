"""LLM provider abstraction.

`get_llm_provider()` returns the configured provider. With the default
LLM_PROVIDER=auto it uses Claude whenever ANTHROPIC_API_KEY is set, and falls
back to the deterministic mock otherwise (so local dev and tests need no key).
"""

from __future__ import annotations

from app.core.config import get_settings
from app.services.llm.base import LLMProvider
from app.services.llm.mock import MockLLMProvider


def get_llm_provider() -> LLMProvider:
    settings = get_settings()
    provider = settings.llm_provider
    if provider == "auto":
        provider = "anthropic" if settings.anthropic_api_key else "mock"
    if provider == "anthropic":
        # Imported lazily so the `anthropic` SDK is only required when used.
        from app.services.llm.anthropic import ClaudeProvider

        return ClaudeProvider()
    return MockLLMProvider()


__all__ = ["LLMProvider", "MockLLMProvider", "get_llm_provider"]
