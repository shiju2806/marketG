"""Company autocomplete — real company/domain suggestions for onboarding.

Proxies Clearbit's keyless autocomplete so the frontend gets real options
("gm" -> General Motors/gm.com, GMC/gmc.com, GM Canada/gm.ca). Cached in-memory
to avoid hammering the upstream on every keystroke.
"""
from __future__ import annotations

import time

import httpx
from fastapi import APIRouter, Query

router = APIRouter(prefix="/api/v1", tags=["company"])

_cache: dict[str, tuple[float, list]] = {}
_TTL = 3600.0  # 1h


@router.get("/company-suggest")
async def company_suggest(query: str = Query(..., min_length=1)):
    q = query.strip().lower()
    if not q:
        return []
    now = time.time()
    hit = _cache.get(q)
    if hit and now - hit[0] < _TTL:
        return hit[1]

    results: list[dict] = []
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                "https://autocomplete.clearbit.com/v1/companies/suggest",
                params={"query": query}, timeout=8.0,
            )
            resp.raise_for_status()
            for d in resp.json():
                if d.get("domain"):
                    results.append({"name": d.get("name") or d["domain"], "domain": d["domain"]})
        results = results[:6]
    except Exception:  # noqa: BLE001 - lookup is best-effort; fall back to the typed guess
        results = []

    _cache[q] = (now, results)
    return results
