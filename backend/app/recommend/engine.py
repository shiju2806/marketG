"""Recommendation generation — gather gap signals from the twin + latest runs,
build ranked recommendations, and persist them (replacing prior open ones).
"""
from __future__ import annotations

from app.recommend.builder import build_recommendations


async def generate_recommendations(pool, account_id, organization_id) -> list[dict]:
    signals = await _gather_signals(pool, organization_id)
    recs = build_recommendations(**signals)

    async with pool.acquire() as conn:
        async with conn.transaction():
            await conn.execute(
                "delete from recommendation where organization_id=$1 and status='open'",
                organization_id,
            )
            for r in recs:
                await conn.execute(
                    """
                    insert into recommendation (account_id, organization_id, title, missing_type,
                        missing_detail, affects, expected_impact, source)
                    values ($1,$2,$3,$4,$5,$6,$7,$8::jsonb)
                    """,
                    account_id, organization_id, r["title"], r["missing_type"],
                    r["missing_detail"], r["affects"], r["expected_impact"], r["source"],
                )
    return recs


async def _gather_signals(pool, organization_id) -> dict:
    # Machine-readability gaps from crawled documents.
    docs = await pool.fetch(
        "select has_schema_org, ai_crawler_policy from document where organization_id=$1",
        organization_id,
    )
    blocked: set[str] = set()
    unstructured = 0
    for d in docs:
        bots = (d["ai_crawler_policy"] or {}).get("bots", {})
        for bot, status in bots.items():
            if status == "blocked":
                blocked.add(bot)
        if not d["has_schema_org"]:
            unstructured += 1
    unstructured_share = (unstructured / len(docs)) if docs else 0.0

    # Citation gaps from the latest probe run (questions where we're absent but rivals aren't).
    citation_gaps: list[dict] = []
    latest_probe = await pool.fetchval(
        "select probe_run_id from probe_run where organization_id=$1 and status='done' "
        "order by created_at desc limit 1",
        organization_id,
    )
    if latest_probe:
        rows = await pool.fetch(
            """
            select question, competitor_mentions
              from probe_result
             where probe_run_id=$1 and organization_mentioned = false
               and array_length(competitor_mentions, 1) > 0
             order by question
            """,
            latest_probe,
        )
        seen = set()
        for r in rows:
            if r["question"] in seen:
                continue
            seen.add(r["question"])
            citation_gaps.append({"question": r["question"], "competitors": list(r["competitor_mentions"])})

    # Coverage gaps: vehicles with no claims/relationships.
    uncovered = [
        r["canonical_name"]
        for r in await pool.fetch(
            """
            select e.canonical_name from entity e
             where e.organization_id=$1 and e.entity_type='Vehicle' and e.status='resolved'
               and not exists (select 1 from claim c where c.subject_entity_id=e.entity_id and c.valid_to is null)
               and not exists (select 1 from relationship r where r.subject_entity_id=e.entity_id and r.valid_to is null)
            """,
            organization_id,
        )
    ]

    return {
        "blocked_bots": sorted(blocked),
        "unstructured_page_share": unstructured_share,
        "citation_gaps": citation_gaps,
        "uncovered_vehicles": uncovered,
        "low_trust_entities": [],
    }
