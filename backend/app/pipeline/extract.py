"""Extraction orchestrator (Sprint 2 + 3).

Per crawled document: download -> normalize -> concept chunk -> embed (pgvector)
+ FTS -> extract knowledge (entities + relationships + claims) -> govern
(resolve, confidence, conflicts) -> persist into the Semantic Business Twin.

"LLM proposes, twin decides" (KIPS §25): the provider proposes; governance +
writer decide what enters the twin, with evidence and versioning.
"""
from __future__ import annotations

import asyncio

import asyncpg

from app.config import settings
from app.llm.base import TokenUsage
from app.llm.factory import get_embedding_provider, get_llm_provider
from app.pipeline.chunker import chunk_sections
from app.pipeline.normalizer import normalize_html
from app.storage import download_raw
from app.twin import governance, writer
from app.verticals.registry import get_vertical_pack


def _vector_literal(vec: list[float]) -> str:
    return "[" + ",".join(f"{x:.6f}" for x in vec) + "]"


async def process_document(pool: asyncpg.Pool, document: asyncpg.Record) -> dict:
    if not document["object_storage_key"]:
        return {"skipped": "no object_storage_key"}

    pack_id = await pool.fetchval(
        "select vertical_pack_id from organization where organization_id=$1",
        document["organization_id"],
    )
    pack = get_vertical_pack(pack_id or "automotive")
    html = await download_raw(document["object_storage_key"])

    normalized = normalize_html(html)
    chunks = chunk_sections(normalized.sections, pack, document["page_classification"])
    if not chunks:
        return {"chunks": 0, "entities": 0, "relationships": 0, "claims": 0}

    embedder = get_embedding_provider()
    llm = get_llm_provider()
    usage = TokenUsage()
    page_class = document["page_classification"]
    model_version = f"{settings.llm_provider}:{settings.openai_llm_model}"

    vectors, embed_usage = await embedder.embed([c.text for c in chunks])
    usage = usage + embed_usage

    # Extract knowledge from all chunks CONCURRENTLY (bounded) — these independent LLM
    # calls were the main bottleneck when run sequentially. DB writes stay ordered below.
    sem = asyncio.Semaphore(settings.extract_concurrency)

    async def _extract(chunk):
        text_in = f"{chunk.heading}. {chunk.text}"[: settings.extract_max_chars_per_chunk]
        async with sem:
            return await llm.extract_knowledge(text_in, pack)

    knowledge_results = await asyncio.gather(*[_extract(c) for c in chunks])
    knowledges = []
    for kn, k_usage in knowledge_results:
        knowledges.append(kn)
        usage = usage + k_usage

    counters = {"chunks": len(chunks), "entities": 0, "relationships": 0, "claims": 0, "conflicts": 0}

    async with pool.acquire() as conn:
        async with conn.transaction():
            await conn.execute("delete from chunk where document_id=$1", document["document_id"])

            # Existing resolved entity names (for fuzzy dedup, D-03).
            existing = await conn.fetch(
                "select entity_type, canonical_name from entity where organization_id=$1 and status='resolved'",
                document["organization_id"],
            )
            names_by_type: dict[str, list[str]] = {}
            for r in existing:
                names_by_type.setdefault(r["entity_type"], []).append(r["canonical_name"])

            name_to_id: dict[str, str] = {}

            async def resolve_entity(raw_name: str, entity_type: str, conf: float) -> str | None:
                if not raw_name:
                    return None
                canonical = governance.canonicalize(raw_name, entity_type, pack)
                pool_names = names_by_type.setdefault(entity_type, [])
                match = governance.fuzzy_match(canonical, pool_names)
                canonical = match or canonical
                if canonical not in pool_names:
                    pool_names.append(canonical)
                key = (entity_type, raw_name.lower())
                if key in name_to_id:
                    return name_to_id[key]
                entity_id = await writer.upsert_entity(
                    conn, document["account_id"], document["organization_id"],
                    entity_type, canonical, governance.overall_confidence(conf, page_class),
                )
                name_to_id[key] = entity_id
                name_to_id[(entity_type, canonical.lower())] = entity_id
                counters["entities"] += 1
                return entity_id

            for chunk, vector, knowledge in zip(chunks, vectors, knowledges):
                chunk_id = await conn.fetchval(
                    """
                    insert into chunk (account_id, organization_id, document_id, chunk_index,
                                       chunk_type, heading, text, token_estimate, embedding)
                    values ($1,$2,$3,$4,$5,$6,$7,$8,$9::vector) returning chunk_id
                    """,
                    document["account_id"], document["organization_id"], document["document_id"],
                    chunk.index, chunk.chunk_type, chunk.heading, chunk.text,
                    chunk.token_estimate, _vector_literal(vector),
                )

                evidence_id = await writer.write_evidence(
                    conn, document["account_id"], document["organization_id"],
                    document_id=document["document_id"], chunk_id=chunk_id,
                    source_url=document["url"], text_span=chunk.text,
                    page_classification=page_class, model_version=model_version,
                )

                # Entities (+ provenance link).
                type_lookup: dict[str, str] = {}
                for ent in knowledge.entities:
                    entity_id = await resolve_entity(ent.name, ent.entity_type, ent.confidence)
                    if entity_id:
                        type_lookup[ent.name.lower()] = ent.entity_type
                        await conn.execute(
                            "insert into chunk_entity (chunk_id, entity_id, account_id) "
                            "values ($1,$2,$3) on conflict do nothing",
                            chunk_id, entity_id, document["account_id"],
                        )

                # Relationships (only between entities we resolved).
                for rel in knowledge.relationships:
                    subj = name_to_id.get((type_lookup.get(rel.subject.lower(), ""), rel.subject.lower()))
                    obj = name_to_id.get((type_lookup.get(rel.object.lower(), ""), rel.object.lower()))
                    if subj and obj and subj != obj:
                        await writer.write_relationship(
                            conn, document["account_id"], document["organization_id"],
                            subject_id=subj, predicate=rel.predicate, object_id=obj,
                            evidence_id=evidence_id,
                            confidence=governance.overall_confidence(rel.confidence, page_class),
                        )
                        counters["relationships"] += 1

                # Claims (subject may be an entity or free text).
                for claim in knowledge.claims:
                    subj_id = name_to_id.get(
                        (type_lookup.get(claim.subject.lower(), ""), claim.subject.lower())
                    )
                    result = await writer.write_claim(
                        conn, document["account_id"], document["organization_id"],
                        subject_entity_id=subj_id, subject_text=None if subj_id else claim.subject,
                        predicate=claim.predicate, object_=claim.object, value=claim.value,
                        claim_type=claim.claim_type, evidence_id=evidence_id,
                        confidence=governance.overall_confidence(claim.confidence, page_class),
                    )
                    if result["action"] in ("inserted", "conflict"):
                        counters["claims"] += 1
                    if result["action"] == "conflict":
                        counters["conflicts"] += 1

    counters.update(
        tokens=usage.tokens, cost_usd=usage.cost_usd,
        embedding_provider=settings.embedding_provider, llm_provider=settings.llm_provider,
    )
    return counters
