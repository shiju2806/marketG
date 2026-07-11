-- marketG — Sprint 5 schema: evidence-backed recommendations (AVAS §5)
-- Each recommendation ties a specific twin/visibility gap to a concrete action
-- and the score(s) it would improve. Ranked by expected impact.

create table if not exists recommendation (
    recommendation_id  uuid primary key default gen_random_uuid(),
    account_id         uuid not null references account(account_id) on delete cascade,
    organization_id    uuid not null references organization(organization_id) on delete cascade,
    title              text not null,
    missing_type       text,              -- machine_readability | citation | coverage | trust
    missing_detail     text,
    affects            text[] not null default '{}',   -- which scores it lifts
    expected_impact    text not null default 'medium'
                         check (expected_impact in ('high', 'medium', 'low')),
    status             text not null default 'open'
                         check (status in ('open', 'applied', 'dismissed')),
    source             jsonb not null default '{}'::jsonb,   -- evidence/context
    created_at         timestamptz not null default now()
);
create index if not exists idx_recommendation_org on recommendation (organization_id, created_at desc);
create index if not exists idx_recommendation_account on recommendation (account_id);

alter table recommendation enable row level security;

drop policy if exists recommendation_isolation on recommendation;
create policy recommendation_isolation on recommendation
    using (account_id = current_account_id())
    with check (account_id = current_account_id());
