"""Remediation generator — turn a diagnosed gap into a ready-to-use fix.

Given a recommendation (which carries the delta cell in its `source`), produce a
publish-ready artifact grounded in the org's own twin content + the competitors AI
cites. "Measure → diagnose → REMEDIATE" — the move from analyst to platform.

The LLM proposes the content; we shape it into a stable artifact. Grounded ONLY in
known facts (the twin), so it doesn't invent specs.
"""
from __future__ import annotations

import json

from app.llm.factory import get_llm_provider

_SYSTEM = (
    "You are a GEO (Generative Engine Optimization) content strategist. Produce "
    "publish-ready web content that AI assistants will readily cite: answer-first, "
    "factual, well-structured (clear H2/H3, bullet facts, a short FAQ). Ground it "
    "ONLY in the provided facts about the company — never invent specs, prices, or "
    "claims. Respond as JSON with keys: title, body_markdown, body_html, "
    "schema_jsonld (a schema.org object), notes (1-2 sentences on why this improves "
    "AI visibility)."
)


def _shape_artifact(raw: dict, gap_type: str, fallback_title: str) -> dict:
    """Normalize the LLM output into a stable artifact shape (pure, testable)."""
    raw = raw if isinstance(raw, dict) else {}
    schema = raw.get("schema_jsonld")
    if isinstance(schema, str):
        try:
            schema = json.loads(schema)
        except (ValueError, TypeError):
            schema = {}
    md = str(raw.get("body_markdown") or "").strip()
    html = str(raw.get("body_html") or "").strip()
    if not html and md:
        # Minimal fallback so an HTML export always exists.
        html = "<article>\n" + "\n".join(f"<p>{ln}</p>" for ln in md.splitlines() if ln.strip()) + "\n</article>"
    return {
        "title": str(raw.get("title") or fallback_title).strip(),
        "gap_type": gap_type,
        "body_markdown": md,
        "body_html": html,
        "schema_jsonld": schema if isinstance(schema, dict) else {},
        "notes": str(raw.get("notes") or "").strip(),
    }


async def _existing_page_content(pool, organization_id, url: str) -> str:
    rows = await pool.fetch(
        """
        select c.text from chunk c join document d on d.document_id = c.document_id
         where c.organization_id = $1 and d.url = $2
         order by c.chunk_index limit 20
        """,
        organization_id, url,
    )
    return "\n\n".join(r["text"] for r in rows)[:6000]


async def generate_fix(pool, organization_id, recommendation: dict) -> dict:
    org = await pool.fetchrow(
        "select name, website from organization where organization_id=$1", organization_id
    )
    company = org["name"] if org else "the company"
    source = recommendation.get("source") or {}
    if isinstance(source, str):
        try:
            source = json.loads(source)
        except (ValueError, TypeError):
            source = {}
    gap_type = recommendation.get("missing_type") or source.get("quadrant") or "content"
    question = source.get("question") or recommendation.get("title", "")
    competitors = ", ".join(source.get("competitors", [])[:5]) or "competitors"

    # Facts we can ground on: the org's known claims (the twin).
    claims = await pool.fetch(
        """
        select coalesce(e.canonical_name, c.subject_text) subj, c.predicate, c.value, c.object
          from claim c left join entity e on e.entity_id = c.subject_entity_id
         where c.organization_id = $1 and c.valid_to is null and c.status='active'
         order by c.confidence desc nulls last limit 30
        """,
        organization_id,
    )
    facts = "\n".join(
        f"- {r['subj']} {r['predicate']} {r['value'] or r['object'] or ''}".strip() for r in claims
    ) or "(no extracted facts — keep content general and accurate)"

    if gap_type in ("hidden", "citation") and (source.get("evidence") or {}).get("url"):
        existing = await _existing_page_content(pool, organization_id, source["evidence"]["url"])
        instruction = (
            f"REWRITE the company's existing page below so AI assistants can extract and cite it "
            f"for the buyer question: \"{question}\". AI currently recommends {competitors} instead. "
            f"Keep it truthful to the facts; add structure, direct answers, a fact table, an FAQ, and "
            f"schema.org markup.\n\nEXISTING PAGE:\n{existing}"
        )
    else:
        instruction = (
            f"DRAFT a new authoritative page for {company} targeting the buyer question: "
            f"\"{question}\". AI currently recommends {competitors} and not {company}. Use the "
            f"company's known facts; write answer-first with headings, a fact table, and an FAQ, "
            f"plus schema.org markup."
        )

    user = f"Company: {company} ({org['website'] if org else ''}).\nKnown facts:\n{facts}\n\n{instruction}"

    try:
        raw, _ = await get_llm_provider().complete_json(_SYSTEM, user)
    except Exception:  # noqa: BLE001 - fall back to an empty shell the user can edit
        raw = {}
    return _shape_artifact(raw, gap_type, fallback_title=f"Content for: {question}")
