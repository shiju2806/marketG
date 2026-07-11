"""Extraction orchestrator (Sprint 2).

For one crawled document: download raw HTML -> normalize -> concept chunk ->
embed (pgvector) -> persist chunks (+ FTS via generated tsv) -> extract candidate
entities -> persist entities + chunk links. Idempotent: rebuilds a document's
chunks each run. Records tokens/cost for D-05.

Entities are *candidates* here; resolution/dedup into the twin is Sprint 3.
"""
from __future__ import annotations

import asyncpg

from app.config import settings
from app.llm.base import TokenUsage
from app.llm.factory import get_embedding_provider, get_llm_provider
from app.pipeline.chunker import chunk_sections
from app.pipeline.normalizer import normalize_html
from app.storage import download_raw
from app.verticals.registry import get_vertical_pack


def _vector_literal(vec: list[float]) -> str:
    return "[" + ",".join(f"{x:.6f}" for x in vec) + "]"


async def process_document(pool: asyncpg.Pool, document: asyncpg.Record) -> dict:
    if not document["object_storage_key"]:
        return {"skipped": "no object_storage_key"}

    pack = await _pack_for_org(pool, document["organization_id"])
    html = await download_raw(document["object_storage_key"])

    normalized = normalize_html(html)
    chunks = chunk_sections(normalized.sections, pack, document["page_classification"])
    if not chunks:
        return {"chunks": 0, "entities": 0}

    embedder = get_embedding_provider()
    llm = get_llm_provider()
    usage = TokenUsage()

    vectors, embed_usage = await embedder.embed([c.text for c in chunks])
    usage = usage + embed_usage

    async with pool.acquire() as conn:
        async with conn.transaction():
            # Idempotent rebuild for this document.
            await conn.execute("delete from chunk where document_id=$1", document["document_id"])

            entity_ids: dict[tuple[str, str], str] = {}
            n_entities = 0
            for chunk, vector in zip(chunks, vectors):
                chunk_id = await conn.fetchval(
                    """
                    insert into chunk (account_id, organization_id, document_id, chunk_index,
                                       chunk_type, heading, text, token_estimate, embedding)
                    values ($1,$2,$3,$4,$5,$6,$7,$8,$9::vector)
                    returning chunk_id
                    """,
                    document["account_id"],
                    document["organization_id"],
                    document["document_id"],
                    chunk.index,
                    chunk.chunk_type,
                    chunk.heading,
                    chunk.text,
                    chunk.token_estimate,
                    _vector_literal(vector),
                )

                text_for_llm = chunk.text[: settings.extract_max_chars_per_chunk]
                entities, ent_usage = await llm.extract_entities(text_for_llm, pack)
                usage = usage + ent_usage

                for ent in entities:
                    key = (ent.entity_type, ent.name.lower())
                    entity_id = entity_ids.get(key)
                    if entity_id is None:
                        entity_id = await conn.fetchval(
                            """
                            insert into entity (account_id, organization_id, entity_type,
                                                canonical_name, confidence, attributes)
                            values ($1,$2,$3,$4,$5,$6::jsonb)
                            on conflict (organization_id, entity_type, lower(canonical_name))
                            do update set confidence = greatest(entity.confidence, excluded.confidence)
                            returning entity_id
                            """,
                            document["account_id"],
                            document["organization_id"],
                            ent.entity_type,
                            ent.name,
                            round(ent.confidence, 2),
                            ent.attributes,
                        )
                        entity_ids[key] = entity_id
                        n_entities += 1

                    await conn.execute(
                        """
                        insert into chunk_entity (chunk_id, entity_id, account_id)
                        values ($1,$2,$3) on conflict do nothing
                        """,
                        chunk_id,
                        entity_id,
                        document["account_id"],
                    )

    return {
        "chunks": len(chunks),
        "entities": n_entities,
        "tokens": usage.tokens,
        "cost_usd": usage.cost_usd,
        "embedding_provider": settings.embedding_provider,
        "llm_provider": settings.llm_provider,
    }


async def _pack_for_org(pool: asyncpg.Pool, organization_id) -> object:
    pack_id = await pool.fetchval(
        "select vertical_pack_id from organization where organization_id=$1", organization_id
    )
    return get_vertical_pack(pack_id or "automotive")
