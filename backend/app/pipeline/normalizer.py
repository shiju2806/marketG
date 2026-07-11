"""Document normalization (KIPS §9).

Strip chrome (nav/footer/scripts/ads), keep meaning-bearing structure. Output a
title plus an ordered list of (heading, text) sections, which the chunker turns
into concept-based chunks.
"""
from __future__ import annotations

from dataclasses import dataclass

from bs4 import BeautifulSoup

_STRIP_TAGS = ("script", "style", "noscript", "nav", "footer", "aside", "form", "svg")
_HEADINGS = ("h1", "h2", "h3")


@dataclass
class Section:
    heading: str
    text: str


@dataclass
class NormalizedDoc:
    title: str
    sections: list[Section]


def _clean_text(node) -> str:
    return " ".join(node.get_text(" ").split())


def normalize_html(html: str) -> NormalizedDoc:
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(_STRIP_TAGS):
        tag.decompose()

    title = (soup.title.string.strip() if soup.title and soup.title.string else "") or ""
    main = soup.find("main") or soup.body or soup

    sections: list[Section] = []
    current_heading = title or "Introduction"
    buffer: list[str] = []

    def flush() -> None:
        text = " ".join(" ".join(buffer).split())
        if text:
            sections.append(Section(heading=current_heading, text=text))

    # Walk block-level elements in order, starting a new section at each heading.
    for el in main.find_all(["h1", "h2", "h3", "p", "li", "td", "th"]):
        if el.name in _HEADINGS:
            flush()
            buffer = []
            current_heading = _clean_text(el) or current_heading
        else:
            txt = _clean_text(el)
            if txt:
                buffer.append(txt)
    flush()

    # Fallback: no structured sections -> one section from the whole body.
    if not sections:
        body_text = _clean_text(main)
        if body_text:
            sections.append(Section(heading=title or "Page", text=body_text))

    return NormalizedDoc(title=title, sections=sections)
