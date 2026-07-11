"""Knowledge governance (SBTS §12-15, KIPS §17) — pure decision logic.

Turns raw extraction into *trusted* knowledge: source authority, multi-dimensional
confidence, entity-name canonicalization + fuzzy resolution (D-03), and conflict
detection. Kept side-effect-free so it's unit-testable; the writer applies it.
"""
from __future__ import annotations

from difflib import SequenceMatcher

from app.verticals.base import VerticalPack

# How authoritative a page class is as evidence (SBTS §13 evidence dimension).
_AUTHORITY = {
    "security": 0.95,
    "documentation": 0.95,
    "pricing": 0.90,
    "product": 0.85,
    "integration": 0.85,
    "spec": 0.90,
    "homepage": 0.70,
    "case_study": 0.65,
    "about": 0.60,
    "blog": 0.50,
}


def source_authority(page_classification: str | None) -> float:
    return _AUTHORITY.get((page_classification or "").lower(), 0.55)


def overall_confidence(
    extraction_confidence: float, page_classification: str | None, freshness: float = 1.0
) -> float:
    """Blend extraction (0.5), evidence authority (0.3), freshness (0.2) — SBTS §13."""
    ext = max(0.0, min(1.0, extraction_confidence))
    auth = source_authority(page_classification)
    fresh = max(0.0, min(1.0, freshness))
    return round(0.5 * ext + 0.3 * auth + 0.2 * fresh, 2)


def canonicalize(name: str, entity_type: str, pack: VerticalPack) -> str:
    """Map a raw name to its canonical form via the ontology seed (D-04)."""
    seed = pack.ontology_seed.get(name.strip().lower())
    if seed and seed[0] == entity_type:
        return seed[1]
    return " ".join(name.split()).strip()


def fuzzy_match(name: str, existing: list[str], threshold: float = 0.9) -> str | None:
    """Return an existing name that is a near-duplicate of `name` (D-03)."""
    target = name.lower()
    best, best_ratio = None, 0.0
    for candidate in existing:
        ratio = SequenceMatcher(None, target, candidate.lower()).ratio()
        if ratio > best_ratio:
            best, best_ratio = candidate, ratio
    return best if best_ratio >= threshold else None


def claims_conflict(a: dict, b: dict) -> bool:
    """Two current claims conflict if same subject+predicate+type but different value/object."""
    same_target = (
        a["subject"] == b["subject"]
        and a["predicate"] == b["predicate"]
        and a.get("claim_type") == b.get("claim_type")
    )
    if not same_target:
        return False
    return (a.get("value", ""), a.get("object", "")) != (b.get("value", ""), b.get("object", ""))
