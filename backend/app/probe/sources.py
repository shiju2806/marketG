"""Citation-source analysis — 'who AI trusts instead of you'.

Aggregates the URLs browsing assistants actually cited across the probe, ranks the
domains, and flags whether the org's own site appears. This is the concrete GEO
insight: to get recommended, your content has to be in the sources AI draws from.
"""
from __future__ import annotations

from collections import Counter
from urllib.parse import urlparse


def domain_of(url: str) -> str:
    host = urlparse(url if "//" in url else f"//{url}").netloc or ""
    return host.lower().removeprefix("www.")


async def cited_sources(pool, organization_id) -> dict:
    org = await pool.fetchrow(
        "select name, website from organization where organization_id=$1", organization_id
    )
    your_domain = domain_of(org["website"]) if org and org["website"] else None

    run = await pool.fetchrow(
        "select probe_run_id from probe_run where organization_id=$1 and status='done' "
        "order by created_at desc limit 1",
        organization_id,
    )
    if run is None:
        return {"your_domain": your_domain, "your_domain_cited": False, "total_citations": 0, "sources": []}

    rows = await pool.fetch(
        "select cited_sources from probe_result where probe_run_id=$1", run["probe_run_id"]
    )

    counts: Counter[str] = Counter()
    total = 0
    for r in rows:
        for url in (r["cited_sources"] or []):
            d = domain_of(url)
            if not d:
                continue
            counts[d] += 1
            total += 1

    def is_first_party(d: str) -> bool:
        return bool(your_domain) and (d == your_domain or d.endswith("." + your_domain))

    sources = [
        {
            "domain": d,
            "count": c,
            "share": round(c / total, 3) if total else 0.0,
            "is_first_party": is_first_party(d),
        }
        for d, c in counts.most_common(15)
    ]
    your_cited = any(is_first_party(d) for d in counts)

    return {
        "your_domain": your_domain,
        "your_domain_cited": your_cited,
        "total_citations": total,
        "sources": sources,
    }
