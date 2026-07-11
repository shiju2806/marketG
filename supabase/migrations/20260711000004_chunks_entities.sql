-- marketG — Sprint 2 schema: semantic chunks + candidate entities
-- Chunks carry embeddings (pgvector) and full-text (tsvector) for hybrid
-- retrieval later (HRRE). Entities are OPEN-VOCABULARY (ADR-006) candidates;
-- resolution/dedup into the twin is Sprint 3 (D-03).

create extension if not exists vector;

-- A concept-based chunk (KIPS §10): the retrieval unit, not a fixed token window.
create table if not exists chunk (
    chunk_id         uuid primary key default gen_random_uuid(),
    account_id       uuid not null references account(account_id) on delete cascade,
    organization_id  uuid not null references organization(organization_id) on delete cascade,
    document_id      uuid not null references document(document_id) on delete cascade,
    chunk_index      int  not null,
    chunk_type       text,          -- open vocabulary (spec / security_compliance / ...)
    heading          text,
    text             text not null,
    token_estimate   int,
    embedding        vector(1536),  -- text-embedding-3-small dim (config: EMBED_DIM)
    tsv              tsvector generated always as (to_tsvector('english', coalesce(text, ''))) stored,
    created_at       timestamptz not null default now(),
    unique (document_id, chunk_index)
);

create index if not exists idx_chunk_account  on chunk (account_id);
create index if not exists idx_chunk_document on chunk (document_id);
create index if not exists idx_chunk_tsv      on chunk using gin (tsv);
-- HNSW builds fine on an empty table and needs no training data (unlike ivfflat).
create index if not exists idx_chunk_embedding on chunk using hnsw (embedding vector_cosine_ops);

-- Candidate entities extracted from chunks. entity_type is an OPEN vocabulary
-- (ADR-006) — never a DB enum — so new verticals add types as data.
create table if not exists entity (
    entity_id        uuid primary key default gen_random_uuid(),
    account_id       uuid not null references account(account_id) on delete cascade,
    organization_id  uuid not null references organization(organization_id) on delete cascade,
    entity_type      text not null,
    canonical_name   text not null,
    aliases          text[] not null default '{}',
    attributes       jsonb  not null default '{}'::jsonb,
    confidence       numeric(3, 2),
    status           text not null default 'candidate'
                       check (status in ('candidate', 'resolved', 'rejected')),
    source           text not null default 'extraction',
    created_at       timestamptz not null default now()
);

-- Light idempotency for re-extraction; full entity resolution is Sprint 3 (D-03).
create unique index if not exists uq_entity_natural
    on entity (organization_id, entity_type, lower(canonical_name));
create index if not exists idx_entity_account on entity (account_id);
create index if not exists idx_entity_org_type on entity (organization_id, entity_type);

-- Which chunk mentioned which entity (provenance link).
create table if not exists chunk_entity (
    chunk_id    uuid not null references chunk(chunk_id) on delete cascade,
    entity_id   uuid not null references entity(entity_id) on delete cascade,
    account_id  uuid not null references account(account_id) on delete cascade,
    primary key (chunk_id, entity_id)
);
create index if not exists idx_chunk_entity_account on chunk_entity (account_id);

-- RLS (ADR-001/007): isolate the new tables by account_id.
alter table chunk        enable row level security;
alter table entity       enable row level security;
alter table chunk_entity enable row level security;

do $$
declare t text;
begin
    foreach t in array array['chunk', 'entity', 'chunk_entity']
    loop
        execute format('drop policy if exists %I_isolation on %I;', t, t);
        execute format(
            'create policy %I_isolation on %I '
            'using (account_id = current_account_id()) '
            'with check (account_id = current_account_id());',
            t, t
        );
    end loop;
end
$$;
