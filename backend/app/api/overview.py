"""Overview API — the command-center landing bundle.

Returns everything the Overview page needs in ONE call (score, share/rank,
earned-owned, trend, crawl diagnosis, and counts), so the landing view doesn't
fan out a dozen requests. Read-only aggregate over existing data.
"""
from __future__ import annotations

from collections import Counter
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query

from app.api.deps import require_account
from app.db import get_pool
from app.recommend.delta import compute_delta

router = APIRouter(prefix="/api/v1", tags=["overview"])


@router.get("/overview")
async def overview(organization_id: UUID = Query(...), account_id: UUID = Depends(require_account)):
    pool = await get_pool()
    org = await pool.fetchrow(
        "select organization_id, name, website from organization where organization_id=$1 and account_id=$2",
        organization_id, account_id,
    )
    if org is None:
        raise HTTPException(status_code=404, detail="organization not found")

    score = await pool.fetchrow(
        "select retrieval, reasoning, trust, machine_readability, citation, overall "
        "from visibility_run where organization_id=$1 order by created_at desc limit 1",
        organization_id,
    )

    probe = await pool.fetchrow(
        "select metrics, earned_owned from probe_run where organization_id=$1 and status='done' "
        "order by created_at desc limit 1",
        organization_id,
    )
    sov = (probe["metrics"] or {}).get("share_of_voice", []) if probe else []
    you_idx = next((i for i, s in enumerate(sov) if s.get("is_you")), None)
    your_share = round(sov[you_idx]["share"] * 100) if you_idx is not None else None

    trend = await pool.fetch(
        "select created_at, citation, metrics from probe_run where organization_id=$1 and status='done' "
        "order by created_at asc limit 60",
        organization_id,
    )
    points = []
    for t in trend:
        tsov = (t["metrics"] or {}).get("share_of_voice", [])
        you = next((s for s in tsov if s.get("is_you")), None)
        points.append({"date": t["created_at"].isoformat(),
                       "citation": t["citation"],
                       "your_share": round(you["share"] * 100) if you else None,
                       "targets": []})

    src = await pool.fetchrow(
        "select crawl_diagnosis from source where organization_id=$1 and crawl_diagnosis is not null "
        "order by created_at desc limit 1",
        organization_id,
    )
    diag = src["crawl_diagnosis"] if src else None

    delta = await compute_delta(pool, organization_id)
    quad = Counter(c["quadrant"] for c in delta["categories"])
    open_recs = await pool.fetchval(
        "select count(*) from recommendation where organization_id=$1 and status='open'", organization_id
    )
    conflicts = await pool.fetchval(
        "select count(*) from conflict where organization_id=$1 and resolution_status='pending_review'",
        organization_id,
    )

    return {
        "organization": {"name": org["name"], "website": org["website"]},
        "score": dict(score) if score else None,
        "share_of_voice": sov[:8],
        "your_share": your_share,
        "rank": (you_idx + 1) if you_idx is not None else None,
        "brand_count": len(sov),
        "earned_owned": float(probe["earned_owned"]) if probe and probe["earned_owned"] is not None else None,
        "trend": points,
        "diagnosis": {"status": diag.get("status"), "headline": diag.get("headline")} if diag else None,
        "counts": {
            "gaps": quad.get("hidden", 0) + quad.get("missing", 0),
            "hidden": quad.get("hidden", 0),
            "missing": quad.get("missing", 0),
            "winning": quad.get("winning", 0),
            "recommendations": open_recs or 0,
            "conflicts": conflicts or 0,
        },
    }
