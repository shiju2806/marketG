"""Anthropic (Claude) entity-extraction provider (real).

Used when LLM_PROVIDER=anthropic. The LLM *proposes* entities as structured JSON;
governance (Sprint 3) decides what enters the twin — "LLM proposes, twin decides"
(KIPS §25).
"""
from __future__ import annotations

import httpx

from app.config import settings
from app.llm.base import TokenUsage
from app.llm.util import (
    parse_brands_json,
    parse_entities_json,
    parse_knowledge_json,
    parse_questions_json,
)
from app.verticals.base import VerticalPack

_BRANDS_SYSTEM = (
    "List the vehicle MANUFACTURER BRANDS mentioned — parent marque only. Map every "
    "model/trim to its manufacturer ('Silverado'->'Chevrolet', 'F-150 Raptor'->'Ford', "
    "'Tacoma'->'Toyota'). EXCLUDE model names, trims, components, features, "
    "publications, websites. Normalize variants ('Chevy'->'Chevrolet', 'RAM'->'Ram', "
    "'Mercedes'->'Mercedes-Benz'). Return ONLY JSON {\"brands\": [\"...\"]}, unique "
    "manufacturer brands. No prose."
)

_QUESTIONS_SYSTEM = (
    "Generate the category buyer questions a shopper asks an AI assistant when "
    "researching this company's MARKET. Questions must ELICIT SPECIFIC PRODUCT/BRAND "
    "RECOMMENDATIONS ('what is the best…', 'which… should I buy', 'top… for…'). Never "
    'name the specific company/products. Return ONLY JSON {"questions": ["..."]}. No prose.'
)

# Claude Sonnet pricing (approx, per 1M tokens).
_IN_PER_1M = 3.0
_OUT_PER_1M = 15.0

_SYSTEM = (
    "You extract business entities from web page text. "
    "Return ONLY a JSON array of objects with keys: name, entity_type, confidence "
    "(0-1). Use the provided entity types. No prose."
)

_KNOWLEDGE_SYSTEM = (
    "You extract structured business knowledge. Return ONLY a JSON object with arrays "
    '"entities" [{name,entity_type,confidence}], "relationships" '
    "[{subject,predicate,object,confidence}], and \"claims\" "
    "[{subject,predicate,object,value,claim_type,confidence}]. subject/object in "
    "relationships are entity names. claim_type one of: spec, performance, compliance, "
    "capability, comparison, award, safety, pricing. confidence 0-1. No prose."
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
        return parse_entities_json(raw), self._usage(data)

    async def extract_knowledge(self, text: str, pack: VerticalPack):
        if not settings.anthropic_api_key:
            raise RuntimeError("ANTHROPIC_API_KEY not set")
        prompt = (
            f"{pack.extraction_hint}\n"
            f"Allowed entity_type values: {', '.join(pack.entity_types)}.\n\n"
            f"Page text:\n{text}"
        )
        data = await self._message(_KNOWLEDGE_SYSTEM, prompt)
        raw = "".join(block.get("text", "") for block in data.get("content", []))
        return parse_knowledge_json(raw), self._usage(data)

    async def extract_brands(self, text: str) -> tuple[list[str], TokenUsage]:
        if not settings.anthropic_api_key:
            raise RuntimeError("ANTHROPIC_API_KEY not set")
        data = await self._message(_BRANDS_SYSTEM, text)
        raw = "".join(b.get("text", "") for b in data.get("content", []))
        return parse_brands_json(raw), self._usage(data)

    async def generate_category_questions(self, context: str, n: int) -> tuple[list[str], TokenUsage]:
        if not settings.anthropic_api_key:
            raise RuntimeError("ANTHROPIC_API_KEY not set")
        data = await self._message(_QUESTIONS_SYSTEM, f"Generate {n} questions.\n\n{context}")
        raw = "".join(b.get("text", "") for b in data.get("content", []))
        return parse_questions_json(raw), self._usage(data)

    async def _message(self, system: str, prompt: str) -> dict:
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
                    "max_tokens": 1500,
                    "system": system,
                    "messages": [{"role": "user", "content": prompt}],
                },
                timeout=90.0,
            )
            resp.raise_for_status()
            return resp.json()

    @staticmethod
    def _usage(data: dict) -> TokenUsage:
        u = data.get("usage", {})
        cost = round(
            u.get("input_tokens", 0) / 1_000_000 * _IN_PER_1M
            + u.get("output_tokens", 0) / 1_000_000 * _OUT_PER_1M,
            6,
        )
        return TokenUsage(tokens=u.get("input_tokens", 0) + u.get("output_tokens", 0), cost_usd=cost)
