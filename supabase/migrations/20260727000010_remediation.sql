-- marketG — Phase 1: remediation artifacts (the generated "fix" for a gap).
-- Turns a diagnosed delta gap into a ready-to-use page draft / schema / copy.

create table if not exists remediation (
    remediation_id     uuid primary key default gen_random_uuid(),
    account_id         uuid not null references account(account_id) on delete cascade,
    organization_id    uuid not null references organization(organization_id) on delete cascade,
    recommendation_id  uuid references recommendation(recommendation_id) on delete set null,
    gap_type           text,          -- missing | hidden | word | design | crawlability
    title              text,
    artifact           jsonb not null default '{}'::jsonb,  -- {title, body_markdown, body_html, schema_jsonld, notes}
    status             text not null default 'draft'
                         check (status in ('draft', 'published', 'dismissed')),
    created_at         timestamptz not null default now()
);

create index if not exists idx_remediation_org on remediation (organization_id, created_at desc);
create index if not exists idx_remediation_account on remediation (account_id);
create index if not exists idx_remediation_rec on remediation (recommendation_id);

alter table remediation enable row level security;

drop policy if exists remediation_isolation on remediation;
create policy remediation_isolation on remediation
    using (account_id = current_account_id())
    with check (account_id = current_account_id());
