import pytest

from app.llm.mock import MockEmbeddingProvider, MockLLMProvider
from app.verticals.automotive import AUTOMOTIVE


async def test_embedding_is_deterministic_and_dimensioned():
    provider = MockEmbeddingProvider(dim=1536)
    v1, usage = await provider.embed(["range 410 miles"])
    v2, _ = await provider.embed(["range 410 miles"])
    v3, _ = await provider.embed(["a totally different string"])
    assert len(v1[0]) == 1536
    assert v1[0] == v2[0]            # deterministic
    assert v1[0] != v3[0]            # content-sensitive
    assert usage.tokens > 0
    norm = sum(x * x for x in v1[0]) ** 0.5
    assert 0.99 <= norm <= 1.01     # normalized


async def test_seeded_terms_extracted_with_high_confidence():
    llm = MockLLMProvider()
    text = "The vehicle ships with Super Cruise and is SOC 2 certified. Alternative to Tesla."
    entities, usage = await llm.extract_entities(text, AUTOMOTIVE)
    by_name = {e.name: e for e in entities}
    assert by_name["Super Cruise"].entity_type == "Technology"
    assert by_name["Super Cruise"].confidence >= 0.9
    assert by_name["SOC 2"].entity_type == "Regulation"
    assert by_name["Tesla"].entity_type == "Competitor"
    assert usage.tokens > 0


async def test_vertical_fallback():
    from app.verticals.registry import get_vertical_pack

    assert get_vertical_pack("automotive").pack_id == "automotive"
    assert get_vertical_pack("does-not-exist").pack_id == "automotive"  # safe fallback
