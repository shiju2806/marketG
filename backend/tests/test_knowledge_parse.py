from app.llm.util import parse_knowledge_json


def test_parses_full_knowledge_object():
    raw = """{
      "entities": [{"name":"TX1","entity_type":"Vehicle","confidence":0.9}],
      "relationships": [{"subject":"TX1","predicate":"uses","object":"Super Cruise","confidence":0.8}],
      "claims": [{"subject":"TX1","predicate":"range","value":"410 miles","claim_type":"spec","confidence":0.85}]
    }"""
    k = parse_knowledge_json(raw)
    assert k.entities[0].name == "TX1"
    assert k.relationships[0].predicate == "uses"
    assert k.claims[0].value == "410 miles"
    assert k.claims[0].claim_type == "spec"


def test_filters_incomplete_records():
    raw = """{
      "entities": [{"entity_type":"Vehicle"}],
      "relationships": [{"subject":"TX1","predicate":"uses"}],
      "claims": [{"subject":"TX1"}]
    }"""
    k = parse_knowledge_json(raw)
    assert k.entities == []          # no name
    assert k.relationships == []     # no object
    assert k.claims == []            # no predicate


def test_handles_garbage():
    k = parse_knowledge_json("sorry, no JSON")
    assert (k.entities, k.relationships, k.claims) == ([], [], [])


def test_drops_junk_valueless_claims():
    # The exact "R1S has_feature None" problem — claims with no value AND no object.
    raw = """{
      "claims": [
        {"subject":"R1S","predicate":"has_feature","value":"None","claim_type":"spec"},
        {"subject":"R1S","predicate":"has_spec","value":"true"},
        {"subject":"R1S","predicate":"range","value":"410 miles","claim_type":"spec"},
        {"subject":"R1S","predicate":"integrates","object":"Apple CarPlay","claim_type":"capability"}
      ]
    }"""
    k = parse_knowledge_json(raw)
    kept = {(c.predicate, c.value or c.object) for c in k.claims}
    assert kept == {("range", "410 miles"), ("integrates", "Apple CarPlay")}  # junk dropped
