"""External AI Probe API (HRRE §13). Async — external calls are slow + metered."""
from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query

from app.api.deps import require_account
from app.db import get_pool
from app.jobs import queue

router = APIRouter(prefix="/api/v1", tags=["probe"])


@router.post("/probe", status_code=202)
async def start_probe(organization_id: UUID = Query(...), account_id: UUID = Depends(require_account)):
    pool = await get_pool()
    org = await pool.fetchrow(
        "select organization_id from organization where organization_id=$1 and account_id=$2",
        organization_id, account_id,
    )
    if org is None:
        raise HTTPException(status_code=404, detail="organization not found")
    job_id = await queue.enqueue(
        pool, account_id=account_id, job_type="probe", organization_id=organization_id
    )
    return {"job_id": job_id, "status": "queued"}


@router.get("/probe/{probe_run_id}")
async def probe_results(probe_run_id: UUID, account_id: UUID = Depends(require_account)):
    pool = await get_pool()
    run = await pool.fetchrow(
        "select * from probe_run where probe_run_id=$1 and account_id=$2", probe_run_id, account_id
    )
    if run is None:
        raise HTTPException(status_code=404, detail="probe run not found")
    results = await pool.fetch(
        """
        select question, model, organization_mentioned, organization_cited, competitor_mentions,
               first_party, third_party, left(answer, 300) as answer_preview
          from probe_result where probe_run_id=$1 order by question, model
        """,
        probe_run_id,
    )
    return {"run": dict(run), "results": [dict(r) for r in results]}
