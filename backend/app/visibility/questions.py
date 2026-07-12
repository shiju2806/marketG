"""Buyer-question generation (AVAS §3.3).

Generate a representative set of questions the organization *should* be findable
for, from the twin (its vehicles + competitors) crossed with the vertical pack's
templates (ADR-006). Each question carries the target entity so the reasoning /
trust signals can be computed against the twin.
"""
from __future__ import annotations

from dataclasses import dataclass

from app.verticals.registry import get_vertical_pack


@dataclass
class Question:
    text: str
    intent: str
    target_entity_id: str | None


async def generate_questions(pool, organization_id, limit: int = 12) -> list[Question]:
    org = await pool.fetchrow(
        "select name, vertical_pack_id from organization where organization_id=$1", organization_id
    )
    pack = get_vertical_pack(org["vertical_pack_id"] if org else "automotive")
    brand = org["name"] if org else "the brand"

    vehicles = await pool.fetch(
        "select entity_id, canonical_name from entity "
        "where organization_id=$1 and entity_type='Vehicle' and status='resolved' "
        "order by confidence desc nulls last limit 5",
        organization_id,
    )
    competitors = await pool.fetch(
        "select canonical_name from entity "
        "where organization_id=$1 and entity_type='Competitor' and status='resolved' limit 3",
        organization_id,
    )
    competitor = competitors[0]["canonical_name"] if competitors else "the leading rival"

    questions: list[Question] = []
    for template, intent in pack.question_templates:
        if "{vehicle}" in template:
            for v in vehicles:
                questions.append(
                    Question(
                        text=template.format(vehicle=v["canonical_name"], competitor=competitor, brand=brand),
                        intent=intent,
                        target_entity_id=str(v["entity_id"]),
                    )
                )
        else:
            questions.append(
                Question(text=template.format(brand=brand, competitor=competitor), intent=intent,
                         target_entity_id=None)
            )
    return questions[:limit]


async def generate_category_questions(pool, organization_id, limit: int = 8) -> list[Question]:
    """Unbranded category questions for the external probe (D-07).

    Generated DYNAMICALLY from the company's actual market (LLM), so they fit the
    business — never the brand name (a mention must be *unprompted*). Falls back to
    the vertical pack's static list if the LLM is unavailable (keyless/error).
    """
    from app.llm.factory import get_llm_provider

    org = await pool.fetchrow(
        "select name, website, vertical_pack_id from organization where organization_id=$1",
        organization_id,
    )
    pack = get_vertical_pack(org["vertical_pack_id"] if org else "automotive")

    # A short description of what the company does, from the crawled homepage/text.
    description = await pool.fetchval(
        """
        select c.text from chunk c join document d on d.document_id = c.document_id
         where c.organization_id = $1
         order by (d.page_classification = 'homepage') desc, c.token_estimate desc
         limit 1
        """,
        organization_id,
    ) or ""

    context = (
        f"Company: {org['name']} ({org['website']}). Industry: {pack.pack_id}.\n"
        f"What they do: {description[:500] or '(unknown — infer from the company name and industry)'}"
    )

    questions: list[str] = []
    try:
        questions, _ = await get_llm_provider().generate_category_questions(context, limit)
    except Exception:  # noqa: BLE001 - fall back to the static pack list
        questions = []
    if not questions:
        questions = list(pack.category_questions)

    return [Question(text=q, intent="citation", target_entity_id=None) for q in questions][:limit]
