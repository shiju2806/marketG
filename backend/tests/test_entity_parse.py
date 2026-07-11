from app.llm.util import parse_entities_json


def test_parses_wrapped_object():
    raw = '{"entities":[{"name":"Super Cruise","entity_type":"Technology","confidence":0.9}]}'
    ents = parse_entities_json(raw)
    assert len(ents) == 1
    assert ents[0].name == "Super Cruise"
    assert ents[0].entity_type == "Technology"
    assert ents[0].confidence == 0.9


def test_parses_bare_array_with_prose_wrapper():
    raw = 'Here you go:\n[{"name":"Tesla","entity_type":"Competitor"}]\nThanks!'
    ents = parse_entities_json(raw)
    assert ents[0].name == "Tesla"
    assert ents[0].confidence == 0.6  # default when missing


def test_clamps_and_defaults_bad_confidence():
    raw = '{"entities":[{"name":"X","confidence":"not-a-number"},{"name":"Y","confidence":5}]}'
    ents = {e.name: e for e in parse_entities_json(raw)}
    assert ents["X"].confidence == 0.6   # default
    assert ents["Y"].confidence == 1.0   # clamped


def test_ignores_garbage_and_nameless():
    assert parse_entities_json("no json here") == []
    assert parse_entities_json('{"entities":[{"entity_type":"Technology"}]}') == []
