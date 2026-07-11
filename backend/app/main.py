"""marketG backend — FastAPI entry point (Sprint 1: ingestion).

Run with:  uvicorn app.main:app --reload
"""
from __future__ import annotations

import json
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import analyze, crawl, organizations, probe, recommendations, sources, twin, visibility
from app.config import settings
from app.db import close_pool, get_pool


@asynccontextmanager
async def lifespan(_: FastAPI):
    await get_pool()  # warm the connection pool
    yield
    await close_pool()


app = FastAPI(
    title="marketG API",
    version="0.1.0",
    summary="Generative Engine Optimization platform — ingestion (Sprint 1)",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in settings.cors_origins.split(",") if o.strip()],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(organizations.router)
app.include_router(sources.router)
app.include_router(crawl.router)
app.include_router(twin.router)
app.include_router(visibility.router)
app.include_router(probe.router)
app.include_router(recommendations.router)
app.include_router(analyze.router)


@app.get("/health", tags=["meta"])
async def health() -> dict:
    """Liveness + DB connectivity."""
    try:
        pool = await get_pool()
        one = await pool.fetchval("select 1")
        db_ok = one == 1
    except Exception as exc:  # noqa: BLE001
        return {"status": "degraded", "db": False, "error": str(exc)}
    return {"status": "ok", "db": db_ok}
