"""External AI Probe target seam (HRRE §13, TECH_STACK ProbeTarget).

Each target asks a real assistant a buyer question and returns its answer plus any
sources it cited. Non-browsing chat models return no citations; Perplexity returns
real ones.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol


@dataclass
class ProbeAnswer:
    text: str
    cited_sources: list[str] = field(default_factory=list)
    tokens: int = 0
    cost_usd: float = 0.0
    latency_ms: int = 0


class ProbeTarget(Protocol):
    name: str

    async def ask(self, question: str) -> ProbeAnswer:
        ...
