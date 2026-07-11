"""End-to-end smoke test for the Sprint 1 ingestion slice.

Drives the real pipeline against a live local Supabase:
  create source -> enqueue crawl job -> claim it (as a worker would) ->
  run handle_crawl (render + classify + machine-readability + storage) ->
  read back the document rows.

Usage:  python -m scripts.smoke_crawl https://www.rivian.com
Requires: `supabase start` running and backend/.env configured.
"""
from __future__ import annotations

import asyncio
import json
import sys
from uuid import UUID

from app.db import close_pool, get_pool
from app.jobs import queue
from app.jobs.worker import handle_crawl
from app.storage import ensure_bucket

DEMO_ACCOUNT = UUID("00000000-0000-0000-0000-000000000001")
DEMO_ORG = UUID("00000000-0000-0000-0000-0000000000a1")


async def main(seed_url: str) -> int:
    pool = await get_pool()
    try:
        await ensure_bucket()

        source = await pool.fetchrow(
            """
            insert into source (account_id, organization_id, type, seed_url)
            values ($1, $2, 'website', $3)
            returning *
            """,
            DEMO_ACCOUNT,
            DEMO_ORG,
            seed_url,
        )
        print(f"• created source {source['source_id']} -> {seed_url}")

        job_id = await queue.enqueue(
            pool,
            account_id=DEMO_ACCOUNT,
            job_type="crawl",
            organization_id=DEMO_ORG,
            source_id=source["source_id"],
        )
        print(f"• enqueued crawl job {job_id}")

        record = await queue.claim_next(pool, "smoke", ["crawl"])
        assert record is not None and record["job_id"] == job_id, "claim_next did not return our job"
        print(f"• claimed job (attempts={record['attempts']}) — running handler…")

        metrics = await handle_crawl(pool, record)
        await queue.complete(pool, record["job_id"], metrics)
        print(f"• handler done: {json.dumps(metrics)[:300]}")

        rows = await pool.fetch(
            """
            select url, page_classification, js_required, has_schema_org, http_status
              from document
             where source_id = $1
             order by url
            """,
            source["source_id"],
        )
        print(f"\n=== {len(rows)} document rows persisted ===")
        for r in rows:
            print(
                f"  [{r['http_status']}] {r['page_classification']:<13} "
                f"js={str(r['js_required']):<5} schema={str(r['has_schema_org']):<5} {r['url']}"
            )

        # Confirm the machine-readability signal (robots AI-crawler policy) landed.
        policy = await pool.fetchval(
            "select ai_crawler_policy from document where source_id=$1 limit 1", source["source_id"]
        )
        print(f"\nAI-crawler policy (robots.txt): {json.dumps(policy.get('bots') if policy else None)}")

        # Verify account isolation invariant: no document without a matching account.
        leaked = await pool.fetchval("select count(*) from document where account_id <> $1", DEMO_ACCOUNT)
        print(f"account-isolation check — foreign-account documents: {leaked} (expect 0)")

        ok = len(rows) > 0 and leaked == 0
        print("\nRESULT:", "PASS ✅" if ok else "FAIL ❌")
        return 0 if ok else 1
    finally:
        await close_pool()


if __name__ == "__main__":
    url = sys.argv[1] if len(sys.argv) > 1 else "https://example.com"
    raise SystemExit(asyncio.run(main(url)))
