-- marketG — Sprint 1: Row-Level Security + triggers
-- ADR-001/007: every table is isolated by account_id.
-- The backend pipeline uses the service_role key (bypasses RLS). These policies
-- protect client (anon/authenticated) access: a user only sees their account's
-- rows, keyed on the `account_id` claim in their JWT app_metadata.

-- Resolve the caller's account from the verified JWT claims (null for service role).
create or replace function current_account_id() returns uuid
language sql stable as $$
    select nullif(
        (current_setting('request.jwt.claims', true)::jsonb
            -> 'app_metadata' ->> 'account_id'),
        ''
    )::uuid
$$;

-- keep job.updated_at fresh
create or replace function set_updated_at() returns trigger
language plpgsql as $$
begin
    new.updated_at = now();
    return new;
end
$$;

drop trigger if exists trg_job_updated_at on job;
create trigger trg_job_updated_at
    before update on job
    for each row execute function set_updated_at();

-- Enable RLS everywhere.
alter table account      enable row level security;
alter table app_user     enable row level security;
alter table organization enable row level security;
alter table source       enable row level security;
alter table job          enable row level security;
alter table document     enable row level security;

-- account: the row's own id must match the caller's account.
drop policy if exists account_isolation on account;
create policy account_isolation on account
    using (account_id = current_account_id())
    with check (account_id = current_account_id());

-- everything else: filter on account_id.
do $$
declare t text;
begin
    foreach t in array array['app_user', 'organization', 'source', 'job', 'document']
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
