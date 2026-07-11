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

    # CORS — allow the local dashboard (Vite dev server) to call the API.
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"

    # LLM / embeddings (TECH_STACK seams). Default to the keyless mock so the
    # pipeline runs locally without provider credentials or internet.
    llm_provider: str = "mock"            # mock | anthropic | openai
    embedding_provider: str = "mock"      # mock | openai
    embed_dim: int = 1536                 # must match chunk.embedding vector(N)
    openai_api_key: str = ""
    anthropic_api_key: str = ""
    perplexity_api_key: str = ""
    openai_embed_model: str = "text-embedding-3-small"
    openai_llm_model: str = "gpt-4o-mini"
    openai_probe_model: str = "gpt-4o-mini"  # browsing probe via Responses API web_search
    anthropic_model: str = "claude-sonnet-5"
    perplexity_model: str = "sonar"

    # External AI probe (Sprint 4b, HRRE §13).
    probe_targets: str = "chatgpt,claude,perplexity"  # requested; only keyed ones run
    probe_samples: int = 1

    # Chunking / extraction limits (D-05 cost control: cap work per unit).
    chunk_max_chars: int = 2400           # split a section beyond this
    chunk_min_chars: int = 60             # drop trivial fragments
    extract_max_chars_per_chunk: int = 6000  # truncate LLM input per chunk


settings = Settings()
