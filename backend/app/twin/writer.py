"""Twin writer (SBTS §14 versioning, §15 conflicts).

Persists governed knowledge: resolved entities, evidence, versioned relationships,
and versioned claims with conflict detection. All writes are account-scoped and
idempotent within a transaction (the caller owns the connection).
"""
from __future__ import annotations

import asyncpg

from app.twin import governance


async def upsert_entity(
    conn, account_id, organization_id, entity_type: str, canonical_name: str, confidence: float
) -> str:
    return await conn.fetchval(
        """
        insert into entity (account_id, organization_id, entity_type, canonical_name,
                            confidence, status, source)
        values ($1,$2,$3,$4,$5,'resolved','extraction')
        on conflict (organization_id, entity_type, lower(canonical_name))
        do update set confidence = greatest(entity.confidence, excluded.confidence),
                      status = 'resolved'
        returning entity_id
        """,
        account_id, organization_id, entity_type, canonical_name, round(confidence, 2),
    )


async def write_evidence(
    conn, account_id, organization_id, *, document_id, chunk_id, source_url,
    text_span: str, page_classification, model_version: str
) -> str:
    return await conn.fetchval(
        """
        insert into evidence (account_id, organization_id, document_id, chunk_id,
                              source_url, text_span, page_classification, model_version)
        values ($1,$2,$3,$4,$5,$6,$7,$8)
        returning evidence_id
        """,
        account_id, organization_id, document_id, chunk_id, source_url,
        text_span[:600], page_classification, model_version,
    )


async def write_relationship(
    conn, account_id, organization_id, *, subject_id, predicate: str, object_id,
    evidence_id, confidence: float
) -> None:
    """Insert a current relationship, or bump confidence if it already exists."""
    await conn.execute(
        """
        insert into relationship (account_id, organization_id, subject_entity_id,
                                  predicate, object_entity_id, evidence_id, confidence)
        values ($1,$2,$3,$4,$5,$6,$7)
        on conflict (organization_id, subject_entity_id, predicate, object_entity_id)
            where valid_to is null
        do update set confidence = greatest(relationship.confidence, excluded.confidence),
                      evidence_id = coalesce(relationship.evidence_id, excluded.evidence_id)
        """,
        account_id, organization_id, subject_id, predicate, object_id, evidence_id,
        round(confidence, 2),
    )


async def write_claim(
    conn, account_id, organization_id, *, subject_entity_id, subject_text: str,
    predicate: str, object_: str, value: str, claim_type: str, evidence_id, confidence: float
) -> dict:
    """Insert a claim with versioning + conflict detection (SBTS §14/15).

    Returns {"action": "inserted"|"kept"|"conflict"}.
    """
    subject_key = str(subject_entity_id) if subject_entity_id else (subject_text or "")

    current = await conn.fetch(
        """
        select claim_id, object, value from claim
         where organization_id = $1 and predicate = $2 and claim_type = $3
           and coalesce(subject_entity_id::text, subject_text) = $4
           and valid_to is null and status = 'active'
        """,
        organization_id, predicate, claim_type, subject_key,
    )

    for row in current:
        if (row["object"] or "") == object_ and (row["value"] or "") == value:
            return {"action": "kept"}  # identical assertion already present

    async def _insert() -> str:
        return await conn.fetchval(
            """
            insert into claim (account_id, organization_id, subject_entity_id, subject_text,
                               predicate, object, value, claim_type, evidence_id, confidence)
            values ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10)
            returning claim_id
            """,
            account_id, organization_id, subject_entity_id, subject_text, predicate,
            object_, value, claim_type, evidence_id, round(confidence, 2),
        )

    if current:
        # Differing current assertion -> record a conflict (SBTS §15), keep both.
        new_id = await _insert()
        await conn.execute(
            """
            insert into conflict (account_id, organization_id, object_type, object_a_id,
                                  object_b_id, description)
            values ($1,$2,'claim',$3,$4,$5)
            """,
            account_id, organization_id, current[0]["claim_id"], new_id,
            f"Conflicting {claim_type} for {predicate}: "
            f"'{current[0]['value'] or current[0]['object']}' vs '{value or object_}'",
        )
        return {"action": "conflict"}

    await _insert()
    return {"action": "inserted"}
