"""One-shot full analysis: crawl -> twin -> scores -> probe -> recommendations.

Powers the single "Analyze a website" action. Runs inline within one job so the
frontend can poll a single status. Updates job.stage as it progresses.
"""
from __future__ import annotations

import httpx

from app.config import settings
from app.crawler.classifier import classify_page
from app.crawler.crawler import crawl_site
from app.crawler.diagnosis import diagnose
from app.crawler.machine_readability import fetch_ai_crawler_policy
from app.pipeline.extract import process_document
from app.probe.engine import run_probe
from app.recommend.engine import generate_recommendations
from app.storage import ensure_bucket, raw_key, upload_raw
from app.visibility.engine import run_visibility


async def crawl_and_store(pool, source) -> list:
    """Crawl a source's site and persist documents + machine-readability. Returns doc ids."""
    await pool.execute("update source set status='crawling' where source_id=$1", source["source_id"])
    async with httpx.AsyncClient(follow_redirects=True) as client:
        ai_policy = await fetch_ai_crawler_policy(source["seed_url"], client)

    pages = await crawl_site(
        source["seed_url"], max_pages=settings.crawl_max_pages,
        max_depth=settings.crawl_max_depth, timeout_ms=settings.crawl_timeout_ms,
    )

    # Diagnose what happened reading the site — the report's opening finding.
    diagnosis = diagnose(pages, ai_policy)
    await pool.execute(
        "update source set crawl_status=$2, crawl_diagnosis=$3::jsonb where source_id=$1",
        source["source_id"], diagnosis["status"], diagnosis,
    )

    doc_ids, skipped = [], 0
    for page in pages:
        if not page.html:
            continue
        # Don't build a twin from blocked/error pages — that's how we ended up with a
        # fake "twin" from a 403 error page. Only readable pages feed extraction.
        readable = bool(page.http_status and 200 <= page.http_status < 300 and len(page.text) >= 250)

        # Incremental (D-05): if this page's content_hash is unchanged since the last
        # crawl AND it already produced chunks, skip re-extraction (the costly step).
        prior = await pool.fetchrow(
            "select document_id, content_hash from document where source_id=$1 and url=$2",
            source["source_id"], page.url,
        )
        unchanged = (
            prior is not None and prior["content_hash"] == page.content_hash
            and await pool.fetchval("select count(*) from chunk where document_id=$1", prior["document_id"]) > 0
        )

        key = raw_key(str(source["account_id"]), str(source["source_id"]), page.content_hash)
        await upload_raw(key, page.html)
        doc_id = await pool.fetchval(
            """
            insert into document (account_id, organization_id, source_id, url, page_classification,
                object_storage_key, content_hash, http_status, js_required, has_schema_org, ai_crawler_policy)
            values ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11::jsonb)
            on conflict (source_id, url) do update set
                page_classification=excluded.page_classification, object_storage_key=excluded.object_storage_key,
                content_hash=excluded.content_hash, http_status=excluded.http_status,
                js_required=excluded.js_required, has_schema_org=excluded.has_schema_org,
                ai_crawler_policy=excluded.ai_crawler_policy, crawled_at=now()
            returning document_id
            """,
            source["account_id"], source["organization_id"], source["source_id"], page.url,
            classify_page(page.url, page.text), key, page.content_hash, page.http_status,
            page.js_required, page.has_schema_org, ai_policy,
        )
        if readable and not unchanged:
            doc_ids.append(doc_id)
        elif unchanged:
            skipped += 1

    await pool.execute("update source set status='done' where source_id=$1", source["source_id"])
    return {"doc_ids": doc_ids, "skipped": skipped}


async def run_full_analysis(pool, job_id, account_id, source) -> dict:
    async def stage(name: str) -> None:
        await pool.execute("update job set stage=$2 where job_id=$1", job_id, name)

    await ensure_bucket()

    await stage("crawling")
    crawl_result = await crawl_and_store(pool, source)
    doc_ids, skipped = crawl_result["doc_ids"], crawl_result["skipped"]

    await stage("building twin" if not skipped else f"building twin ({skipped} unchanged, skipped)")
    total_cost, total_tokens = 0.0, 0
    for doc_id in doc_ids:
        doc = await pool.fetchrow("select * from document where document_id=$1", doc_id)
        if doc:
            r = await process_document(pool, doc)
            total_cost += r.get("cost_usd", 0.0) or 0.0
            total_tokens += r.get("tokens", 0) or 0

    await stage("scoring")
    await run_visibility(pool, account_id, source["organization_id"])

    await stage("probing AI")
    probe = await run_probe(pool, account_id, source["organization_id"])
    total_cost += (probe.get("cost_usd") or 0.0)

    await stage("recommendations")
    recs = await generate_recommendations(pool, account_id, source["organization_id"])

    # Persist per-run spend so the usage endpoint / caps have real data (D-05).
    metrics = {"cost_usd": round(total_cost, 6), "tokens": total_tokens,
               "pages": len(doc_ids), "pages_skipped": skipped}
    await pool.execute("update job set metrics=$2::jsonb where job_id=$1", job_id, metrics)

    await stage("done")
    return {**metrics, "citation": probe.get("citation"), "recommendations": len(recs),
            "organization_id": str(source["organization_id"])}
