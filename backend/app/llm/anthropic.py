"""Anthropic (Claude) entity-extraction provider (real).

Used when LLM_PROVIDER=anthropic. The LLM *proposes* entities as structured JSON;
governance (Sprint 3) decides what enters the twin — "LLM proposes, twin decides"
(KIPS §25).
"""
from __future__ import annotations

import httpx

from app.config import settings
from app.llm.base import TokenUsage
from app.llm.util import parse_entities_json
from app.verticals.base import VerticalPack

# Claude Sonnet pricing (approx, per 1M tokens).
_IN_PER_1M = 3.0
_OUT_PER_1M = 15.0

_SYSTEM = (
    "You extract business entities from web page text. "
    "Return ONLY a JSON array of objects with keys: name, entity_type, confidence "
    "(0-1). Use the provided entity types. No prose."
)


class AnthropicLLMProvider:
    def __init__(self, model: str | None = None) -> None:
        self.model = model or settings.anthropic_model

    async def extract_entities(
        self, text: str, pack: VerticalPack
    ) -> tuple[list[ExtractedEntity], TokenUsage]:
        if not settings.anthropic_api_key:
            raise RuntimeError("ANTHROPIC_API_KEY not set")
        prompt = (
            f"{pack.extraction_hint}\n"
            f"Allowed entity_type values: {', '.join(pack.entity_types)}.\n\n"
            f"Page text:\n{text}"
        )
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                "https://api.anthropic.com/v1/messages",
                headers={
                    "x-api-key": settings.anthropic_api_key,
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json",
                },
                json={
                    "model": self.model,
                    "max_tokens": 1024,
                    "system": _SYSTEM,
                    "messages": [{"role": "user", "content": prompt}],
                },
                timeout=60.0,
            )
            resp.raise_for_status()
            data = resp.json()

        raw = "".join(block.get("text", "") for block in data.get("content", []))
        entities = parse_entities_json(raw)
        u = data.get("usage", {})
        cost = round(
            u.get("input_tokens", 0) / 1_000_000 * _IN_PER_1M
            + u.get("output_tokens", 0) / 1_000_000 * _OUT_PER_1M,
            6,
        )
        usage = TokenUsage(
            tokens=u.get("input_tokens", 0) + u.get("output_tokens", 0), cost_usd=cost
        )
        return entities, usage
