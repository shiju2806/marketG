from app.pipeline.normalizer import normalize_html

HTML = """
<html><head><title>Testarossa Motors</title></head>
<body>
  <nav>Home Menu Shop</nav>
  <script>var x = 1;</script>
  <main>
    <h1>TX1</h1>
    <p>Range 410 miles. 1025 horsepower.</p>
    <h2>Security</h2>
    <p>SOC 2 Type II certified and GDPR compliant.</p>
  </main>
  <footer>Copyright 2026</footer>
</body></html>
"""


def test_extracts_title_and_sections():
    doc = normalize_html(HTML)
    assert doc.title == "Testarossa Motors"
    headings = [s.heading for s in doc.sections]
    assert "TX1" in headings
    assert "Security" in headings


def test_strips_chrome_and_scripts():
    doc = normalize_html(HTML)
    blob = " ".join(s.text for s in doc.sections)
    assert "var x" not in blob          # script removed
    assert "Copyright" not in blob      # footer removed
    assert "Menu" not in blob           # nav removed
    assert "410 miles" in blob          # real content kept


def test_section_text_grouped_under_heading():
    doc = normalize_html(HTML)
    sec = next(s for s in doc.sections if s.heading == "Security")
    assert "SOC 2" in sec.text
