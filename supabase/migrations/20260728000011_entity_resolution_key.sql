-- marketG — D-03: dedup entities on a normalized RESOLUTION KEY, not canonical_name.
-- "2026 R1S Dual", "r1s", "Rivian R1S" share key "r1s" -> one entity (R1S != R1T).

alter table entity add column if not exists resolution_key text;

-- The old name-based uniqueness fragmented casing variants; replace it.
drop index if exists uq_entity_natural;

create unique index if not exists uq_entity_resolution
    on entity (organization_id, entity_type, resolution_key)
    where resolution_key is not null;
