"""Shared parsing for LLM entity-extraction responses.

Tolerant of both a bare JSON array and a wrapped object ({"entities": [...]}),
so it works with OpenAI's json_object mode and Anthropic's freer output.
"""
from __future__ import annotations

import json

from app.llm.base import (
    ExtractedClaim,
    ExtractedEntity,
    ExtractedRelationship,
    KnowledgeExtraction,
)


def _clamp(x, default=0.6) -> float:
    try:
        return max(0.0, min(1.0, float(x)))
    except (TypeError, ValueError):
        return default


def parse_knowledge_json(raw: str) -> KnowledgeExtraction:
    """Parse {"entities":[...], "relationships":[...], "claims":[...]}."""
    obj = _extract_object(raw)
    if not isinstance(obj, dict):
        return KnowledgeExtraction()

    entities = [
        ExtractedEntity(str(e["name"]).strip(), str(e.get("entity_type", "Entity")), _clamp(e.get("confidence")))
        for e in obj.get("entities", [])
        if isinstance(e, dict) and e.get("name")
    ]
    relationships = [
        ExtractedRelationship(
            str(r["subject"]).strip(), str(r["predicate"]).strip(), str(r["object"]).strip(),
            _clamp(r.get("confidence")),
        )
        for r in obj.get("relationships", [])
        if isinstance(r, dict) and r.get("subject") and r.get("predicate") and r.get("object")
    ]
    claims = [
        ExtractedClaim(
            subject=str(c["subject"]).strip(),
            predicate=str(c.get("predicate", "")).strip(),
            object=str(c.get("object", "")).strip(),
            value=str(c.get("value", "")).strip(),
            claim_type=str(c.get("claim_type", "capability")).strip(),
            confidence=_clamp(c.get("confidence")),
        )
        for c in obj.get("claims", [])
        if isinstance(c, dict) and c.get("subject") and c.get("predicate")
    ]
    return KnowledgeExtraction(entities=entities, relationships=relationships, claims=claims)


def parse_questions_json(raw: str) -> list[str]:
    """Parse {"questions": ["...", ...]} -> cleaned question strings."""
    obj = _extract_object(raw)
    items = obj.get("questions") if isinstance(obj, dict) else None
    if not isinstance(items, list):
        return []
    return [str(q).strip() for q in items if str(q).strip()]


# Common brand-variant normalization (belt-and-suspenders; the LLM does most of it).
_BRAND_ALIASES = {
    "chevy": "Chevrolet",
    "chevrolet": "Chevrolet",
    "ram": "Ram",
    "mercedes": "Mercedes-Benz",
    "mercedes benz": "Mercedes-Benz",
    "mercedes-benz": "Mercedes-Benz",
    "vw": "Volkswagen",
    "volkswagen": "Volkswagen",
    "gm": "GM",
    "range rover": "Land Rover",
    "land rover": "Land Rover",
}


def parse_brands_json(raw: str) -> list[str]:
    """Parse {"brands": ["Tesla", ...]} -> normalized, deduped brand names."""
    obj = _extract_object(raw)
    items = obj.get("brands") if isinstance(obj, dict) else None
    if not isinstance(items, list):
        return []
    seen, out = set(), []
    for b in items:
        name = str(b).strip()
        if not name:
            continue
        name = _BRAND_ALIASES.get(name.lower(), name)
        key = name.lower()
        if key not in seen:
            seen.add(key)
            out.append(name)
    return out


def _extract_object(raw: str):
    raw = raw.strip()
    start, end = raw.find("{"), raw.rfind("}")
    if start != -1 and end > start:
        try:
            return json.loads(raw[start : end + 1])
        except json.JSONDecodeError:
            return None
    return None


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
