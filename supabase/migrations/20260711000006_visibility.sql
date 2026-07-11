-- marketG — Sprint 4 schema: AI Visibility scoring (internal engine)
-- A run computes the internal scores over the twin; per-question rows keep the
-- explainable breakdown (AVAS §4). Citation is external (Sprint 4b) and stays null here.

create table if not exists visibility_run (
    run_id               uuid primary key default gen_random_uuid(),
    account_id           uuid not null references account(account_id) on delete cascade,
    organization_id      uuid not null references organization(organization_id) on delete cascade,
    retrieval            int,
    reasoning            int,
    trust                int,
    machine_readability  int,
    citation             int,          -- filled by the external probe (Sprint 4b)
    overall              int,
    question_count       int,
    created_at           timestamptz not null default now()
);
create index if not exists idx_visibility_run_org on visibility_run (organization_id, created_at desc);
create index if not exists idx_visibility_run_account on visibility_run (account_id);

create table if not exists visibility_question (
    id               uuid primary key default gen_random_uuid(),
    run_id           uuid not null references visibility_run(run_id) on delete cascade,
    account_id       uuid not null references account(account_id) on delete cascade,
    organization_id  uuid not null references organization(organization_id) on delete cascade,
    question         text not null,
    intent           text,
    retrieval        numeric(3, 2),
    reasoning        numeric(3, 2),
    trust            numeric(3, 2),
    matched          jsonb not null default '{}'::jsonb,
    created_at       timestamptz not null default now()
);
create index if not exists idx_visibility_question_run on visibility_question (run_id);
create index if not exists idx_visibility_question_account on visibility_question (account_id);

alter table visibility_run      enable row level security;
alter table visibility_question enable row level security;

do $$
declare t text;
begin
    foreach t in array array['visibility_run', 'visibility_question']
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
