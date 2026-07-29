from app.probe.sources import _classify, domain_of


def test_domain_of():
    assert domain_of("https://www.caranddriver.com/x") == "caranddriver.com"
    assert domain_of("reddit.com/r/rivian") == "reddit.com"


def test_classify_categories():
    comp = {"tesla.com", "ford.com"}
    assert _classify("rivian.com", is_first_party=True, competitor_domains=comp) == "own"
    assert _classify("reddit.com", is_first_party=False, competitor_domains=comp) == "social"
    assert _classify("youtu.be", is_first_party=False, competitor_domains=comp) == "social"
    assert _classify("tesla.com", is_first_party=False, competitor_domains=comp) == "competitor"
    assert _classify("caranddriver.com", is_first_party=False, competitor_domains=comp) == "editorial"


def test_own_wins_over_social():
    # first-party always classifies as own even if it were somehow in social set
    assert _classify("reddit.com", is_first_party=True, competitor_domains=set()) == "own"
