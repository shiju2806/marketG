from app.recommend.builder import build_recommendations


def test_blocked_bots_and_citation_gaps_rank_high():
    recs = build_recommendations(
        blocked_bots=["GPTBot"],
        unstructured_page_share=0.8,
        citation_gaps=[{"question": "best electric SUV?", "competitors": ["Tesla", "Ford"]}],
        uncovered_vehicles=["R2"],
        low_trust_entities=[],
    )
    # high-impact recs come first
    assert recs[0]["expected_impact"] == "high"
    types = [r["missing_type"] for r in recs]
    assert "machine_readability" in types
    assert "citation" in types
    assert "coverage" in types
    # citation gap names the competitors
    cit = next(r for r in recs if r["missing_type"] == "citation")
    assert "Tesla" in cit["title"]
    assert cit["affects"] == ["citation"]


def test_no_gaps_yields_no_recs():
    recs = build_recommendations(
        blocked_bots=[], unstructured_page_share=0.0, citation_gaps=[],
        uncovered_vehicles=[], low_trust_entities=[],
    )
    assert recs == []


def test_low_unstructured_share_skips_schema_rec():
    recs = build_recommendations(
        blocked_bots=[], unstructured_page_share=0.2, citation_gaps=[],
        uncovered_vehicles=[], low_trust_entities=[],
    )
    assert all(r["missing_type"] != "machine_readability" for r in recs)
