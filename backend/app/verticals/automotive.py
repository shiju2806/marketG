"""Automotive vertical pack (ADR-002 / ADR-006) — the beachhead vertical.

First instance of a VerticalPack. Everything here is data; the core pipeline
doesn't import automotive concepts directly.
"""
from __future__ import annotations

from app.verticals.base import VerticalPack

AUTOMOTIVE = VerticalPack(
    pack_id="automotive",
    entity_types=(
        "Vehicle",
        "Technology",
        "Feature",
        "Integration",
        "Industry",
        "Competitor",
        "Award",
        "Regulation",
    ),
    # Seed terms the extractor can recognize with high confidence. Grows over time.
    ontology_seed={
        "super cruise": ("Technology", "Super Cruise"),
        "ultium": ("Technology", "Ultium"),
        "nacs": ("Technology", "NACS"),
        "carplay": ("Integration", "Apple CarPlay"),
        "android auto": ("Integration", "Android Auto"),
        "soc 2": ("Regulation", "SOC 2"),
        "soc2": ("Regulation", "SOC 2"),
        "gdpr": ("Regulation", "GDPR"),
        "iihs": ("Award", "IIHS Top Safety Pick"),
        "epa": ("Regulation", "EPA"),
        "tesla": ("Competitor", "Tesla"),
        "ford": ("Competitor", "Ford"),
        "rivian": ("Competitor", "Rivian"),
        "lucid": ("Competitor", "Lucid"),
        "workday": ("Competitor", "Workday"),
    },
    chunk_type_hints={
        "pricing": "pricing",
        "price": "pricing",
        "security": "security_compliance",
        "compliance": "security_compliance",
        "integration": "integration_capability",
        "spec": "spec",
        "range": "spec",
        "horsepower": "spec",
        "towing": "spec",
        "safety": "safety",
        "warranty": "warranty",
        "charging": "charging",
    },
    extraction_hint=(
        "This is an automotive brand's website. Prioritize vehicle models, their "
        "specs (range, horsepower, towing, price), technologies, integrations, "
        "safety awards, and named competitors."
    ),
)
