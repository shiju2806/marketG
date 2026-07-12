"""Recommendation generation — grounded in the DELTA (twin vs probe) + crawl reality.

Every recommendation ties to a specific gap: crawlability, a category where you
have content AI can't see (hidden), or a category with no content at all (missing).
Replaces the old generic "publish authoritative content" template.
"""
from __future__ import annotations

from app.recommend.delta import compute_delta


def _competitors(cat: dict, n: int = 4) -> str:
    comps = cat.get("competitors", [])[:n]
    return ", ".join(comps) if comps else "competitors"


async def generate_recommendations(pool, account_id, organization_id) -> list[dict]:
    diag_row = await pool.fetchrow(
        "select crawl_diagnosis from source where organization_id=$1 and crawl_diagnosis is not null "
        "order by created_at desc limit 1",
        organization_id,
    )
    diag = diag_row["crawl_diagnosis"] if diag_row else None
    delta = await compute_delta(pool, organization_id)

    recs: list[dict] = []

    # 1) Crawlability — the root issue when the site is unreadable. Comes first.
    if diag and diag.get("status") in ("blocked", "thin", "unreachable"):
        recs.append({
            "title": f"{diag['headline']} Fix this first.",
            "missing_type": "crawlability",
            "missing_detail": diag["detail"],
            "affects": ["retrieval", "citation", "trust"],
            "expected_impact": "high",
            "source": {"crawl": diag.get("status")},
        })
    elif diag and diag.get("status") == "readable" and not diag.get("has_structured_data"):
        recs.append({
            "title": "Add schema.org structured data to key pages",
            "missing_type": "machine_readability",
            "missing_detail": "AI can read your pages, but they have no structured data (schema.org). "
                              "Add Vehicle/Product markup so assistants can extract your specifics.",
            "affects": ["retrieval", "machine_readability"],
            "expected_impact": "medium",
            "source": {},
        })

    # 2) Delta-driven, per-category gaps.
    for cat in delta["categories"]:
        q = cat["question"]
        if cat["quadrant"] == "hidden":
            ev = cat.get("evidence") or {}
            where = ev.get("heading") or ev.get("url") or "your site"
            recs.append({
                "title": f"AI can't find your content for “{q}”",
                "missing_type": "citation",
                "missing_detail": f"You already have relevant content ({where}), but AI names "
                                  f"{_competitors(cat)} instead. Your page isn't reaching AI's sources — "
                                  "make it more citable: clearer facts, structured data, and third-party coverage.",
                "affects": ["citation"],
                "expected_impact": "high",
                "source": cat,
            })
        elif cat["quadrant"] == "missing":
            recs.append({
                "title": f"No content for “{q}”",
                "missing_type": "content",
                "missing_detail": f"AI is asked this and names {_competitors(cat)}. Your site has no content "
                                  "targeting it — publish an authoritative page for this category.",
                "affects": ["citation", "retrieval"],
                "expected_impact": "high",
                "source": cat,
            })
        elif cat["quadrant"] == "unknown" and not cat["ai_mentions"] and cat["competitors"]:
            recs.append({
                "title": f"AI names {_competitors(cat, 3)} — not you — for “{q}”",
                "missing_type": "citation",
                "missing_detail": "We couldn't read your site to check whether you cover this. Fix crawlability "
                                  "first, then ensure you have authoritative content for this category.",
                "affects": ["citation"],
                "expected_impact": "high",
                "source": cat,
            })

    async with pool.acquire() as conn:
        async with conn.transaction():
            await conn.execute(
                "delete from recommendation where organization_id=$1 and status='open'", organization_id
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
