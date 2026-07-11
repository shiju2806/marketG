"""Object storage for immutable raw documents (Supabase Storage, S3-compatible).

Raw crawled HTML is written once and never modified (DATABASE_DESIGN §7). Keys:
    {account_id}/{source_id}/{content_hash}.html
"""
from __future__ import annotations

import httpx

from app.config import settings


def raw_key(account_id: str, source_id: str, content_hash: str) -> str:
    return f"{account_id}/{source_id}/{content_hash}.html"


def _auth_headers(extra: dict | None = None) -> dict:
    # Supabase's gateway wants both apikey and Authorization; without apikey some
    # endpoints return 400 instead of the correct status (e.g. 409 on duplicate).
    headers = {
        "Authorization": f"Bearer {settings.supabase_service_role_key}",
        "apikey": settings.supabase_service_role_key,
    }
    if extra:
        headers.update(extra)
    return headers


async def upload_raw(key: str, html: str) -> str:
    """Upload rendered HTML to the raw-documents bucket. Idempotent (upsert)."""
    url = f"{settings.supabase_url}/storage/v1/object/{settings.storage_bucket}/{key}"
    headers = _auth_headers({"Content-Type": "text/html", "x-upsert": "true"})
    async with httpx.AsyncClient() as client:
        resp = await client.post(url, content=html.encode("utf-8"), headers=headers, timeout=30.0)
        resp.raise_for_status()
    return key


async def download_raw(key: str) -> str:
    """Fetch a previously stored raw document (rendered HTML) by key."""
    url = f"{settings.supabase_url}/storage/v1/object/{settings.storage_bucket}/{key}"
    async with httpx.AsyncClient() as client:
        resp = await client.get(url, headers=_auth_headers(), timeout=30.0)
        resp.raise_for_status()
        return resp.text


async def ensure_bucket() -> None:
    """Create the raw-documents bucket if it doesn't exist (idempotent, dev helper)."""
    url = f"{settings.supabase_url}/storage/v1/bucket"
    headers = _auth_headers({"Content-Type": "application/json"})
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            url,
            json={"name": settings.storage_bucket, "id": settings.storage_bucket, "public": False},
            headers=headers,
            timeout=15.0,
        )
        # 200 created; 409 already exists; some gateways report a duplicate as 400.
        if resp.status_code in (200, 409):
            return
        if resp.status_code == 400 and (
            "exist" in resp.text.lower() or "duplicate" in resp.text.lower()
        ):
            return
        resp.raise_for_status()
