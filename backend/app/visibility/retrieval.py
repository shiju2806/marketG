"""Hybrid retrieval (HRRE §3-6): BM25/FTS + vector + graph expansion.

Lexical (Postgres tsvector) catches exact terms; vector (pgvector cosine) catches
meaning; the two are score-fused. Graph expansion pulls connected claims/relationships
for a matched entity — the step that separates this from plain RAG. Graph traversal
is a recursive CTE in Postgres (Neo4j deferred).
"""
from __future__ import annotations

from app.llm.factory import get_embedding_provider


def _vector_literal(vec: list[float]) -> str:
    return "[" + ",".join(f"{x:.6f}" for x in vec) + "]"


async def hybrid_search(pool, organization_id, query: str, k: int = 5) -> list[dict]:
    """Return up to k chunk hits with a fused score in [0,1]."""
    embedder = get_embedding_provider()
    qvec, _ = await embedder.embed([query])
    lit = _vector_literal(qvec[0])

    rows = await pool.fetch(
        """
        with vec as (
            select chunk_id, 1 - (embedding <=> $2::vector) as cos
              from chunk
             where organization_id = $1 and embedding is not null
             order by embedding <=> $2::vector
             limit $3
        ),
        fts as (
            select chunk_id, ts_rank(tsv, plainto_tsquery('english', $4)) as rank
              from chunk
             where organization_id = $1 and tsv @@ plainto_tsquery('english', $4)
             order by rank desc
             limit $3
        )
        select c.chunk_id, c.chunk_type, c.heading,
               coalesce(v.cos, 0)  as cos,
               coalesce(f.rank, 0) as rank
          from chunk c
          left join vec v on v.chunk_id = c.chunk_id
          left join fts f on f.chunk_id = c.chunk_id
         where c.organization_id = $1 and (v.chunk_id is not null or f.chunk_id is not null)
        """,
        organization_id, lit, k, query,
    )

    hits = []
    for r in rows:
        cos = max(0.0, float(r["cos"]))
        rank = min(1.0, float(r["rank"]) * 10.0)  # ts_rank is small; scale into [0,1]
        hits.append(
            {
                "chunk_id": str(r["chunk_id"]),
                "chunk_type": r["chunk_type"],
                "heading": r["heading"],
                "score": round(0.6 * cos + 0.4 * rank, 4),
            }
        )
    hits.sort(key=lambda h: h["score"], reverse=True)
    return hits[:k]


async def graph_expand(pool, entity_id, max_hops: int = 2) -> list[dict]:
    """Bounded multi-hop expansion over the twin's current relationships (HRRE §6)."""
    rows = await pool.fetch(
        """
        with recursive walk(subject_entity_id, object_entity_id, predicate, depth) as (
            select subject_entity_id, object_entity_id, predicate, 1
              from relationship
             where subject_entity_id = $1 and valid_to is null
            union all
            select r.subject_entity_id, r.object_entity_id, r.predicate, w.depth + 1
              from relationship r
              join walk w on r.subject_entity_id = w.object_entity_id
             where r.valid_to is null and w.depth < $2
        )
        select w.predicate, w.depth, e.canonical_name as object, e.entity_type as object_type
          from walk w join entity e on e.entity_id = w.object_entity_id
         order by w.depth
        """,
        entity_id, max_hops,
    )
    return [dict(r) for r in rows]
