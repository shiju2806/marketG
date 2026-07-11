"""External AI Probe API (HRRE §13).

POST runs inline (a handful of external calls, ~10-20s) so the dashboard needs no
worker. GET returns the latest probe as a report: share-of-voice + per-question
answers.
"""
from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query

from app.api.deps import require_account
from app.db import get_pool
from app.probe.engine import run_probe

router = APIRouter(prefix="/api/v1", tags=["probe"])


@router.post("/probe", status_code=201)
async def start_probe(organization_id: UUID = Query(...), account_id: UUID = Depends(require_account)):
    pool = await get_pool()
    org = await pool.fetchrow(
        "select organization_id from organization where organization_id=$1 and account_id=$2",
        organization_id, account_id,
    )
    if org is None:
        raise HTTPException(status_code=404, detail="organization not found")
    return await run_probe(pool, account_id, organization_id)


@router.get("/probe/latest")
async def latest_probe(organization_id: UUID = Query(...), account_id: UUID = Depends(require_account)):
    pool = await get_pool()
    run = await pool.fetchrow(
        "select * from probe_run where organization_id=$1 and account_id=$2 and status='done' "
        "order by created_at desc limit 1",
        organization_id, account_id,
    )
    if run is None:
        return {"run": None, "share_of_voice": [], "questions": []}
    results = await pool.fetch(
        """
        select question, model, organization_mentioned, competitor_mentions,
               left(answer, 400) as answer
          from probe_result where probe_run_id=$1 order by question, model
        """,
        run["probe_run_id"],
    )
    return {
        "run": {
            "probe_run_id": str(run["probe_run_id"]),
            "citation": run["citation"],
            "targets": run["targets"],
            "created_at": run["created_at"].isoformat(),
        },
        "share_of_voice": (run["metrics"] or {}).get("share_of_voice", []),
        "questions": [dict(r) for r in results],
    }
