"""Async Postgres connection pool (asyncpg).

The backend connects directly to Postgres with the service role, so RLS is
bypassed for pipeline work. Client-facing access goes through Supabase with a
JWT and is governed by the RLS policies in migration 0003.
"""
from __future__ import annotations

import json

import asyncpg

from app.config import settings

_pool: asyncpg.Pool | None = None


async def _init_connection(conn: asyncpg.Connection) -> None:
    # Round-trip json/jsonb as Python objects instead of raw strings.
    for typ in ("json", "jsonb"):
        await conn.set_type_codec(
            typ, encoder=json.dumps, decoder=json.loads, schema="pg_catalog"
        )


async def get_pool() -> asyncpg.Pool:
    global _pool
    if _pool is None:
        _pool = await asyncpg.create_pool(
            settings.database_url,
            min_size=1,
            max_size=10,
            command_timeout=60,
            init=_init_connection,
        )
    return _pool


async def close_pool() -> None:
    global _pool
    if _pool is not None:
        await _pool.close()
        _pool = None
