-- marketG — Sprint 4b schema: External AI Probe (HRRE §13)
-- Probe real assistants with buyer questions; record what they actually say and
-- who they cite. These are OBSERVATIONS about the outside world — they never enter
-- the twin as facts (they inform the Citation score + earned-vs-owned insight).

create table if not exists probe_run (
    probe_run_id          uuid primary key default gen_random_uuid(),
    account_id            uuid not null references account(account_id) on delete cascade,
    organization_id       uuid not null references organization(organization_id) on delete cascade,
    visibility_run_id     uuid references visibility_run(run_id) on delete set null,
    targets               text[] not null default '{}',
    question_count        int,
    samples_per_question  int not null default 1,
    status                text not null default 'queued'
                            check (status in ('queued', 'running', 'done', 'failed')),
    citation              int,
    earned_owned          numeric(3, 2),      -- share of cited sources that are first-party
    metrics               jsonb not null default '{}'::jsonb,
    created_at            timestamptz not null default now()
);
create index if not exists idx_probe_run_org on probe_run (organization_id, created_at desc);
create index if not exists idx_probe_run_account on probe_run (account_id);

-- One row per question x model x sample (external answers are non-deterministic).
create table if not exists probe_result (
    probe_result_id        uuid primary key default gen_random_uuid(),
    probe_run_id           uuid not null references probe_run(probe_run_id) on delete cascade,
    account_id             uuid not null references account(account_id) on delete cascade,
    organization_id        uuid not null references organization(organization_id) on delete cascade,
    question               text not null,
    model                  text not null,
    sample                 int not null default 1,
    answer                 text,
    organization_mentioned boolean,
    organization_cited     boolean,
    competitor_mentions    text[] not null default '{}',
    claim_consistency      text,               -- consistent | inconsistent | unknown
    cited_sources          jsonb not null default '[]'::jsonb,
    first_party            int not null default 0,
    third_party            int not null default 0,
    latency_ms             int,
    tokens                 int,
    cost_usd               numeric(10, 4),
    probed_at              timestamptz not null default now()
);
create index if not exists idx_probe_result_run on probe_result (probe_run_id);
create index if not exists idx_probe_result_account on probe_result (account_id);

alter table probe_run    enable row level security;
alter table probe_result enable row level security;

do $$
declare t text;
begin
    foreach t in array array['probe_run', 'probe_result']
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
