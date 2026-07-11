"""Probe answer analysis (HRRE §13.3) — pure, unit-testable.

Given a real AI answer, decide: did it mention the org? cite it (first-party)?
which competitors did it name? and classify cited sources as owned vs earned.

Mention/competitor detection is deterministic string matching (cheap, robust).
claim_consistency is left 'unknown' for MVP (an LLM classifier is deferred, D-02).
"""
from __future__ import annotations

from urllib.parse import urlparse


def _domain(url_or_host: str) -> str:
    host = urlparse(url_or_host if "//" in url_or_host else f"//{url_or_host}").netloc or url_or_host
    return host.lower().lstrip("www.").strip("/")


def _mentions(text: str, name: str) -> bool:
    return name.strip().lower() in text.lower()


def analyze_answer(
    answer: str,
    cited_sources: list[str],
    *,
    org_names: list[str],
    competitor_names: list[str],
    org_website: str | None,
) -> dict:
    text = answer or ""
    org_mentioned = any(_mentions(text, n) for n in org_names if n)

    competitor_mentions = sorted({c for c in competitor_names if c and _mentions(text, c)})

    org_domain = _domain(org_website) if org_website else None
    first_party, third_party = 0, 0
    for src in cited_sources:
        d = _domain(src)
        if org_domain and (d == org_domain or d.endswith("." + org_domain)):
            first_party += 1
        else:
            third_party += 1

    return {
        "organization_mentioned": org_mentioned,
        "organization_cited": first_party > 0,
        "competitor_mentions": competitor_mentions,
        "first_party": first_party,
        "third_party": third_party,
        "claim_consistency": "unknown",
    }
