"""Remediation API — generate and fetch the ready-to-use fix for a gap."""
from __future__ import annotations

import json
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query

from app.api.deps import require_account
from app.db import get_pool
from app.remediate.generator import generate_fix

router = APIRouter(prefix="/api/v1", tags=["remediate"])


@router.post("/remediate", status_code=201)
async def remediate(recommendation_id: UUID = Query(...), account_id: UUID = Depends(require_account)):
    pool = await get_pool()
    rec = await pool.fetchrow(
        "select * from recommendation where recommendation_id=$1 and account_id=$2",
        recommendation_id, account_id,
    )
    if rec is None:
        raise HTTPException(status_code=404, detail="recommendation not found")

    artifact = await generate_fix(pool, rec["organization_id"], dict(rec))

    row = await pool.fetchrow(
        """
        insert into remediation (account_id, organization_id, recommendation_id, gap_type, title, artifact)
        values ($1,$2,$3,$4,$5,$6::jsonb)
        returning remediation_id, created_at
        """,
        account_id, rec["organization_id"], recommendation_id,
        artifact["gap_type"], artifact["title"], json.dumps(artifact),
    )
    return {"remediation_id": str(row["remediation_id"]), "artifact": artifact}


@router.get("/remediation")
async def list_remediation(organization_id: UUID = Query(...), account_id: UUID = Depends(require_account)):
    pool = await get_pool()
    rows = await pool.fetch(
        "select remediation_id, recommendation_id, gap_type, title, artifact, status, created_at "
        "from remediation where organization_id=$1 and account_id=$2 order by created_at desc",
        organization_id, account_id,
    )
    return [dict(r) for r in rows]


@router.get("/remediation/{remediation_id}")
async def get_remediation(remediation_id: UUID, account_id: UUID = Depends(require_account)):
    pool = await get_pool()
    row = await pool.fetchrow(
        "select * from remediation where remediation_id=$1 and account_id=$2",
        remediation_id, account_id,
    )
    if row is None:
        raise HTTPException(status_code=404, detail="remediation not found")
    return dict(row)
