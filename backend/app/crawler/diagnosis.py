"""Crawl diagnosis — 'here's what happened when AI tried to read your site'.

Turns raw crawl results into the report's opening finding: could a machine read
the site, or is it blocked / JS-walled / empty — and what that means for AI
visibility (the SEO-vs-GEO distinction). Honest by design: if we couldn't read
the site, we say so instead of fabricating a twin.
"""
from __future__ import annotations

from app.crawler.crawler import PageResult

_MIN_READABLE_CHARS = 250


def diagnose(pages: list[PageResult], ai_policy: dict) -> dict:
    attempted = len(pages)
    readable = [p for p in pages if p.http_status and 200 <= p.http_status < 300 and len(p.text) >= _MIN_READABLE_CHARS]
    blocked = [p for p in pages if p.http_status and p.http_status in (401, 403, 429)]
    server_err = [p for p in pages if p.http_status and p.http_status >= 500]
    thin = [
        p for p in pages
        if p.http_status and 200 <= p.http_status < 300 and len(p.text) < _MIN_READABLE_CHARS
    ]
    errored = [p for p in pages if p.http_status is None]

    bots = (ai_policy or {}).get("bots", {})
    ai_allowed_in_robots = bool(bots) and all(v == "allowed" for v in bots.values())
    blocked_bots = [b for b, v in bots.items() if v == "blocked"]
    has_structured = any(p.has_schema_org for p in readable)

    if attempted == 0 or (errored and not readable and not blocked and not thin):
        status = "unreachable"
    elif blocked and not readable:
        status = "blocked"
    elif readable:
        status = "readable"
    else:
        status = "thin"

    headline, detail = _verdict(status, ai_allowed_in_robots, blocked_bots, has_structured, len(readable))

    return {
        "status": status,               # readable | blocked | thin | unreachable
        "pages_attempted": attempted,
        "pages_read": len(readable),
        "pages_blocked": len(blocked),
        "server_errors": len(server_err),
        "thin_pages": len(thin),
        "ai_crawler_policy": bots,
        "ai_allowed_in_robots": ai_allowed_in_robots,
        "blocked_bots": blocked_bots,
        "has_structured_data": has_structured,
        "headline": headline,
        "detail": detail,
    }


def _verdict(status, ai_allowed, blocked_bots, has_structured, n_read):
    if status == "blocked":
        head = "AI can't read your website."
        detail = (
            "Every page we requested returned a block (e.g. 403 Forbidden) — even from a "
            "real browser user-agent. Your site sits behind bot protection that refuses "
            "automated readers. "
        )
        if ai_allowed:
            detail += (
                "Notably, your robots.txt *welcomes* AI crawlers — but the server still "
                "blocks them. That's the SEO-vs-GEO gap: Google is whitelisted so search "
                "works, but AI assistants get refused, so they describe you from third "
                "parties instead of your own words. Fix: allowlist AI crawlers (and ours) "
                "at your CDN/WAF, or provide a sitemap/content feed."
            )
        elif blocked_bots:
            detail += f"Your robots.txt also blocks: {', '.join(blocked_bots)}. Unblock them."
        return head, detail

    if status == "thin":
        return (
            "AI reads almost nothing on your site.",
            "Pages loaded but returned little machine-readable text — usually a heavy "
            "JavaScript app that renders for humans but not for AI crawlers. Add server-"
            "rendered content and structured data so assistants can extract your facts.",
        )

    if status == "unreachable":
        return (
            "We couldn't reach your website.",
            "Requests failed to connect. Check the URL, or that the site is publicly reachable.",
        )

    # readable
    schema_note = (
        " It also exposes structured data (schema.org), which helps assistants extract facts."
        if has_structured
        else " But it has no structured data (schema.org) — add Vehicle/Product markup so "
        "assistants can extract specifics."
    )
    return (
        "AI can read your website.",
        f"We read {n_read} page(s) of real content.{schema_note}",
    )
