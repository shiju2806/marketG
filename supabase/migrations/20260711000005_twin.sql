-- marketG — Sprint 3 schema: the Semantic Business Twin
-- evidence, first-class relationships, claims (separate from entities, SBTS §4),
-- conflicts, and entity resolution. Versioned + governed (SBTS §12-15).
-- Graph lives in these relational tables (Neo4j deferred, TECH_STACK).

-- Entity resolution: merged duplicates point to their canonical entity.
alter table entity add column if not exists canonical_entity_id uuid
    references entity(entity_id) on delete set null;

-- Evidence: nothing enters the twin without a traceable source (SBTS Principle 2).
create table if not exists evidence (
    evidence_id          uuid primary key default gen_random_uuid(),
    account_id           uuid not null references account(account_id) on delete cascade,
    organization_id      uuid not null references organization(organization_id) on delete cascade,
    document_id          uuid references document(document_id) on delete set null,
    chunk_id             uuid references chunk(chunk_id) on delete set null,
    source_url           text,
    text_span            text,
    page_classification  text,
    model_version        text,
    extraction_date      timestamptz not null default now()
);
create index if not exists idx_evidence_account on evidence (account_id);
create index if not exists idx_evidence_org     on evidence (organization_id);

-- Relationships are first-class (SBTS §7), versioned; current = valid_to is null.
create table if not exists relationship (
    relationship_id    uuid primary key default gen_random_uuid(),
    account_id         uuid not null references account(account_id) on delete cascade,
    organization_id    uuid not null references organization(organization_id) on delete cascade,
    subject_entity_id  uuid not null references entity(entity_id) on delete cascade,
    predicate          text not null,                       -- open vocabulary
    object_entity_id   uuid not null references entity(entity_id) on delete cascade,
    evidence_id        uuid references evidence(evidence_id) on delete set null,
    confidence         numeric(3, 2),
    version            int  not null default 1,
    valid_from         date not null default current_date,
    valid_to           date,
    created_at         timestamptz not null default now()
);
create index if not exists idx_relationship_account on relationship (account_id);
create index if not exists idx_relationship_subject on relationship (subject_entity_id);
create unique index if not exists uq_relationship_current
    on relationship (organization_id, subject_entity_id, predicate, object_entity_id)
    where valid_to is null;

-- Claims: assertions about reality, separate from entities (SBTS §4), versioned.
create table if not exists claim (
    claim_id           uuid primary key default gen_random_uuid(),
    account_id         uuid not null references account(account_id) on delete cascade,
    organization_id    uuid not null references organization(organization_id) on delete cascade,
    subject_entity_id  uuid references entity(entity_id) on delete set null,
    subject_text       text,                                 -- fallback if subject isn't an entity
    predicate          text not null,
    object             text,
    value              text,
    claim_type         text not null,                        -- spec/performance/compliance/... (open)
    evidence_id        uuid references evidence(evidence_id) on delete set null,
    confidence         numeric(3, 2),
    version            int  not null default 1,
    valid_from         date not null default current_date,
    valid_to           date,
    status             text not null default 'active'
                         check (status in ('active', 'superseded', 'disputed')),
    created_at         timestamptz not null default now()
);
create index if not exists idx_claim_account on claim (account_id);
create index if not exists idx_claim_subject on claim (subject_entity_id);

-- Contradiction management (SBTS §15): recorded, not silently resolved.
create table if not exists conflict (
    conflict_id        uuid primary key default gen_random_uuid(),
    account_id         uuid not null references account(account_id) on delete cascade,
    organization_id    uuid not null references organization(organization_id) on delete cascade,
    object_type        text not null,                        -- claim | relationship
    object_a_id        uuid not null,
    object_b_id        uuid not null,
    description        text,
    resolution_status  text not null default 'pending_review'
                         check (resolution_status in ('pending_review', 'resolved', 'dismissed')),
    created_at         timestamptz not null default now()
);
create index if not exists idx_conflict_account on conflict (account_id);

-- RLS (ADR-001/007).
alter table evidence     enable row level security;
alter table relationship enable row level security;
alter table claim        enable row level security;
alter table conflict     enable row level security;

do $$
declare t text;
begin
    foreach t in array array['evidence', 'relationship', 'claim', 'conflict']
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
