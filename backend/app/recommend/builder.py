"""Recommendation builder (AVAS §5) — pure, unit-testable.

Turns structured gap signals into ranked, evidence-backed recommendations. Every
recommendation names the specific gap, the action, and which score(s) it lifts.
"""
from __future__ import annotations

_IMPACT_RANK = {"high": 0, "medium": 1, "low": 2}


def build_recommendations(
    *,
    blocked_bots: list[str],
    unstructured_page_share: float,
    citation_gaps: list[dict],       # [{"question":..., "competitors":[...]}]
    uncovered_vehicles: list[str],
    low_trust_entities: list[str],
) -> list[dict]:
    recs: list[dict] = []

    if blocked_bots:
        recs.append({
            "title": f"Unblock AI crawlers ({', '.join(blocked_bots)}) in robots.txt",
            "missing_type": "machine_readability",
            "missing_detail": "AI assistants can't read your site, so they answer from third parties.",
            "affects": ["retrieval", "trust", "machine_readability"],
            "expected_impact": "high",
            "source": {"blocked_bots": blocked_bots},
        })

    if unstructured_page_share >= 0.5:
        recs.append({
            "title": "Add schema.org structured data (Vehicle/Product) to key pages",
            "missing_type": "machine_readability",
            "missing_detail": f"{round(unstructured_page_share * 100)}% of pages lack structured markup.",
            "affects": ["retrieval", "machine_readability"],
            "expected_impact": "medium",
            "source": {"unstructured_page_share": round(unstructured_page_share, 2)},
        })

    for gap in citation_gaps:
        competitors = gap.get("competitors", [])
        comp_str = ", ".join(competitors) if competitors else "competitors"
        recs.append({
            "title": f"AI names {comp_str} but not you for “{gap['question']}”",
            "missing_type": "citation",
            "missing_detail": "Publish authoritative, evidence-backed content for this category.",
            "affects": ["citation"],
            "expected_impact": "high" if competitors else "medium",
            "source": gap,
        })

    for vehicle in uncovered_vehicles:
        recs.append({
            "title": f"Add detailed specs & capabilities content for the {vehicle}",
            "missing_type": "coverage",
            "missing_detail": "The twin has little connected knowledge for this model.",
            "affects": ["reasoning", "citation"],
            "expected_impact": "medium",
            "source": {"vehicle": vehicle},
        })

    for entity in low_trust_entities:
        recs.append({
            "title": f"Strengthen evidence for claims about {entity}",
            "missing_type": "trust",
            "missing_detail": "Claims are weakly supported; add authoritative first-party sources.",
            "affects": ["trust"],
            "expected_impact": "low",
            "source": {"entity": entity},
        })

    recs.sort(key=lambda r: _IMPACT_RANK.get(r["expected_impact"], 3))
    return recs
