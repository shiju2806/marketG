"""Central configuration. All values overridable via env / backend/.env."""
from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Storage of record
    database_url: str = "postgresql://postgres:postgres@127.0.0.1:54322/postgres"

    # Supabase API + object storage
    supabase_url: str = "http://127.0.0.1:54321"
    supabase_service_role_key: str = ""
    storage_bucket: str = "raw-documents"

    # Crawler (ADR-003 render-everything; ADR-007 bounded + polite)
    crawl_max_pages: int = 40
    crawl_max_depth: int = 2
    crawl_concurrency: int = 4
    crawl_timeout_ms: int = 20_000

    # Worker
    worker_id: str = "worker-1"
    worker_poll_seconds: float = 2.0


settings = Settings()
