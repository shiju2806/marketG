from app.crawler.classifier import classify_page


def test_homepage():
    assert classify_page("https://www.rivian.com/") == "homepage"
    assert classify_page("https://www.rivian.com") == "homepage"


def test_url_rules():
    assert classify_page("https://x.com/pricing") == "pricing"
    assert classify_page("https://x.com/security/overview") == "security"
    assert classify_page("https://x.com/integrations") == "integration"
    assert classify_page("https://x.com/docs/api") == "documentation"
    assert classify_page("https://x.com/blog/why-geo") == "blog"
    assert classify_page("https://x.com/careers") == "careers"


def test_product_paths():
    assert classify_page("https://www.rivian.com/r1t") == "product"
    assert classify_page("https://www.rivian.com/models/r1s") == "product"


def test_text_fallback_detects_product():
    # URL gives no hint, but spec-heavy text does.
    text = "Range 410 miles. 1025 horsepower. Towing capacity and 0-60 in 2.9s."
    assert classify_page("https://x.com/xyz", text) == "product"


def test_unknown_is_other():
    assert classify_page("https://x.com/random-thing") == "other"
