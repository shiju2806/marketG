"""Keyless, deterministic providers for local dev + tests.

Not a toy that returns garbage — a *deterministic* stand-in so the full pipeline
(chunk -> embed -> extract -> persist) can be exercised and asserted without API
keys or internet (the sandbox has neither). Real providers live alongside and
swap in via config.
"""
from __future__ import annotations

import hashlib
import math
import re

from app.llm.base import (
    ExtractedClaim,
    ExtractedEntity,
    ExtractedRelationship,
    KnowledgeExtraction,
    TokenUsage,
)
from app.verticals.base import VerticalPack

_SPEC = re.compile(r"(\d[\d,\.]*)\s*(miles|mph|mpg|hp|horsepower|lbs|kwh|inches|seconds)", re.I)
_PRICE = re.compile(r"\$[\d,]+(?:\.\d+)?")
_REL_PREDICATE = {
    "Technology": "uses",
    "Integration": "integrates_with",
    "Regulation": "complies_with",
    "Competitor": "competes_with",
    "Feature": "has_feature",
    "Award": "won",
}

_TOKEN = re.compile(r"[A-Za-z0-9][A-Za-z0-9\-/.]+")
# Multi-word Proper Noun sequences, e.g. "Super Cruise", "Land Cruiser".
_PROPER = re.compile(r"\b([A-Z][a-zA-Z0-9]+(?:\s+[A-Z][a-zA-Z0-9]+){0,3})\b")


def _est_tokens(text: str) -> int:
    return max(1, len(text) // 4)


class MockEmbeddingProvider:
    """Hashing embedding: deterministic, normalized, dimension-configurable.

    Same text -> same vector; different text -> different vector. Enough for the
    pipeline and index to work end-to-end; not semantically meaningful.
    """

    def __init__(self, dim: int = 1536) -> None:
        self.dim = dim

    async def embed(self, texts: list[str]) -> tuple[list[list[float]], TokenUsage]:
        vectors: list[list[float]] = []
        usage = TokenUsage()
        for text in texts:
            usage.tokens += _est_tokens(text)
            vectors.append(self._vector(text))
        return vectors, usage

    def _vector(self, text: str) -> list[float]:
        vec = [0.0] * self.dim
        for token in _TOKEN.findall(text.lower()):
            h = int.from_bytes(hashlib.blake2b(token.encode(), digest_size=8).digest(), "big")
            vec[h % self.dim] += 1.0
        norm = math.sqrt(sum(v * v for v in vec)) or 1.0
        return [round(v / norm, 6) for v in vec]


class MockLLMProvider:
    """Heuristic entity extraction driven by the vertical pack's ontology seed
    plus a proper-noun fallback. Deterministic."""

    async def extract_entities(
        self, text: str, pack: VerticalPack
    ) -> tuple[list[ExtractedEntity], TokenUsage]:
        found: dict[str, ExtractedEntity] = {}
        lowered = text.lower()

        # High-confidence: seeded ontology terms.
        for term, (etype, canonical) in pack.ontology_seed.items():
            if term in lowered:
                found[canonical.lower()] = ExtractedEntity(canonical, etype, confidence=0.9)

        # Lower-confidence: multi-word proper nouns as candidate Vehicles/Features.
        default_type = "Vehicle" if "Vehicle" in pack.entity_types else "Entity"
        for match in _PROPER.findall(text):
            key = match.lower()
            if key in found or len(match) < 4 or match.isupper():
                continue
            if any(w in key for w in ("home", "menu", "cookie", "privacy")):
                continue
            found[key] = ExtractedEntity(match.strip(), default_type, confidence=0.5)

        usage = TokenUsage(tokens=_est_tokens(text))
        return list(found.values()), usage

    async def extract_knowledge(
        self, text: str, pack: VerticalPack
    ) -> tuple[KnowledgeExtraction, TokenUsage]:
        entities, usage = await self.extract_entities(text, pack)

        # Subject for relationships/claims: prefer a Vehicle, else generic "product".
        vehicle = next((e for e in entities if e.entity_type == "Vehicle"), None)
        subject = vehicle.name if vehicle else "product"

        relationships: list[ExtractedRelationship] = []
        if vehicle:
            for ent in entities:
                pred = _REL_PREDICATE.get(ent.entity_type)
                if pred and ent.name != vehicle.name:
                    relationships.append(
                        ExtractedRelationship(vehicle.name, pred, ent.name, confidence=0.6)
                    )

        claims: list[ExtractedClaim] = []
        for num, unit in _SPEC.findall(text):
            claims.append(
                ExtractedClaim(subject, f"spec_{unit.lower()}", value=f"{num} {unit}",
                               claim_type="spec", confidence=0.7)
            )
        for price in _PRICE.findall(text):
            claims.append(
                ExtractedClaim(subject, "price", value=price, claim_type="pricing", confidence=0.7)
            )

        return KnowledgeExtraction(entities, relationships, claims), usage
