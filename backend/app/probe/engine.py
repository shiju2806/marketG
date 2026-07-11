"""External AI Probe orchestrator (HRRE §13).

Ask each keyed target the buyer questions, analyze answers, persist results, then
fold the Citation score + earned-vs-owned back onto the org's latest visibility run.
"""
from __future__ import annotations

import time
from statistics import mean

from app.config import settings
from app.probe.analysis import analyze_answer
from app.probe.factory import available_targets
from app.visibility.questions import generate_questions
from app.visibility.scoring import to_score


async def run_probe(pool, account_id, organization_id, *, requested_targets=None, samples=None) -> dict:
    samples = samples or settings.probe_samples
    org = await pool.fetchrow(
        "select name, website from organization where organization_id=$1", organization_id
    )
    org_names = [org["name"]] if org else []
    competitors = [
        r["canonical_name"]
        for r in await pool.fetch(
            "select canonical_name from entity where organization_id=$1 and entity_type='Competitor' "
            "and status='resolved'",
            organization_id,
        )
    ]
    targets = available_targets(requested_targets)
    questions = await generate_questions(pool, organization_id)

    probe_run_id = await pool.fetchval(
        """
        insert into probe_run (account_id, organization_id, targets, question_count,
            samples_per_question, status)
        values ($1,$2,$3,$4,$5,'running') returning probe_run_id
        """,
        account_id, organization_id, [t.name for t in targets], len(questions), samples,
    )

    mention_flags: list[float] = []
    first_total, third_total = 0, 0
    total_cost = 0.0

    for q in questions:
        for target in targets:
            for sample in range(1, samples + 1):
                started = time.perf_counter()
                try:
                    ans = await target.ask(q.text)
                except Exception as exc:  # noqa: BLE001 - record the failure, keep going
                    await _record_error(pool, probe_run_id, account_id, organization_id, q.text,
                                        target.name, sample, str(exc))
                    continue
                latency_ms = int((time.perf_counter() - started) * 1000)
                a = analyze_answer(
                    ans.text, ans.cited_sources,
                    org_names=org_names, competitor_names=competitors, org_website=org["website"],
                )
                mention_flags.append(1.0 if a["organization_mentioned"] else 0.0)
                first_total += a["first_party"]
                third_total += a["third_party"]
                total_cost += ans.cost_usd

                await pool.execute(
                    """
                    insert into probe_result (probe_run_id, account_id, organization_id, question,
                        model, sample, answer, organization_mentioned, organization_cited,
                        competitor_mentions, claim_consistency, cited_sources, first_party,
                        third_party, latency_ms, tokens, cost_usd)
                    values ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12::jsonb,$13,$14,$15,$16,$17)
                    """,
                    probe_run_id, account_id, organization_id, q.text, target.name, sample,
                    ans.text[:4000], a["organization_mentioned"], a["organization_cited"],
                    a["competitor_mentions"], a["claim_consistency"], ans.cited_sources,
                    a["first_party"], a["third_party"], latency_ms, ans.tokens, round(ans.cost_usd, 4),
                )

    citation_signal = mean(mention_flags) if mention_flags else 0.0
    citation_score = to_score(citation_signal)
    earned_owned = round(first_total / (first_total + third_total), 2) if (first_total + third_total) else None

    await pool.execute(
        """
        update probe_run set status='done', citation=$2, earned_owned=$3, metrics=$4::jsonb
         where probe_run_id=$1
        """,
        probe_run_id, citation_score, earned_owned,
        {"cost_usd": round(total_cost, 6), "targets_ran": [t.name for t in targets],
         "results": len(mention_flags)},
    )

    updated = await _apply_citation_to_visibility(pool, organization_id, citation_score)

    return {
        "probe_run_id": str(probe_run_id),
        "targets_ran": [t.name for t in targets],
        "citation": citation_score,
        "earned_owned": earned_owned,
        "results": len(mention_flags),
        "visibility_overall": updated,
    }


async def _record_error(pool, probe_run_id, account_id, organization_id, question, model, sample, err):
    await pool.execute(
        """
        insert into probe_result (probe_run_id, account_id, organization_id, question, model,
            sample, answer, claim_consistency)
        values ($1,$2,$3,$4,$5,$6,$7,'unknown')
        """,
        probe_run_id, account_id, organization_id, question, model, sample, f"ERROR: {err}",
    )


async def _apply_citation_to_visibility(pool, organization_id, citation_score: int) -> int | None:
    """Write Citation onto the latest visibility run and recompute overall over all 5 dims."""
    run = await pool.fetchrow(
        "select run_id, retrieval, reasoning, trust, machine_readability from visibility_run "
        "where organization_id=$1 order by created_at desc limit 1",
        organization_id,
    )
    if run is None:
        return None
    dims = [run["retrieval"], run["reasoning"], run["trust"], run["machine_readability"], citation_score]
    present = [d for d in dims if d is not None]
    overall = int(round(mean(present))) if present else None
    await pool.execute(
        "update visibility_run set citation=$2, overall=$3 where run_id=$1",
        run["run_id"], citation_score, overall,
    )
    return overall
