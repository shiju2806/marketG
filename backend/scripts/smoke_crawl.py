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
from app.jobs.worker import handle_crawl, handle_extract
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
        print(f"• crawl done: {json.dumps(metrics)[:300]}")

        # Drain the extract jobs the crawl fanned out (Sprint 2).
        extract_runs = 0
        while True:
            erec = await queue.claim_next(pool, "smoke", ["extract"])
            if erec is None:
                break
            em = await handle_extract(pool, erec)
            await queue.complete(pool, erec["job_id"], em)
            extract_runs += 1
            print(f"  · extract {erec['payload']['document_id'][:8]}: {json.dumps(em)}")
        print(f"• extract jobs run: {extract_runs}")

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

        # Sprint 2 results: chunks (with embeddings + FTS) and candidate entities.
        chunk_rows = await pool.fetch(
            """
            select chunk_type, count(*) n,
                   count(embedding) with_vec,
                   count(*) filter (where tsv is not null) with_fts
              from chunk c
              join document d on d.document_id = c.document_id
             where d.source_id = $1
             group by chunk_type order by n desc
            """,
            source["source_id"],
        )
        total_chunks = sum(r["n"] for r in chunk_rows)
        with_vec = sum(r["with_vec"] for r in chunk_rows)
        with_fts = sum(r["with_fts"] for r in chunk_rows)
        print(f"\n=== {total_chunks} chunks ({with_vec} embedded, {with_fts} FTS-indexed) ===")
        for r in chunk_rows:
            print(f"  {r['chunk_type']:<22} {r['n']}")

        ent_rows = await pool.fetch(
            """
            select entity_type, canonical_name, confidence
              from entity where organization_id = $1
             order by confidence desc, canonical_name limit 20
            """,
            DEMO_ORG,
        )
        print(f"\n=== {len(ent_rows)} candidate entities (top 20) ===")
        for e in ent_rows:
            print(f"  [{e['confidence']}] {e['entity_type']:<12} {e['canonical_name']}")

        # A hybrid-retrieval sanity check: FTS finds a spec chunk.
        fts_hit = await pool.fetchval(
            """
            select count(*) from chunk c join document d on d.document_id=c.document_id
             where d.source_id=$1 and c.tsv @@ plainto_tsquery('english', 'horsepower range')
            """,
            source["source_id"],
        )
        print(f"\nFTS query 'horsepower range' matched {fts_hit} chunk(s)")

        # Verify account isolation invariant across all Sprint-1/2 tables.
        leaked = 0
        for tbl in ("document", "chunk", "entity"):
            leaked += await pool.fetchval(
                f"select count(*) from {tbl} where account_id <> $1", DEMO_ACCOUNT
            )
        print(f"account-isolation check — foreign-account rows across doc/chunk/entity: {leaked} (expect 0)")

        ok = len(rows) > 0 and total_chunks > 0 and with_vec == total_chunks and len(ent_rows) > 0 and leaked == 0
        print("\nRESULT:", "PASS ✅" if ok else "FAIL ❌")
        return 0 if ok else 1
    finally:
        await close_pool()


if __name__ == "__main__":
    url = sys.argv[1] if len(sys.argv) > 1 else "https://example.com"
    raise SystemExit(asyncio.run(main(url)))
