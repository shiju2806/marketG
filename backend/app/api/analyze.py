"""One-button onboarding: analyze a website end-to-end (AVAS §3 user workflow)."""
from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.api.deps import require_account
from app.db import get_pool
from app.jobs import queue

router = APIRouter(prefix="/api/v1", tags=["analyze"])


class AnalyzeRequest(BaseModel):
    name: str
    website: str
    vertical_pack_id: str = "automotive"


def _normalize(url: str) -> str:
    url = url.strip()
    if not url.startswith("http"):
        url = "https://" + url
    return url


@router.post("/analyze", status_code=202)
async def analyze(body: AnalyzeRequest, account_id: UUID = Depends(require_account)):
    pool = await get_pool()
    website = _normalize(body.website)

    # Reuse an existing org for this website, else create one.
    org = await pool.fetchrow(
        "select organization_id from organization where account_id=$1 and website=$2",
        account_id, website,
    )
    if org is None:
        org = await pool.fetchrow(
            """
            insert into organization (account_id, name, website, org_role, vertical_pack_id)
            values ($1,$2,$3,'owned_brand',$4) returning organization_id
            """,
            account_id, body.name.strip(), website, body.vertical_pack_id,
        )
    organization_id = org["organization_id"]

    source = await pool.fetchrow(
        "insert into source (account_id, organization_id, type, seed_url) "
        "values ($1,$2,'website',$3) returning source_id",
        account_id, organization_id, website,
    )
    job_id = await queue.enqueue(
        pool, account_id=account_id, job_type="analyze",
        organization_id=organization_id, source_id=source["source_id"],
    )
    return {"job_id": str(job_id), "organization_id": str(organization_id)}


@router.get("/analyze/{job_id}")
async def analyze_status(job_id: UUID, account_id: UUID = Depends(require_account)):
    pool = await get_pool()
    job = await pool.fetchrow(
        "select job_id, organization_id, status, stage, error from job "
        "where job_id=$1 and account_id=$2",
        job_id, account_id,
    )
    if job is None:
        raise HTTPException(status_code=404, detail="job not found")
    return dict(job)
