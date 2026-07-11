"""Provider seams (TECH_STACK): embeddings + entity extraction.

Both return a TokenUsage so every stage can log tokens/cost (D-05). Concrete
implementations: mock (default, keyless), openai, anthropic.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol

from app.verticals.base import VerticalPack


@dataclass
class TokenUsage:
    tokens: int = 0
    cost_usd: float = 0.0

    def __add__(self, other: "TokenUsage") -> "TokenUsage":
        return TokenUsage(self.tokens + other.tokens, round(self.cost_usd + other.cost_usd, 6))


@dataclass
class ExtractedEntity:
    name: str
    entity_type: str
    confidence: float = 0.6
    attributes: dict = field(default_factory=dict)


class EmbeddingProvider(Protocol):
    dim: int

    async def embed(self, texts: list[str]) -> tuple[list[list[float]], TokenUsage]:
        ...


class LLMProvider(Protocol):
    async def extract_entities(
        self, text: str, pack: VerticalPack
    ) -> tuple[list[ExtractedEntity], TokenUsage]:
        ...
