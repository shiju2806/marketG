"""Multi-hop reasoning over the twin — the queryable knowledge asset.

A point-tool checklist can't answer "can you support multinational families?" —
that needs traversing the graph (entity → relationships → claims) and synthesizing.
This is what makes the twin a *product*, not a report.
"""
from __future__ import annotations

from app.llm.factory import get_llm_provider
from app.visibility.retrieval import graph_expand, hybrid_search

_SYSTEM = (
    "Answer the question about the company using ONLY the provided facts from its "
    "knowledge graph. Be concise and specific. If the facts don't support an answer, "
    'say so plainly. Respond as JSON: {"answer": "...", "supported": true/false}.'
)


async def reason(pool, organization_id, question: str) -> dict:
    # 1) find the most relevant content, 2) resolve its entities,
    # 3) expand the graph around them, 4) gather claims, 5) synthesize.
    hits = await hybrid_search(pool, organization_id, question, k=4)
    chunk_ids = [h["chunk_id"] for h in hits]

    entities = await pool.fetch(
        """
        select distinct e.entity_id, e.canonical_name, e.entity_type
          from chunk_entity ce join entity e on e.entity_id = ce.entity_id
         where ce.chunk_id = any($1::uuid[]) and e.organization_id = $2
        """,
        chunk_ids, organization_id,
    ) if chunk_ids else []

    facts: list[str] = []
    for e in entities[:5]:
        claims = await pool.fetch(
            "select predicate, value, object from claim where subject_entity_id=$1 and valid_to is null "
            "and status='active' limit 12",
            e["entity_id"],
        )
        for c in claims:
            facts.append(f"{e['canonical_name']} {c['predicate']} {c['value'] or c['object'] or ''}".strip())
        for hop in await graph_expand(pool, e["entity_id"], max_hops=2):
            facts.append(f"{e['canonical_name']} {hop['predicate']} {hop['object']}")

    # Also pull the raw retrieved text as supporting context.
    texts = await pool.fetch(
        "select text from chunk where chunk_id = any($1::uuid[]) limit 4", chunk_ids
    ) if chunk_ids else []
    context = "\n".join(f"- {f}" for f in facts[:40]) or "(no structured facts)"
    snippets = "\n".join(t["text"][:400] for t in texts)

    user = f"Question: {question}\n\nKnowledge-graph facts:\n{context}\n\nPage context:\n{snippets}"
    try:
        obj, _ = await get_llm_provider().complete_json(_SYSTEM, user)
    except Exception:  # noqa: BLE001
        obj = {}
    return {
        "question": question,
        "answer": obj.get("answer") if isinstance(obj, dict) else None,
        "supported": bool(obj.get("supported")) if isinstance(obj, dict) else False,
        "facts_used": facts[:12],
    }
