"""Shared API dependencies.

Sprint 1 resolves the caller's account from an `X-Account-Id` header. This is a
deliberate placeholder: when Supabase Auth is wired, the account comes from the
verified JWT (`app_metadata.account_id`) — the same value RLS uses — and this
dependency is the single place that changes. Every query is scoped by the
returned account_id (ADR-001/007: no cross-account access).
"""
from __future__ import annotations

from uuid import UUID

from fastapi import Header, HTTPException


async def require_account(x_account_id: str = Header(...)) -> UUID:
    try:
        return UUID(x_account_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="X-Account-Id must be a UUID") from exc
