from app.twin import governance as g
from app.verticals.automotive import AUTOMOTIVE


def test_source_authority_ranks_pages():
    assert g.source_authority("security") > g.source_authority("blog")
    assert g.source_authority("unknown-thing") == 0.55


def test_overall_confidence_blends_dimensions():
    strong = g.overall_confidence(1.0, "security")
    weak = g.overall_confidence(1.0, "blog")
    assert strong > weak                 # same extraction, better source -> higher
    assert 0.0 <= weak <= strong <= 1.0


def test_canonicalize_uses_ontology_seed():
    assert g.canonicalize("soc2", "Regulation", AUTOMOTIVE) == "SOC 2"
    assert g.canonicalize("  Some   Brand ", "Vehicle", AUTOMOTIVE) == "Some Brand"


def test_fuzzy_match_dedups_near_duplicates():
    assert g.fuzzy_match("Super Cruise", ["super cruise"]) == "super cruise"
    assert g.fuzzy_match("Rivian R1S", ["Ford F-150"]) is None


def test_claims_conflict_detects_value_difference():
    a = {"subject": "TX1", "predicate": "price", "claim_type": "pricing", "value": "$99", "object": ""}
    b = {"subject": "TX1", "predicate": "price", "claim_type": "pricing", "value": "$149", "object": ""}
    same = {**a}
    assert g.claims_conflict(a, b) is True
    assert g.claims_conflict(a, same) is False
