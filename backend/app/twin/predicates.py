"""Predicate normalization (unblocks D-06).

The LLM phrases the same relation/claim inconsistently ("has range", "range",
"hasRange", "has"), so contradiction detection and relationship dedup miss real
matches. Canonicalize predicates to a stable form so "TX1 has range 410" and
"TX1 range 502" are recognized as the *same* assertion (and thus a conflict).
"""
from __future__ import annotations

import re

# Auxiliary/filler words dropped from the front of a predicate.
_FILLERS = {
    "has", "have", "had", "is", "are", "was", "were", "can", "could", "will",
    "offers", "offer", "provides", "provide", "with", "the", "a", "an", "its",
    "their", "comes", "featuring", "includes", "include",
}

# Known synonym collapses (domain-flavored but harmless generally).
_ALIASES = {
    "driving_range": "range", "epa_range": "range", "estimated_range": "range",
    "max_range": "range",
    "tow": "towing_capacity", "towing": "towing_capacity", "tows": "towing_capacity",
    "hp": "horsepower", "power": "horsepower",
    "starts_at": "price", "msrp": "price", "pricing": "price", "cost": "price",
    "starting_price": "price", "priced_at": "price",
    "zero_sixty": "acceleration", "0_60": "acceleration", "0_to_60": "acceleration",
}


def canonicalize_predicate(predicate: str) -> str:
    if not predicate:
        return ""
    # split camelCase, then normalize separators/case/punctuation
    s = re.sub(r"([a-z0-9])([A-Z])", r"\1 \2", predicate)
    s = re.sub(r"[_\-/]", " ", s).lower()
    s = re.sub(r"[^a-z0-9 ]", "", s)
    tokens = [t for t in s.split() if t]
    # Strip filler words only from the FRONT — "has range" -> "range", but keep
    # trailing particles like "integrates with" / "competes with".
    kept = tokens[:]
    while kept and kept[0] in _FILLERS:
        kept.pop(0)
    if not kept:
        kept = tokens  # never collapse to empty (e.g. bare "has")
    key = "_".join(kept)
    return _ALIASES.get(key, key)
