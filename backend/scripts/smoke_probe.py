"""End-to-end smoke for the External AI Probe (Sprint 4b).

Seeds a couple of real entities for the demo Rivian org (so question generation
produces real buyer questions), then probes the keyed assistants and prints what
they actually said. Requires OPENAI_API_KEY (and network).

Usage:  python -m scripts.smoke_probe
"""
from __future__ import annotations

import asyncio
import json
from uuid import UUID

from app.db import close_pool, get_pool
from app.probe.engine import run_probe

DEMO_ACCOUNT = UUID("00000000-0000-0000-0000-000000000001")
DEMO_ORG = UUID("00000000-0000-0000-0000-0000000000a1")  # seeded "Rivian", rivian.com


async def _seed_entities(pool) -> None:
    for etype, name, conf in [("Vehicle", "Rivian R1S", 0.95), ("Competitor", "Tesla", 0.9)]:
        await pool.execute(
            """
            insert into entity (account_id, organization_id, entity_type, canonical_name,
                                confidence, status, source)
            values ($1,$2,$3,$4,$5,'resolved','manual')
            on conflict (organization_id, entity_type, lower(canonical_name)) do nothing
            """,
            DEMO_ACCOUNT, DEMO_ORG, etype, name, conf,
        )


async def main() -> int:
    pool = await get_pool()
    try:
        await _seed_entities(pool)
        print("• seeded Rivian R1S (Vehicle) + Tesla (Competitor)")
        result = await run_probe(pool, DEMO_ACCOUNT, DEMO_ORG)
        print(f"• probe complete: {json.dumps(result)}")

        rows = await pool.fetch(
            """
            select question, model, organization_mentioned, competitor_mentions,
                   left(answer, 160) as preview
              from probe_result where probe_run_id=$1 order by question
            """,
            UUID(result["probe_run_id"]),
        )
        print(f"\n=== {len(rows)} probe results ===")
        for r in rows:
            mark = "✓ mentions Rivian" if r["organization_mentioned"] else "✗ no Rivian"
            comps = ", ".join(r["competitor_mentions"]) or "—"
            print(f"\n[{r['model']}] {r['question']}\n  {mark} | competitors: {comps}\n  {r['preview']}…")

        print(f"\nCITATION score (real-AI mention rate): {result['citation']}")
        print(f"Earned-vs-owned: {result['earned_owned']}")
        print(f"Visibility overall (with citation): {result['visibility_overall']}")

        ok = result["results"] > 0
        print("\nRESULT:", "PASS ✅" if ok else "FAIL ❌ (no targets ran — check OPENAI_API_KEY)")
        return 0 if ok else 1
    finally:
        await close_pool()


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
