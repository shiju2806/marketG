"""Recommendations API (AVAS §5)."""
from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query

from app.api.deps import require_account
from app.db import get_pool
from app.recommend.engine import generate_recommendations
from app.recommend.insight import competitive_summary

router = APIRouter(prefix="/api/v1", tags=["recommendations"])


@router.get("/competitive-summary")
async def get_competitive_summary(
    organization_id: UUID = Query(...), account_id: UUID = Depends(require_account)
):
    pool = await get_pool()
    org = await pool.fetchrow(
        "select organization_id from organization where organization_id=$1 and account_id=$2",
        organization_id, account_id,
    )
    if org is None:
        raise HTTPException(status_code=404, detail="organization not found")
    return await competitive_summary(pool, organization_id)


@router.post("/recommendations/generate", status_code=201)
async def generate(organization_id: UUID = Query(...), account_id: UUID = Depends(require_account)):
    pool = await get_pool()
    org = await pool.fetchrow(
        "select organization_id from organization where organization_id=$1 and account_id=$2",
        organization_id, account_id,
    )
    if org is None:
        raise HTTPException(status_code=404, detail="organization not found")
    recs = await generate_recommendations(pool, account_id, organization_id)
    return {"count": len(recs), "recommendations": recs}


@router.get("/recommendations")
async def list_recommendations(
    organization_id: UUID = Query(...), account_id: UUID = Depends(require_account)
):
    pool = await get_pool()
    rows = await pool.fetch(
        """
        select recommendation_id, title, missing_type, missing_detail, affects,
               expected_impact, status, created_at
          from recommendation
         where organization_id=$1 and account_id=$2 and status='open'
         order by array_position(array['high','medium','low'], expected_impact), created_at
        """,
        organization_id, account_id,
    )
    return [dict(r) for r in rows]
