from app.pipeline.chunker import chunk_sections
from app.pipeline.normalizer import Section
from app.verticals.automotive import AUTOMOTIVE


def test_concept_type_from_heading_hint():
    sections = [
        Section("Security", "We are SOC 2 Type II certified and GDPR compliant for the platform."),
        Section("Pricing", "The TX1 starts at $54,900 MSRP with financing options available."),
    ]
    chunks = chunk_sections(sections, AUTOMOTIVE, page_classification="homepage")
    by_heading = {c.heading: c.chunk_type for c in chunks}
    assert by_heading["Security"] == "security_compliance"
    assert by_heading["Pricing"] == "pricing"


def test_falls_back_to_page_classification():
    sections = [Section("Welcome", "A generic paragraph about the company and its mission today.")]
    chunks = chunk_sections(sections, AUTOMOTIVE, page_classification="about")
    assert chunks[0].chunk_type == "about"


def test_long_section_is_split():
    long_text = " ".join(f"Sentence number {i} about the vehicle." for i in range(400))
    chunks = chunk_sections([Section("Specs", long_text)], AUTOMOTIVE)
    assert len(chunks) > 1
    assert all(len(c.text) <= 2400 for c in chunks)


def test_indices_are_sequential():
    sections = [Section("A", "first section text here that is long enough to keep."),
                Section("B", "second section text here that is long enough to keep.")]
    chunks = chunk_sections(sections, AUTOMOTIVE)
    assert [c.index for c in chunks] == list(range(len(chunks)))
