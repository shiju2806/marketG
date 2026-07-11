"""OpenAI providers (real): embeddings and entity extraction.

Set EMBEDDING_PROVIDER=openai and/or LLM_PROVIDER=openai — a single OPENAI_API_KEY
powers both.
"""
from __future__ import annotations

import httpx

from app.config import settings
from app.llm.base import TokenUsage
from app.llm.util import parse_entities_json
from app.verticals.base import VerticalPack

# text-embedding-3-small: ~$0.02 / 1M tokens.
_PRICE_PER_1M = 0.02
# gpt-4o-mini (default): ~$0.15 in / $0.60 out per 1M tokens.
_LLM_IN_PER_1M = 0.15
_LLM_OUT_PER_1M = 0.60

_SYSTEM = (
    "You extract business entities from web page text. Respond with a JSON object "
    '{"entities": [{"name": ..., "entity_type": ..., "confidence": 0-1}]}. '
    "Use only the provided entity types. No prose."
)


class OpenAIEmbeddingProvider:
    def __init__(self, model: str | None = None, dim: int = 1536) -> None:
        self.model = model or settings.openai_embed_model
        self.dim = dim

    async def embed(self, texts: list[str]) -> tuple[list[list[float]], TokenUsage]:
        if not settings.openai_api_key:
            raise RuntimeError("OPENAI_API_KEY not set")
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                "https://api.openai.com/v1/embeddings",
                headers={"Authorization": f"Bearer {settings.openai_api_key}"},
                json={"model": self.model, "input": texts, "dimensions": self.dim},
                timeout=60.0,
            )
            resp.raise_for_status()
            data = resp.json()
        vectors = [item["embedding"] for item in data["data"]]
        tokens = data.get("usage", {}).get("total_tokens", 0)
        usage = TokenUsage(tokens=tokens, cost_usd=round(tokens / 1_000_000 * _PRICE_PER_1M, 6))
        return vectors, usage


class OpenAILLMProvider:
    """Entity extraction via OpenAI chat completions (JSON mode)."""

    def __init__(self, model: str | None = None) -> None:
        self.model = model or settings.openai_llm_model

    async def extract_entities(self, text: str, pack: VerticalPack):
        if not settings.openai_api_key:
            raise RuntimeError("OPENAI_API_KEY not set")
        prompt = (
            f"{pack.extraction_hint}\n"
            f"Allowed entity_type values: {', '.join(pack.entity_types)}.\n\n"
            f"Page text:\n{text}"
        )
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                "https://api.openai.com/v1/chat/completions",
                headers={"Authorization": f"Bearer {settings.openai_api_key}"},
                json={
                    "model": self.model,
                    "response_format": {"type": "json_object"},
                    "messages": [
                        {"role": "system", "content": _SYSTEM},
                        {"role": "user", "content": prompt},
                    ],
                },
                timeout=60.0,
            )
            resp.raise_for_status()
            data = resp.json()

        raw = data["choices"][0]["message"]["content"]
        entities = parse_entities_json(raw)
        u = data.get("usage", {})
        cost = round(
            u.get("prompt_tokens", 0) / 1_000_000 * _LLM_IN_PER_1M
            + u.get("completion_tokens", 0) / 1_000_000 * _LLM_OUT_PER_1M,
            6,
        )
        usage = TokenUsage(tokens=u.get("total_tokens", 0), cost_usd=cost)
        return entities, usage
