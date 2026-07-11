-- marketG — Sprint 1 schema: sources, jobs, documents
-- ADR-003: crawler renders every page; documents carry machine-readability signals
-- ADR-004: machine-readability is captured per document (feeds scoring later)
-- ADR-007: jobs are idempotent + queue-driven (locking columns below)

-- A knowledge source for an organization. MVP: website only.
create table if not exists source (
    source_id        uuid primary key default gen_random_uuid(),
    account_id       uuid not null references account(account_id) on delete cascade,
    organization_id  uuid not null references organization(organization_id) on delete cascade,
    type             text not null default 'website',
    seed_url         text not null,
    status           text not null default 'registered'
                       check (status in ('registered', 'crawling', 'done', 'failed')),
    created_at       timestamptz not null default now()
);

create index if not exists idx_source_account on source (account_id);
create index if not exists idx_source_org     on source (organization_id);

-- Postgres-backed job queue. Claimed with FOR UPDATE SKIP LOCKED (ADR-007).
-- `type` is an open vocabulary (crawl | extract | probe | twin_update | ...).
create table if not exists job (
    job_id           uuid primary key default gen_random_uuid(),
    account_id       uuid not null references account(account_id) on delete cascade,
    organization_id  uuid references organization(organization_id) on delete cascade,
    source_id        uuid references source(source_id) on delete cascade,
    type             text not null,
    status           text not null default 'queued'
                       check (status in ('queued', 'running', 'done', 'failed')),
    stage            text,
    attempts         int  not null default 0,
    max_attempts     int  not null default 3,
    locked_at        timestamptz,
    locked_by        text,
    run_after        timestamptz not null default now(),
    payload          jsonb not null default '{}'::jsonb,
    metrics          jsonb not null default '{}'::jsonb,
    error            text,
    created_at       timestamptz not null default now(),
    updated_at       timestamptz not null default now()
);

create index if not exists idx_job_claim   on job (status, run_after);
create index if not exists idx_job_account on job (account_id);

-- One row per crawled page. Raw bytes live in object storage (object_storage_key).
-- Machine-readability signals (ADR-004) are captured here at crawl time.
create table if not exists document (
    document_id          uuid primary key default gen_random_uuid(),
    account_id           uuid not null references account(account_id) on delete cascade,
    organization_id      uuid not null references organization(organization_id) on delete cascade,
    source_id            uuid not null references source(source_id) on delete cascade,
    url                  text not null,
    page_classification  text,            -- open vocabulary (homepage/product/pricing/...)
    object_storage_key   text,
    content_hash         text,
    http_status          int,
    js_required          boolean,         -- was JS needed to render the content?
    has_schema_org       boolean,         -- schema.org / JSON-LD present?
    ai_crawler_policy    jsonb,           -- robots.txt stance on GPTBot/ClaudeBot/etc.
    crawled_at           timestamptz not null default now(),
    unique (source_id, url)               -- idempotent re-crawl (upsert by url)
);

create index if not exists idx_document_account on document (account_id);
create index if not exists idx_document_source  on document (source_id);
