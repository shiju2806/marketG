"""Organizations API — brands under an account (ADR-001)."""
from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException

from app.api.deps import require_account
from app.db import get_pool
from app.models import Organization, OrganizationCreate

router = APIRouter(prefix="/api/v1", tags=["organizations"])


@router.post("/organizations", response_model=Organization, status_code=201)
async def create_organization(body: OrganizationCreate, account_id: UUID = Depends(require_account)):
    pool = await get_pool()
    row = await pool.fetchrow(
        """
        insert into organization
            (account_id, parent_organization_id, name, website, org_role, vertical_pack_id)
        values ($1, $2, $3, $4, $5, $6)
        returning *
        """,
        account_id,
        body.parent_organization_id,
        body.name,
        body.website,
        body.org_role,
        body.vertical_pack_id,
    )
    return dict(row)


@router.get("/organizations", response_model=list[Organization])
async def list_organizations(account_id: UUID = Depends(require_account)):
    pool = await get_pool()
    rows = await pool.fetch(
        "select * from organization where account_id = $1 order by created_at", account_id
    )
    return [dict(r) for r in rows]


@router.get("/organizations/{organization_id}", response_model=Organization)
async def get_organization(organization_id: UUID, account_id: UUID = Depends(require_account)):
    pool = await get_pool()
    row = await pool.fetchrow(
        "select * from organization where organization_id = $1 and account_id = $2",
        organization_id,
        account_id,
    )
    if row is None:
        raise HTTPException(status_code=404, detail="organization not found")
    return dict(row)
