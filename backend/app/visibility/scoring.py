"""AI Visibility scoring — internal engine (AVAS §4, D-01 defaults).

Signals are normalized to [0,1]; scores are 0-100. Four internal dimensions here;
Citation is external (Sprint 4b). Overall is their mean. Pure helpers so the math
is unit-testable.
"""
from __future__ import annotations


def retrieval_signal(hits: list[dict]) -> float:
    """Best fused retrieval score for the question (can AI find relevant content?)."""
    return round(max((h["score"] for h in hits), default=0.0), 2)


def reasoning_signal(relationship_count: int, claim_count: int) -> float:
    """Can AI answer complex questions? Proxy: connected knowledge on the target."""
    return round(min(1.0, (relationship_count + claim_count) / 4.0), 2)


def trust_signal(avg_claim_confidence: float | None) -> float:
    """Is the answer backed by strong evidence? Proxy: mean claim confidence."""
    return round(avg_claim_confidence if avg_claim_confidence else 0.3, 2)


def machine_readability_signal(documents: list[dict]) -> float:
    """Can machines read the brand's own words? (ADR-004) crawlable + AI-open + structured."""
    if not documents:
        return 0.0
    total = 0.0
    for d in documents:
        crawlable = 1.0 if d.get("http_status") == 200 else 0.0
        bots = (d.get("ai_crawler_policy") or {}).get("bots", {})
        ai_open = 1.0 if bots.get("GPTBot") == "allowed" else 0.0
        structured = 1.0 if d.get("has_schema_org") else 0.0
        total += 0.4 * crawlable + 0.4 * ai_open + 0.2 * structured
    return round(total / len(documents), 2)


def to_score(signal: float) -> int:
    return int(round(max(0.0, min(1.0, signal)) * 100))


def overall(retrieval: float, reasoning: float, trust: float, machine_readability: float) -> int:
    return to_score((retrieval + reasoning + trust + machine_readability) / 4.0)
