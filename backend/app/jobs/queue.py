"""Postgres-backed job queue (ADR-007).

Idempotent, resumable, and horizontally scalable: workers claim jobs with
FOR UPDATE SKIP LOCKED so many workers can run concurrently without stepping on
each other. This is the MVP stand-in for Kafka/Temporal (see DEFERRALS I-04/I-05)
— the interface stays the same when we split it out later.
"""
from __future__ import annotations

import json
from uuid import UUID

import asyncpg


async def enqueue(
    pool: asyncpg.Pool,
    *,
    account_id: UUID,
    job_type: str,
    organization_id: UUID | None = None,
    source_id: UUID | None = None,
    payload: dict | None = None,
) -> UUID:
    row = await pool.fetchrow(
        """
        insert into job (account_id, organization_id, source_id, type, payload)
        values ($1, $2, $3, $4, $5::jsonb)
        returning job_id
        """,
        account_id,
        organization_id,
        source_id,
        job_type,
        json.dumps(payload or {}),
    )
    return row["job_id"]


async def claim_next(pool: asyncpg.Pool, worker_id: str, types: list[str]) -> asyncpg.Record | None:
    """Atomically claim the oldest runnable job of the given types."""
    return await pool.fetchrow(
        """
        update job
           set status = 'running',
               attempts = attempts + 1,
               locked_at = now(),
               locked_by = $1
         where job_id = (
             select job_id from job
              where status = 'queued'
                and run_after <= now()
                and type = any($2::text[])
              order by created_at
              for update skip locked
              limit 1
         )
        returning *
        """,
        worker_id,
        types,
    )


async def complete(pool: asyncpg.Pool, job_id: UUID, metrics: dict | None = None) -> None:
    await pool.execute(
        "update job set status='done', stage='done', metrics=$2::jsonb, locked_by=null where job_id=$1",
        job_id,
        json.dumps(metrics or {}),
    )


async def fail(pool: asyncpg.Pool, record: asyncpg.Record, error: str) -> None:
    """Mark failed; requeue for retry if attempts remain (idempotent resume)."""
    requeue = record["attempts"] < record["max_attempts"]
    await pool.execute(
        """
        update job
           set status = $2,
               error = $3,
               locked_by = null,
               run_after = now() + interval '30 seconds'
         where job_id = $1
        """,
        record["job_id"],
        "queued" if requeue else "failed",
        error,
    )
