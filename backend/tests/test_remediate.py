from app.remediate.generator import _shape_artifact


def test_shapes_full_artifact():
    raw = {
        "title": "Best EV for towing",
        "body_markdown": "# Towing\nThe R1T tows 11,000 lbs.",
        "body_html": "<h1>Towing</h1>",
        "schema_jsonld": {"@type": "FAQPage"},
        "notes": "Adds a citable towing page.",
    }
    a = _shape_artifact(raw, "missing", "fallback")
    assert a["title"] == "Best EV for towing"
    assert a["gap_type"] == "missing"
    assert a["schema_jsonld"] == {"@type": "FAQPage"}
    assert a["notes"]


def test_parses_stringified_schema_and_synthesizes_html():
    raw = {"body_markdown": "Line one\nLine two", "schema_jsonld": '{"@type":"Vehicle"}'}
    a = _shape_artifact(raw, "hidden", "fallback title")
    assert a["schema_jsonld"] == {"@type": "Vehicle"}   # parsed from string
    assert "<p>Line one</p>" in a["body_html"]           # synthesized from markdown
    assert a["title"] == "fallback title"                # fell back


def test_tolerates_garbage():
    a = _shape_artifact("not a dict", "missing", "fb")
    assert a["title"] == "fb"
    assert a["schema_jsonld"] == {}
    assert a["body_markdown"] == ""
