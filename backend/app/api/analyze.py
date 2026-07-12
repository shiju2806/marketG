"""One-button onboarding: analyze a website end-to-end (AVAS §3 user workflow).

Runs the full pipeline as an in-process background task on the API server itself —
the SAME process (and therefore the same code) that serves every other endpoint.
This deliberately avoids a separate worker, which could run stale code and silently
produce wrong results. The job row tracks status/stage for the frontend to poll.
"""
from __future__ import annotations

import asyncio
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.api.deps import require_account
from app.db import get_pool
from app.pipeline.full import run_full_analysis

router = APIRouter(prefix="/api/v1", tags=["analyze"])

# Keep strong refs so fire-and-forget tasks aren't garbage-collected.
_running: set[asyncio.Task] = set()


class AnalyzeRequest(BaseModel):
    name: str
    website: str
    vertical_pack_id: str = "automotive"


def _normalize(url: str) -> str:
    url = url.strip()
    if not url.startswith("http"):
        url = "https://" + url
    return url


async def _run_in_background(account_id, source: dict, job_id) -> None:
    pool = await get_pool()
    try:
        await run_full_analysis(pool, job_id, account_id, source)
        await pool.execute("update job set status='done', stage='done' where job_id=$1", job_id)
    except Exception as exc:  # noqa: BLE001 - record failure for the poller
        await pool.execute(
            "update job set status='failed', error=$2 where job_id=$1", job_id, str(exc)[:500]
        )


@router.post("/analyze", status_code=202)
async def analyze(body: AnalyzeRequest, account_id: UUID = Depends(require_account)):
    pool = await get_pool()
    website = _normalize(body.website)

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
        "values ($1,$2,'website',$3) returning *",
        account_id, organization_id, website,
    )

    # Create the job as 'running' so a (now-optional) worker never also claims it.
    job_id = await pool.fetchval(
        """
        insert into job (account_id, organization_id, source_id, type, status, stage)
        values ($1,$2,$3,'analyze','running','queued') returning job_id
        """,
        account_id, organization_id, source["source_id"],
    )

    task = asyncio.create_task(_run_in_background(account_id, dict(source), job_id))
    _running.add(task)
    task.add_done_callback(_running.discard)

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
