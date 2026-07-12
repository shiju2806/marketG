"""Vertical Pack contract (ADR-006).

A vertical is data/config, not code: entity types, chunk-type hints, an ontology
seed, extraction hints, and (later) claim types + buyer-question templates. The
core pipeline is vertical-agnostic and simply loads the pack named by an
organization's `vertical_pack_id`. Adding an industry = authoring a pack, never
changing core schema.
"""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class VerticalPack:
    pack_id: str
    # Entity types this vertical cares about (open vocabulary — hints, not a schema enum).
    entity_types: tuple[str, ...]
    # Seed vocabulary: lower-cased term -> (entity_type, canonical_name). Used by the
    # mock extractor and as an ontology starting point (D-04).
    ontology_seed: dict[str, tuple[str, str]] = field(default_factory=dict)
    # Heading/keyword -> chunk_type hints for concept-based chunking.
    chunk_type_hints: dict[str, str] = field(default_factory=dict)
    # A natural-language instruction fragment injected into the extraction prompt.
    extraction_hint: str = ""
    # Branded buyer-question templates (AVAS §3.3). Placeholders: {vehicle} {competitor} {brand}.
    # Used by the INTERNAL engine (can our twin answer about our own products?).
    question_templates: tuple[tuple[str, str], ...] = ()
    # Category / UNBRANDED questions for the external probe (D-07): measure whether
    # AI names the brand *unprompted* vs competitors. No brand/vehicle placeholders.
    category_questions: tuple[str, ...] = ()
