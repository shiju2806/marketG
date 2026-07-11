"""AI Visibility API (AVAS) — run the internal engine and read scores."""
from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query

from app.api.deps import require_account
from app.db import get_pool
from app.visibility.engine import run_visibility

router = APIRouter(prefix="/api/v1", tags=["visibility"])


@router.post("/visibility/run", status_code=201)
async def start_run(organization_id: UUID = Query(...), account_id: UUID = Depends(require_account)):
    pool = await get_pool()
    org = await pool.fetchrow(
        "select organization_id from organization where organization_id=$1 and account_id=$2",
        organization_id, account_id,
    )
    if org is None:
        raise HTTPException(status_code=404, detail="organization not found")
    return await run_visibility(pool, account_id, organization_id)


@router.get("/visibility-score")
async def latest_score(organization_id: UUID = Query(...), account_id: UUID = Depends(require_account)):
    pool = await get_pool()
    run = await pool.fetchrow(
        """
        select * from visibility_run
         where organization_id=$1 and account_id=$2
         order by created_at desc limit 1
        """,
        organization_id, account_id,
    )
    if run is None:
        raise HTTPException(status_code=404, detail="no visibility run yet — POST /visibility/run first")
    return dict(run)


@router.get("/visibility/runs/{run_id}")
async def run_detail(run_id: UUID, account_id: UUID = Depends(require_account)):
    pool = await get_pool()
    run = await pool.fetchrow(
        "select * from visibility_run where run_id=$1 and account_id=$2", run_id, account_id
    )
    if run is None:
        raise HTTPException(status_code=404, detail="run not found")
    questions = await pool.fetch(
        "select question, intent, retrieval, reasoning, trust, matched "
        "from visibility_question where run_id=$1 order by retrieval desc",
        run_id,
    )
    return {"run": dict(run), "questions": [dict(q) for q in questions]}
