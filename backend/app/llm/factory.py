"""Provider factory — pick embedding + LLM providers from config.

Defaults to the keyless mock so local dev runs without credentials. Swap to real
providers by setting EMBEDDING_PROVIDER / LLM_PROVIDER (+ keys) in .env.
"""
from __future__ import annotations

from app.config import settings
from app.llm.base import EmbeddingProvider, LLMProvider
from app.llm.mock import MockEmbeddingProvider, MockLLMProvider


def get_embedding_provider() -> EmbeddingProvider:
    if settings.embedding_provider == "openai":
        from app.llm.openai import OpenAIEmbeddingProvider

        return OpenAIEmbeddingProvider(dim=settings.embed_dim)
    return MockEmbeddingProvider(dim=settings.embed_dim)


def get_llm_provider() -> LLMProvider:
    if settings.llm_provider == "anthropic":
        from app.llm.anthropic import AnthropicLLMProvider

        return AnthropicLLMProvider()
    return MockLLMProvider()
