from app.probe.analysis import analyze_answer


def test_detects_org_mention_and_competitors():
    a = analyze_answer(
        "The Rivian R1S is great, though the Tesla Model Y and Ford F-150 are alternatives.",
        cited_sources=[],
        org_names=["Rivian"],
        competitor_names=["Tesla", "Ford", "Lucid"],
        org_website="https://www.rivian.com",
    )
    assert a["organization_mentioned"] is True
    assert a["competitor_mentions"] == ["Ford", "Tesla"]
    assert a["organization_cited"] is False


def test_absent_org_is_not_mentioned():
    a = analyze_answer(
        "The best options are Toyota and Honda.",
        cited_sources=[],
        org_names=["Rivian"],
        competitor_names=["Toyota"],
        org_website="https://www.rivian.com",
    )
    assert a["organization_mentioned"] is False
    assert a["competitor_mentions"] == ["Toyota"]


def test_first_vs_third_party_citations():
    a = analyze_answer(
        "See details.",
        cited_sources=[
            "https://www.rivian.com/r1s",
            "https://www.edmunds.com/rivian/r1s/",
            "https://cars.usnews.com/x",
        ],
        org_names=["Rivian"],
        competitor_names=[],
        org_website="https://www.rivian.com",
    )
    assert a["first_party"] == 1        # rivian.com
    assert a["third_party"] == 2        # edmunds, usnews
    assert a["organization_cited"] is True
