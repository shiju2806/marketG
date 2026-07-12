"""The delta engine — the gap between what you HAVE and what AI SAYS.

Joins the twin (your crawled content) with the probe (real AI answers) on each
buyer category, and classifies every category into the 2×2 that makes
recommendations concrete:

                    AI mentions you   |   AI doesn't mention you
    you have content    winning       |   HIDDEN  (content exists, AI can't see/cite it)
    no content          borrowed      |   MISSING (no content for a category AI is asked)

If the site was unreadable (blocked crawl), content presence is 'unknown' and the
top issue is crawlability, not content.
"""
from __future__ import annotations

from app.llm.factory import get_embedding_provider

_RELEVANT_COS = 0.25  # cosine ≥ this => the twin has content on-topic for the question


def _vector_literal(vec: list[float]) -> str:
    return "[" + ",".join(f"{x:.6f}" for x in vec) + "]"


def _classify(have_content: bool | None, ai_mentions: bool) -> str:
    if have_content is None:
        return "unknown"  # site unreadable — can't assess content
    if ai_mentions and have_content:
        return "winning"
    if ai_mentions and not have_content:
        return "borrowed"  # AI knows you from third parties, not your own content
    if have_content and not ai_mentions:
        return "hidden"    # you have it, AI can't see/cite it
    return "missing"       # no content for a category AI is asked about


async def compute_delta(pool, organization_id) -> dict:
    src = await pool.fetchrow(
        "select crawl_status from source where organization_id=$1 and crawl_diagnosis is not null "
        "order by created_at desc limit 1",
        organization_id,
    )
    crawl_status = src["crawl_status"] if src else None
    chunk_count = await pool.fetchval(
        "select count(*) from chunk where organization_id=$1", organization_id
    )
    twin_readable = chunk_count > 0

    run = await pool.fetchrow(
        "select probe_run_id from probe_run where organization_id=$1 and status='done' "
        "order by created_at desc limit 1",
        organization_id,
    )
    if run is None:
        return {"crawl_status": crawl_status, "twin_readable": twin_readable, "categories": []}

    rows = await pool.fetch(
        "select question, organization_mentioned, competitor_mentions from probe_result "
        "where probe_run_id=$1",
        run["probe_run_id"],
    )
    grouped: dict[str, dict] = {}
    for r in rows:
        g = grouped.setdefault(r["question"], {"mentioned": False, "competitors": set()})
        g["mentioned"] = g["mentioned"] or r["organization_mentioned"]
        g["competitors"].update(r["competitor_mentions"])

    embedder = get_embedding_provider() if twin_readable else None
    categories = []
    for question, info in grouped.items():
        have, evidence = None, None
        if twin_readable and embedder is not None:
            best = await _best_match(pool, organization_id, question, embedder)
            have = bool(best and best["cos"] >= _RELEVANT_COS)
            evidence = best if have else None
        categories.append({
            "question": question,
            "ai_mentions": info["mentioned"],
            "competitors": sorted(info["competitors"]),
            "have_content": have,
            "evidence": evidence,
            "quadrant": _classify(have, info["mentioned"]),
        })
    # Order: hidden + missing first (the actionable gaps), then winning.
    order = {"hidden": 0, "missing": 1, "unknown": 2, "borrowed": 3, "winning": 4}
    categories.sort(key=lambda c: order.get(c["quadrant"], 9))
    return {"crawl_status": crawl_status, "twin_readable": twin_readable, "categories": categories}


async def _best_match(pool, organization_id, question: str, embedder) -> dict | None:
    vecs, _ = await embedder.embed([question])
    lit = _vector_literal(vecs[0])
    row = await pool.fetchrow(
        """
        select c.heading, d.url, 1 - (c.embedding <=> $2::vector) as cos
          from chunk c join document d on d.document_id = c.document_id
         where c.organization_id = $1 and c.embedding is not null
         order by c.embedding <=> $2::vector
         limit 1
        """,
        organization_id, lit,
    )
    if row is None:
        return None
    return {"heading": row["heading"], "url": row["url"], "cos": round(float(row["cos"]), 3)}
