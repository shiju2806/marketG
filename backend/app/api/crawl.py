"""Crawl API — enqueue a crawl job and check its status (async, ADR-007)."""
from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query

from app.api.deps import require_account
from app.db import get_pool
from app.jobs import queue
from app.models import CrawlRequest, CrawlStatus, JobRef

router = APIRouter(prefix="/api/v1", tags=["crawl"])


@router.get("/crawl-diagnosis")
async def crawl_diagnosis(organization_id: UUID = Query(...), account_id: UUID = Depends(require_account)):
    """What happened when AI tried to read the site (latest crawl) — the opening finding."""
    pool = await get_pool()
    row = await pool.fetchrow(
        """
        select crawl_status, crawl_diagnosis from source
         where organization_id=$1 and account_id=$2 and crawl_diagnosis is not null
         order by created_at desc limit 1
        """,
        organization_id, account_id,
    )
    if row is None:
        return {"status": None, "diagnosis": None}
    return {"status": row["crawl_status"], "diagnosis": row["crawl_diagnosis"]}


@router.post("/crawl", response_model=JobRef, status_code=202)
async def start_crawl(body: CrawlRequest, account_id: UUID = Depends(require_account)):
    pool = await get_pool()
    source = await pool.fetchrow(
        "select * from source where source_id=$1 and account_id=$2", body.source_id, account_id
    )
    if source is None:
        raise HTTPException(status_code=404, detail="source not found")

    job_id = await queue.enqueue(
        pool,
        account_id=account_id,
        job_type="crawl",
        organization_id=source["organization_id"],
        source_id=source["source_id"],
        payload={"seed_url": source["seed_url"]},
    )
    return {"job_id": job_id, "status": "queued"}


@router.get("/crawl/{job_id}", response_model=CrawlStatus)
async def crawl_status(job_id: UUID, account_id: UUID = Depends(require_account)):
    pool = await get_pool()
    job = await pool.fetchrow(
        "select * from job where job_id=$1 and account_id=$2", job_id, account_id
    )
    if job is None:
        raise HTTPException(status_code=404, detail="job not found")

    pages = await pool.fetchval(
        "select count(*) from document where source_id=$1 and account_id=$2",
        job["source_id"],
        account_id,
    )
    return {
        "job_id": job["job_id"],
        "status": job["status"],
        "stage": job["stage"],
        "attempts": job["attempts"],
        "pages_ingested": pages or 0,
        "error": job["error"],
        "metrics": dict(job["metrics"]) if job["metrics"] else {},
    }
