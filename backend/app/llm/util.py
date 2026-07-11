"""Shared parsing for LLM entity-extraction responses.

Tolerant of both a bare JSON array and a wrapped object ({"entities": [...]}),
so it works with OpenAI's json_object mode and Anthropic's freer output.
"""
from __future__ import annotations

import json

from app.llm.base import ExtractedEntity


def parse_entities_json(raw: str) -> list[ExtractedEntity]:
    payload = _extract_json(raw)
    if payload is None:
        return []
    items = payload.get("entities") if isinstance(payload, dict) else payload
    if not isinstance(items, list):
        return []

    out: list[ExtractedEntity] = []
    for it in items:
        if not isinstance(it, dict) or not it.get("name"):
            continue
        try:
            confidence = float(it.get("confidence", 0.6))
        except (TypeError, ValueError):
            confidence = 0.6
        out.append(
            ExtractedEntity(
                name=str(it["name"]).strip(),
                entity_type=str(it.get("entity_type", "Entity")),
                confidence=max(0.0, min(1.0, confidence)),
            )
        )
    return out


def _extract_json(raw: str):
    raw = raw.strip()
    # Try an array first (the entity list itself, even when nested in an object or
    # wrapped in prose), then fall back to a top-level object.
    for opener, closer in (("[", "]"), ("{", "}")):
        start, end = raw.find(opener), raw.rfind(closer)
        if start != -1 and end > start:
            try:
                return json.loads(raw[start : end + 1])
            except json.JSONDecodeError:
                continue
    return None
