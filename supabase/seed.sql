-- marketG — local dev seed. Loaded by `supabase db reset`.
-- A demo account with one owned brand (Rivian) to exercise the crawler.

insert into account (account_id, name)
values ('00000000-0000-0000-0000-000000000001', 'Demo Motors Inc')
on conflict (account_id) do nothing;

insert into app_user (account_id, email, role)
values ('00000000-0000-0000-0000-000000000001', 'demo@marketg.dev', 'owner')
on conflict (account_id, email) do nothing;

-- Owned brand under the demo account (automotive vertical pack).
insert into organization (organization_id, account_id, name, website, org_role, vertical_pack_id)
values (
    '00000000-0000-0000-0000-0000000000a1',
    '00000000-0000-0000-0000-000000000001',
    'Rivian',
    'https://www.rivian.com',
    'owned_brand',
    'automotive'
)
on conflict (organization_id) do nothing;
