"""Competitive analysis: WHY competitors get recommended and what to do.

Reads the latest probe answers (real AI output) and asks the LLM to explain what
the winning brands offer that the org doesn't, plus prioritized actions. This is
the "what competitors do better" the report needs — grounded in actual answers.
"""
from __future__ import annotations

from app.llm.factory import get_llm_provider

_SYSTEM = (
    "You are a GEO (Generative Engine Optimization) analyst. Given how AI assistants "
    "answered category buyer questions, explain concisely why the leading brands get "
    "recommended and the target company does not, then give prioritized actions. "
    'Respond as JSON: {"summary": "2-3 sentences on why competitors win", '
    '"actions": ["3-5 short, specific, prioritized actions"]}.'
)


async def competitive_summary(pool, organization_id) -> dict:
    org = await pool.fetchrow("select name from organization where organization_id=$1", organization_id)
    company = org["name"] if org else "the company"

    run = await pool.fetchrow(
        "select probe_run_id, metrics from probe_run where organization_id=$1 and status='done' "
        "order by created_at desc limit 1",
        organization_id,
    )
    if run is None:
        return {"summary": None, "actions": [], "leaders": []}

    sov = (run["metrics"] or {}).get("share_of_voice", [])
    leaders = [s["brand"] for s in sov if not s["is_you"]][:5]

    # A few real gap examples: questions where the org was absent + what AI said.
    gaps = await pool.fetch(
        """
        select question, competitor_mentions, left(answer, 500) as answer
          from probe_result
         where probe_run_id=$1 and organization_mentioned = false
           and array_length(competitor_mentions, 1) > 0
         order by question limit 4
        """,
        run["probe_run_id"],
    )

    examples = "\n\n".join(
        f"Q: {g['question']}\nAI recommended: {', '.join(g['competitor_mentions'])}\nAI said: {g['answer']}"
        for g in gaps
    )
    user = (
        f"Target company: {company}. It is rarely named when buyers research its market.\n"
        f"Leading brands in AI answers: {', '.join(leaders) or 'various competitors'}.\n\n"
        f"Examples of what AI actually said:\n{examples or '(no examples)'}"
    )

    try:
        obj, _ = await get_llm_provider().complete_json(_SYSTEM, user)
    except Exception:  # noqa: BLE001 - fall back to a generic summary
        obj = {}

    summary = obj.get("summary") if isinstance(obj, dict) else None
    actions = obj.get("actions") if isinstance(obj, dict) else None
    if not summary:
        summary = (
            f"AI assistants recommend {', '.join(leaders[:3]) or 'competitors'} because they have "
            f"stronger, more citable content in these categories. {company} is largely absent from "
            "the sources AI draws on."
        )
    return {
        "summary": summary,
        "actions": actions if isinstance(actions, list) else [],
        "leaders": leaders,
    }
