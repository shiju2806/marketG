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

from app.llm.base import EmbeddingProvider, ExtractedEntity, LLMProvider, TokenUsage
from app.verticals.base import VerticalPack

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
