"""Background worker: claims jobs and runs the crawl handler.

Run with:  python -m app.jobs.worker
Stateless and idempotent — run as many as you like (ADR-007).
"""
from __future__ import annotations

import asyncio

import asyncpg

from app.config import settings
from app.crawler.crawler import crawl_site
from app.crawler.classifier import classify_page
from app.crawler.machine_readability import fetch_ai_crawler_policy
from app.db import close_pool, get_pool
from app.jobs import queue
from app.pipeline.extract import process_document
from app.storage import ensure_bucket, raw_key, upload_raw

import httpx


async def handle_crawl(pool: asyncpg.Pool, job: asyncpg.Record) -> dict:
    """Crawl a source's site, persist raw docs + machine-readability signals."""
    source = await pool.fetchrow("select * from source where source_id = $1", job["source_id"])
    if source is None:
        raise ValueError(f"source {job['source_id']} not found")

    await pool.execute("update source set status='crawling' where source_id=$1", source["source_id"])

    # Site-level AI-crawler policy (robots.txt) — the headline machine-readability signal.
    async with httpx.AsyncClient(follow_redirects=True) as client:
        ai_policy = await fetch_ai_crawler_policy(source["seed_url"], client)

    pages = await crawl_site(
        source["seed_url"],
        max_pages=settings.crawl_max_pages,
        max_depth=settings.crawl_max_depth,
        timeout_ms=settings.crawl_timeout_ms,
    )

    ingested = 0
    document_ids: list = []
    for page in pages:
        if not page.html:  # errored page — skip persistence, still counted in metrics
            continue
        key = raw_key(str(source["account_id"]), str(source["source_id"]), page.content_hash)
        await upload_raw(key, page.html)
        document_id = await pool.fetchval(
            """
            insert into document (
                account_id, organization_id, source_id, url, page_classification,
                object_storage_key, content_hash, http_status, js_required,
                has_schema_org, ai_crawler_policy
            )
            values ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11::jsonb)
            on conflict (source_id, url) do update set
                page_classification = excluded.page_classification,
                object_storage_key  = excluded.object_storage_key,
                content_hash        = excluded.content_hash,
                http_status         = excluded.http_status,
                js_required         = excluded.js_required,
                has_schema_org      = excluded.has_schema_org,
                ai_crawler_policy   = excluded.ai_crawler_policy,
                crawled_at          = now()
            returning document_id
            """,
            source["account_id"],
            source["organization_id"],
            source["source_id"],
            page.url,
            classify_page(page.url, page.text),
            key,
            page.content_hash,
            page.http_status,
            page.js_required,
            page.has_schema_org,
            ai_policy,
        )
        document_ids.append(document_id)
        ingested += 1

    # Fan out one extract job per document (ADR-007: independent, scalable units).
    for document_id in document_ids:
        await queue.enqueue(
            pool,
            account_id=source["account_id"],
            job_type="extract",
            organization_id=source["organization_id"],
            source_id=source["source_id"],
            payload={"document_id": str(document_id)},
        )

    await pool.execute("update source set status='done' where source_id=$1", source["source_id"])
    return {
        "pages_seen": len(pages),
        "pages_ingested": ingested,
        "extract_jobs": len(document_ids),
        "ai_crawler_policy": ai_policy,
    }


async def handle_extract(pool: asyncpg.Pool, job: asyncpg.Record) -> dict:
    """Normalize -> chunk -> embed -> extract entities for one document."""
    document_id = job["payload"]["document_id"]
    document = await pool.fetchrow("select * from document where document_id=$1", document_id)
    if document is None:
        raise ValueError(f"document {document_id} not found")
    return await process_document(pool, document)


HANDLERS = {"crawl": handle_crawl, "extract": handle_extract}


async def run() -> None:
    pool = await get_pool()
    try:
        await ensure_bucket()
    except Exception as exc:  # noqa: BLE001 - storage may be down in unit contexts
        print(f"[worker] warning: could not ensure bucket: {exc}")

    print(f"[worker] {settings.worker_id} polling for jobs: {list(HANDLERS)}")
    while True:
        record = await queue.claim_next(pool, settings.worker_id, list(HANDLERS))
        if record is None:
            await asyncio.sleep(settings.worker_poll_seconds)
            continue

        job_type = record["type"]
        print(f"[worker] claimed {job_type} job {record['job_id']}")
        try:
            metrics = await HANDLERS[job_type](pool, record)
            await queue.complete(pool, record["job_id"], metrics)
            print(f"[worker] done {record['job_id']}: {metrics}")
        except Exception as exc:  # noqa: BLE001 - log, requeue/fail, keep the loop alive
            await queue.fail(pool, record, str(exc))
            print(f"[worker] failed {record['job_id']}: {exc}")


def main() -> None:
    try:
        asyncio.run(run())
    except KeyboardInterrupt:
        pass
    finally:
        asyncio.run(close_pool())


if __name__ == "__main__":
    main()
