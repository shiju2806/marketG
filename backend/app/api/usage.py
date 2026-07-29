"""Usage & cost API (D-05) — budget-aware infra as a customer-facing feature.

Aggregates real LLM spend (job.metrics from full analyses + probe run costs) per
account/org, so continuous GEO monitoring has predictable, visible cost.
"""
from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Query

from app.api.deps import require_account
from app.config import settings
from app.db import get_pool

router = APIRouter(prefix="/api/v1", tags=["usage"])


async def account_spend(pool, account_id) -> float:
    """Total LLM spend for an account (analyze jobs already fold in probe cost)."""
    total = await pool.fetchval(
        "select coalesce(sum((metrics->>'cost_usd')::float),0) from job "
        "where account_id=$1 and type='analyze' and metrics ? 'cost_usd'",
        account_id,
    )
    return round(float(total or 0.0), 6)


@router.get("/usage")
async def usage(organization_id: UUID | None = Query(None), account_id: UUID = Depends(require_account)):
    pool = await get_pool()
    runs = await pool.fetch(
        """
        select j.job_id, j.organization_id, o.name, j.metrics, j.created_at
          from job j left join organization o on o.organization_id=j.organization_id
         where j.account_id=$1 and j.type='analyze' and j.metrics ? 'cost_usd'
           and ($2::uuid is null or j.organization_id=$2)
         order by j.created_at desc limit 30
        """,
        account_id, organization_id,
    )
    total = round(sum(float((r["metrics"] or {}).get("cost_usd", 0) or 0) for r in runs), 6)
    tokens = sum(int((r["metrics"] or {}).get("tokens", 0) or 0) for r in runs)
    return {
        "total_cost_usd": total,
        "total_tokens": tokens,
        "budget_usd": settings.account_budget_usd or None,
        "runs": [
            {
                "organization": r["name"],
                "cost_usd": (r["metrics"] or {}).get("cost_usd", 0),
                "tokens": (r["metrics"] or {}).get("tokens", 0),
                "pages": (r["metrics"] or {}).get("pages", 0),
                "pages_skipped": (r["metrics"] or {}).get("pages_skipped", 0),
                "at": r["created_at"].isoformat(),
            }
            for r in runs
        ],
    }
