"""Sources API — knowledge sources for an organization (MVP: website)."""
from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException

from app.api.deps import require_account
from app.db import get_pool
from app.models import Source, SourceCreate

router = APIRouter(prefix="/api/v1", tags=["sources"])


@router.post("/sources", response_model=Source, status_code=201)
async def create_source(body: SourceCreate, account_id: UUID = Depends(require_account)):
    pool = await get_pool()

    # Ownership check: the org must belong to the caller's account.
    org = await pool.fetchrow(
        "select organization_id, org_role from organization where organization_id=$1 and account_id=$2",
        body.organization_id,
        account_id,
    )
    if org is None:
        raise HTTPException(status_code=404, detail="organization not found")
    if org["org_role"] != "owned_brand":
        # ADR-003: we only crawl authorized owned brands, never competitors.
        raise HTTPException(status_code=422, detail="can only add sources to owned_brand organizations")

    row = await pool.fetchrow(
        """
        insert into source (account_id, organization_id, type, seed_url)
        values ($1, $2, $3, $4)
        returning *
        """,
        account_id,
        body.organization_id,
        body.type,
        body.seed_url,
    )
    return dict(row)


@router.get("/sources/{source_id}", response_model=Source)
async def get_source(source_id: UUID, account_id: UUID = Depends(require_account)):
    pool = await get_pool()
    row = await pool.fetchrow(
        "select * from source where source_id=$1 and account_id=$2", source_id, account_id
    )
    if row is None:
        raise HTTPException(status_code=404, detail="source not found")
    return dict(row)
