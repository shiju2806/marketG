"""Website crawler (ADR-003: render every page headless with Playwright).

Brand sites are JS/SPA (both GM and Rivian in the pilots), so static fetch would
capture almost nothing. We render each page, capture the post-JS DOM, and detect
whether JS was actually required by comparing rendered vs. static text length.

Same-domain BFS bounded by max_pages / max_depth. Returns structured page results
the worker persists; the crawler itself does no DB or storage work (keeps it pure
and independently testable against a live site).
"""
from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from urllib.parse import urldefrag, urljoin, urlparse

import httpx
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright

from app.crawler.machine_readability import detect_schema_org


@dataclass
class PageResult:
    url: str
    html: str
    http_status: int | None
    js_required: bool
    has_schema_org: bool
    text: str
    content_hash: str
    links: list[str] = field(default_factory=list)


def _same_domain(a: str, b: str) -> bool:
    return urlparse(a).netloc.replace("www.", "") == urlparse(b).netloc.replace("www.", "")


def _visible_text(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()
    return " ".join(soup.get_text(" ").split())


def _extract_links(base_url: str, html: str) -> list[str]:
    soup = BeautifulSoup(html, "html.parser")
    out: list[str] = []
    for a in soup.find_all("a", href=True):
        joined, _ = urldefrag(urljoin(base_url, a["href"]))
        if joined.startswith("http"):
            out.append(joined)
    return out


async def _static_text_len(url: str, client: httpx.AsyncClient) -> int:
    """Length of visible text WITHOUT running JS — used to flag js_required."""
    try:
        resp = await client.get(url, timeout=10.0, follow_redirects=True)
        return len(_visible_text(resp.text))
    except httpx.HTTPError:
        return 0


async def crawl_site(
    seed_url: str,
    max_pages: int = 40,
    max_depth: int = 2,
    timeout_ms: int = 20_000,
) -> list[PageResult]:
    """Render and crawl a site starting at seed_url. Returns page results."""
    results: list[PageResult] = []
    seen: set[str] = set()
    queue: list[tuple[str, int]] = [(urldefrag(seed_url)[0], 0)]

    async with async_playwright() as pw, httpx.AsyncClient(
        headers={"User-Agent": "marketGBot/0.1 (+https://marketg.dev)"}
    ) as client:
        browser = await pw.chromium.launch(headless=True)
        page = await browser.new_page()
        try:
            while queue and len(results) < max_pages:
                url, depth = queue.pop(0)
                if url in seen:
                    continue
                seen.add(url)

                try:
                    response = await page.goto(url, timeout=timeout_ms, wait_until="networkidle")
                    status = response.status if response else None
                    html = await page.content()
                except Exception as exc:  # noqa: BLE001 - record and move on
                    results.append(
                        PageResult(url, "", None, False, False, f"ERROR: {exc}", "", [])
                    )
                    continue

                rendered_text = _visible_text(html)
                static_len = await _static_text_len(url, client)
                js_required = len(rendered_text) > max(static_len * 1.5, static_len + 500)

                results.append(
                    PageResult(
                        url=url,
                        html=html,
                        http_status=status,
                        js_required=js_required,
                        has_schema_org=detect_schema_org(html),
                        text=rendered_text,
                        content_hash=hashlib.sha256(html.encode("utf-8")).hexdigest(),
                        links=_extract_links(url, html),
                    )
                )

                if depth < max_depth:
                    for link in _extract_links(url, html):
                        if _same_domain(seed_url, link) and link not in seen:
                            queue.append((link, depth + 1))
        finally:
            await browser.close()

    return results
