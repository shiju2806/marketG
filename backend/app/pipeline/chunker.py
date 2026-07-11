"""Concept-based chunking (KIPS §10).

Chunk by *business concept*, not by fixed token count: each normalized section is
a candidate chunk, tagged with a chunk_type inferred from the heading/text via the
vertical pack's hints (ADR-006), and page classification as a fallback. Overlong
sections are split on sentence boundaries to respect the size cap (D-05).
"""
from __future__ import annotations

import re
from dataclasses import dataclass

from app.config import settings
from app.pipeline.normalizer import Section
from app.verticals.base import VerticalPack

_SENT = re.compile(r"(?<=[.!?])\s+")


@dataclass
class Chunk:
    index: int
    chunk_type: str
    heading: str
    text: str
    token_estimate: int


def _infer_type(heading: str, text: str, pack: VerticalPack, page_class: str | None) -> str:
    hay = f"{heading} {text[:200]}".lower()
    for needle, chunk_type in pack.chunk_type_hints.items():
        if needle in hay:
            return chunk_type
    # Fall back to the page's classification (Sprint 1) if we have one.
    return page_class or "general"


def _split_to_size(text: str, max_chars: int) -> list[str]:
    if len(text) <= max_chars:
        return [text]
    parts: list[str] = []
    buf = ""
    for sentence in _SENT.split(text):
        if buf and len(buf) + len(sentence) + 1 > max_chars:
            parts.append(buf.strip())
            buf = sentence
        else:
            buf = f"{buf} {sentence}".strip()
    if buf.strip():
        parts.append(buf.strip())
    return parts


def chunk_sections(
    sections: list[Section], pack: VerticalPack, page_classification: str | None = None
) -> list[Chunk]:
    chunks: list[Chunk] = []
    idx = 0
    for section in sections:
        chunk_type = _infer_type(section.heading, section.text, pack, page_classification)
        for piece in _split_to_size(section.text, settings.chunk_max_chars):
            if len(piece) < settings.chunk_min_chars:
                continue
            chunks.append(
                Chunk(
                    index=idx,
                    chunk_type=chunk_type,
                    heading=section.heading,
                    text=piece,
                    token_estimate=max(1, len(piece) // 4),
                )
            )
            idx += 1
    return chunks
