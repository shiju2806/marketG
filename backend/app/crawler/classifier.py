"""Page classification (KIPS §7).

Different pages carry different authority, so every page gets a class. This is a
deliberately simple, pure, testable heuristic over the URL path and visible text
— the LLM-based classifier is a later refinement (see DEFERRALS). Returns an
open-vocabulary string, never a fixed enum (ADR-006).
"""
from __future__ import annotations

from urllib.parse import urlparse

# Ordered: first matching rule wins. Keys are matched against the URL path.
_URL_RULES: list[tuple[str, tuple[str, ...]]] = [
    ("pricing", ("/pricing", "/price", "/build", "/configurator", "/shop")),
    ("security", ("/security", "/trust", "/compliance", "/privacy")),
    ("integration", ("/integrations", "/partners", "/marketplace", "/app")),
    ("documentation", ("/docs", "/documentation", "/developer", "/api", "/support", "/help")),
    ("case_study", ("/customers", "/case-stud", "/success", "/stories")),
    ("blog", ("/blog", "/news", "/press", "/articles", "/insights")),
    ("careers", ("/careers", "/jobs")),
    ("product", ("/product", "/models", "/vehicles", "/r1t", "/r1s", "/r2", "/features")),
    ("about", ("/about", "/company", "/who-we-are")),
]

_TEXT_HINTS: list[tuple[str, tuple[str, ...]]] = [
    ("pricing", ("starting at", "per month", "msrp", "$")),
    ("security", ("soc 2", "soc2", "iso 27001", "gdpr", "hipaa")),
    ("product", ("horsepower", "range", "mpg", "towing", "0-60", "specs")),
]


def classify_page(url: str, text: str = "") -> str:
    """Classify a page from its URL path (primary) and visible text (fallback)."""
    path = (urlparse(url).path or "/").lower().rstrip("/")

    if path in ("", "/"):
        return "homepage"

    for label, needles in _URL_RULES:
        if any(n in path for n in needles):
            return label

    lowered = text.lower()
    for label, needles in _TEXT_HINTS:
        if sum(n in lowered for n in needles) >= 2:
            return label

    return "other"
