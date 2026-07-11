"""Machine-readability signals (ADR-004).

The GM-vs-Rivian pilot made this the most visceral metric: can a machine even
read the brand's own words? We capture two kinds of signal:

  * per-site : robots.txt stance toward AI crawlers (GPTBot, ClaudeBot, ...)
  * per-page : http status, whether JS was required, schema.org presence

`parse_robots` is pure and unit-tested; `fetch_ai_crawler_policy` wraps it with a
network fetch.
"""
from __future__ import annotations

from urllib.parse import urljoin

import httpx
from bs4 import BeautifulSoup

# The crawlers whose access we care about for GEO.
AI_BOTS = ("GPTBot", "ClaudeBot", "PerplexityBot", "Google-Extended", "CCBot")


def parse_robots(robots_txt: str, bots: tuple[str, ...] = AI_BOTS) -> dict[str, str]:
    """Return {bot: 'allowed'|'blocked'} from robots.txt content.

    A bot is 'blocked' if the most specific matching group (its own user-agent,
    else the '*' group) contains `Disallow: /`. Otherwise 'allowed'.
    """
    groups: dict[str, list[str]] = {}
    current: list[str] = []
    for raw in robots_txt.splitlines():
        line = raw.split("#", 1)[0].strip()
        if not line or ":" not in line:
            continue
        field, value = (p.strip() for p in line.split(":", 1))
        field = field.lower()
        if field == "user-agent":
            current = groups.setdefault(value.lower(), [])
        elif field == "disallow" and current is not None:
            current.append(value)

    def blocks_root(agent: str) -> bool:
        rules = groups.get(agent.lower())
        if rules is None:
            rules = groups.get("*", [])
        return any(r == "/" for r in rules)

    return {bot: ("blocked" if blocks_root(bot) else "allowed") for bot in bots}


async def fetch_ai_crawler_policy(base_url: str, client: httpx.AsyncClient) -> dict:
    """Fetch /robots.txt and classify AI-crawler access. Fail-open on error."""
    robots_url = urljoin(base_url, "/robots.txt")
    try:
        resp = await client.get(robots_url, timeout=10.0)
        if resp.status_code == 200:
            return {"status": resp.status_code, "bots": parse_robots(resp.text)}
        return {"status": resp.status_code, "bots": {b: "unknown" for b in AI_BOTS}}
    except httpx.HTTPError as exc:  # network/timeout — record, don't crash
        return {"status": None, "error": str(exc), "bots": {b: "unknown" for b in AI_BOTS}}


def detect_schema_org(html: str) -> bool:
    """True if the page exposes structured data (JSON-LD or microdata)."""
    soup = BeautifulSoup(html, "html.parser")
    if soup.find("script", attrs={"type": "application/ld+json"}):
        return True
    if soup.find(attrs={"itemtype": True}):
        return True
    return "schema.org" in html
