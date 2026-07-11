"""AI Visibility run orchestrator (internal engine).

Generate questions -> hybrid retrieve + graph-reason per question -> score ->
aggregate -> persist a run with its explainable per-question breakdown.
"""
from __future__ import annotations

from statistics import mean

from app.visibility import scoring
from app.visibility.questions import generate_questions
from app.visibility.retrieval import hybrid_search


async def _machine_readability(pool, organization_id) -> float:
    docs = await pool.fetch(
        "select http_status, has_schema_org, ai_crawler_policy from document where organization_id=$1",
        organization_id,
    )
    return scoring.machine_readability_signal([dict(d) for d in docs])


async def _target_signals(pool, target_entity_id) -> tuple[float, float]:
    if not target_entity_id:
        return 0.2, 0.3
    row = await pool.fetchrow(
        """
        select (select count(*) from relationship where subject_entity_id=$1 and valid_to is null) as rels,
               (select count(*) from claim where subject_entity_id=$1 and valid_to is null and status='active') as claims,
               (select coalesce(avg(confidence),0) from claim where subject_entity_id=$1 and valid_to is null and status='active') as avgconf
        """,
        target_entity_id,
    )
    return (
        scoring.reasoning_signal(row["rels"], row["claims"]),
        scoring.trust_signal(float(row["avgconf"]) if row["avgconf"] else None),
    )


async def run_visibility(pool, account_id, organization_id) -> dict:
    questions = await generate_questions(pool, organization_id)
    mr = await _machine_readability(pool, organization_id)

    per_q = []
    for q in questions:
        hits = await hybrid_search(pool, organization_id, q.text)
        r_sig = scoring.retrieval_signal(hits)
        reason_sig, trust_sig = await _target_signals(pool, q.target_entity_id)
        per_q.append((q, r_sig, reason_sig, trust_sig, hits))

    retrieval = mean(p[1] for p in per_q) if per_q else 0.0
    reasoning = mean(p[2] for p in per_q) if per_q else 0.0
    trust = mean(p[3] for p in per_q) if per_q else 0.0

    scores = {
        "retrieval": scoring.to_score(retrieval),
        "reasoning": scoring.to_score(reasoning),
        "trust": scoring.to_score(trust),
        "machine_readability": scoring.to_score(mr),
        "overall": scoring.overall(retrieval, reasoning, trust, mr),
        "question_count": len(per_q),
    }

    async with pool.acquire() as conn:
        async with conn.transaction():
            run_id = await conn.fetchval(
                """
                insert into visibility_run (account_id, organization_id, retrieval, reasoning,
                    trust, machine_readability, overall, question_count)
                values ($1,$2,$3,$4,$5,$6,$7,$8) returning run_id
                """,
                account_id, organization_id, scores["retrieval"], scores["reasoning"],
                scores["trust"], scores["machine_readability"], scores["overall"], scores["question_count"],
            )
            for q, r_sig, reason_sig, trust_sig, hits in per_q:
                await conn.execute(
                    """
                    insert into visibility_question (run_id, account_id, organization_id, question,
                        intent, retrieval, reasoning, trust, matched)
                    values ($1,$2,$3,$4,$5,$6,$7,$8,$9::jsonb)
                    """,
                    run_id, account_id, organization_id, q.text, q.intent,
                    r_sig, reason_sig, trust_sig,
                    {"top_chunks": hits[:3], "target_entity_id": q.target_entity_id},
                )

    return {"run_id": str(run_id), "scores": scores}
