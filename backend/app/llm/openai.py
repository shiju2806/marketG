"""OpenAI embedding provider (real). Used when EMBEDDING_PROVIDER=openai."""
from __future__ import annotations

import httpx

from app.config import settings
from app.llm.base import TokenUsage

# text-embedding-3-small: ~$0.02 / 1M tokens.
_PRICE_PER_1M = 0.02


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
