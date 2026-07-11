-- marketG — Sprint 1 schema: accounts, users, organizations
-- ADR-001: one account -> many organizations (corporate hierarchy)
-- ADR-006: vertical is a pluggable pack (vertical_pack_id on organization)
-- ADR-007: account_id is the leading partition key; no cross-account queries

create extension if not exists "pgcrypto";

-- The paying customer = the tenant boundary. `account_id` is carried on every
-- row and enforced by RLS. (Concrete replacement for the abstract tenant_id.)
create table if not exists account (
    account_id  uuid primary key default gen_random_uuid(),
    name        text not null,
    created_at  timestamptz not null default now()
);

-- A user belongs to an account. `auth_user_id` links to Supabase auth.users(id)
-- once Auth is wired; nullable so the scaffold runs without Auth.
create table if not exists app_user (
    user_id       uuid primary key default gen_random_uuid(),
    account_id    uuid not null references account(account_id) on delete cascade,
    auth_user_id  uuid,
    email         text not null,
    role          text not null default 'analyst'
                    check (role in ('owner', 'admin', 'analyst', 'reviewer')),
    created_at    timestamptz not null default now(),
    unique (account_id, email)
);

-- A brand/company. Sub-brands point at their parent (Chevrolet.parent = GM).
-- org_role keeps competitors in the same model without crawling them (ADR-003).
create table if not exists organization (
    organization_id          uuid primary key default gen_random_uuid(),
    account_id               uuid not null references account(account_id) on delete cascade,
    parent_organization_id   uuid references organization(organization_id) on delete set null,
    name                     text not null,
    website                  text,
    org_role                 text not null default 'owned_brand'
                               check (org_role in ('owned_brand', 'competitor_tracked')),
    -- ADR-006: which vertical pack governs this org's ontology/claims/questions.
    vertical_pack_id         text not null default 'automotive',
    created_at               timestamptz not null default now()
);

create index if not exists idx_app_user_account       on app_user (account_id);
create index if not exists idx_organization_account    on organization (account_id);
create index if not exists idx_organization_parent     on organization (account_id, parent_organization_id);
