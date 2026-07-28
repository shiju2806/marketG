"""Twin API (SBTS §18) — read the Semantic Business Twin.

Applications consume the twin only through these endpoints, never the DB directly
(SAD §17). Read-only in the MVP.
"""
from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query

from pydantic import BaseModel

from app.api.deps import require_account
from app.db import get_pool
from app.twin.reason import reason

router = APIRouter(prefix="/api/v1", tags=["twin"])


class ReasonRequest(BaseModel):
    question: str


@router.get("/conflicts")
async def conflicts(organization_id: UUID = Query(...), account_id: UUID = Depends(require_account)):
    """Contradictions in the twin — claims AI could repeat either way (SBTS §15)."""
    pool = await get_pool()
    rows = await pool.fetch(
        """
        select cf.conflict_id, cf.description, cf.resolution_status,
               a.predicate, a.value as a_value, a.object as a_object,
               b.value as b_value, b.object as b_object
          from conflict cf
          join claim a on a.claim_id = cf.object_a_id
          join claim b on b.claim_id = cf.object_b_id
         where cf.organization_id=$1 and cf.account_id=$2 and cf.resolution_status='pending_review'
         order by cf.created_at desc
        """,
        organization_id, account_id,
    )
    return [dict(r) for r in rows]


@router.post("/reason")
async def reason_endpoint(
    body: ReasonRequest, organization_id: UUID = Query(...), account_id: UUID = Depends(require_account)
):
    """Ask a multi-hop question over the twin (the queryable knowledge asset)."""
    pool = await get_pool()
    org = await pool.fetchrow(
        "select organization_id from organization where organization_id=$1 and account_id=$2",
        organization_id, account_id,
    )
    if org is None:
        raise HTTPException(status_code=404, detail="organization not found")
    return await reason(pool, organization_id, body.question)


@router.get("/twin-diff")
async def twin_diff(organization_id: UUID = Query(...), account_id: UUID = Depends(require_account)):
    """What changed in the twin recently — added claims and superseded (updated) ones."""
    pool = await get_pool()
    added = await pool.fetch(
        """
        select coalesce(e.canonical_name, c.subject_text) subj, c.predicate,
               coalesce(c.value, c.object) as val, c.created_at
          from claim c left join entity e on e.entity_id=c.subject_entity_id
         where c.organization_id=$1 and c.valid_to is null and c.status='active'
         order by c.created_at desc limit 10
        """,
        organization_id,
    )
    superseded = await pool.fetch(
        """
        select coalesce(e.canonical_name, c.subject_text) subj, c.predicate,
               coalesce(c.value, c.object) as val
          from claim c left join entity e on e.entity_id=c.subject_entity_id
         where c.organization_id=$1 and c.status='superseded'
         order by c.valid_to desc nulls last limit 10
        """,
        organization_id,
    )
    return {"added": [dict(r) for r in added], "superseded": [dict(r) for r in superseded]}


@router.get("/semantic-twin")
async def semantic_twin(organization_id: UUID = Query(...), account_id: UUID = Depends(require_account)):
    pool = await get_pool()
    org = await pool.fetchrow(
        "select organization_id from organization where organization_id=$1 and account_id=$2",
        organization_id, account_id,
    )
    if org is None:
        raise HTTPException(status_code=404, detail="organization not found")

    async def count(table: str, extra: str = "") -> int:
        return await pool.fetchval(
            f"select count(*) from {table} where organization_id=$1 {extra}", organization_id
        )

    return {
        "organization_id": str(organization_id),
        "entities": await count("entity", "and status='resolved'"),
        "relationships": await count("relationship", "and valid_to is null"),
        "claims": await count("claim", "and valid_to is null and status='active'"),
        "evidence": await count("evidence"),
        "conflicts": await count("conflict", "and resolution_status='pending_review'"),
        "entities_by_type": [
            dict(r) for r in await pool.fetch(
                "select entity_type, count(*) as n from entity "
                "where organization_id=$1 and status='resolved' group by entity_type order by n desc",
                organization_id,
            )
        ],
    }


@router.get("/entities")
async def list_entities(
    organization_id: UUID = Query(...),
    entity_type: str | None = Query(None),
    account_id: UUID = Depends(require_account),
):
    pool = await get_pool()
    rows = await pool.fetch(
        """
        select entity_id, entity_type, canonical_name, confidence
          from entity
         where organization_id=$1 and account_id=$2 and status='resolved'
           and ($3::text is null or entity_type=$3)
         order by confidence desc nulls last, canonical_name
        """,
        organization_id, account_id, entity_type,
    )
    return [dict(r) for r in rows]


@router.get("/entities/{entity_id}")
async def get_entity(entity_id: UUID, account_id: UUID = Depends(require_account)):
    pool = await get_pool()
    entity = await pool.fetchrow(
        "select * from entity where entity_id=$1 and account_id=$2", entity_id, account_id
    )
    if entity is None:
        raise HTTPException(status_code=404, detail="entity not found")

    relationships = await pool.fetch(
        """
        select r.predicate, r.confidence, e.canonical_name as object, e.entity_type as object_type
          from relationship r join entity e on e.entity_id = r.object_entity_id
         where r.subject_entity_id=$1 and r.valid_to is null
         order by r.confidence desc nulls last
        """,
        entity_id,
    )
    claims = await pool.fetch(
        """
        select claim_id, predicate, object, value, claim_type, confidence
          from claim
         where subject_entity_id=$1 and valid_to is null and status='active'
         order by confidence desc nulls last
        """,
        entity_id,
    )
    return {
        "entity": dict(entity),
        "relationships": [dict(r) for r in relationships],
        "claims": [dict(c) for c in claims],
    }


@router.get("/claims/{claim_id}")
async def get_claim(claim_id: UUID, account_id: UUID = Depends(require_account)):
    pool = await get_pool()
    claim = await pool.fetchrow(
        "select * from claim where claim_id=$1 and account_id=$2", claim_id, account_id
    )
    if claim is None:
        raise HTTPException(status_code=404, detail="claim not found")
    evidence = None
    if claim["evidence_id"]:
        evidence = await pool.fetchrow(
            "select evidence_id, source_url, text_span, page_classification, model_version "
            "from evidence where evidence_id=$1",
            claim["evidence_id"],
        )
    return {"claim": dict(claim), "evidence": dict(evidence) if evidence else None}
