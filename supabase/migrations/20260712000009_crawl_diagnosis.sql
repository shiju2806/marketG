-- marketG — crawl diagnosis: "what happened when AI tried to read the site".
-- Stored on the source so the report can lead with it (honest, first-class finding).

alter table source add column if not exists crawl_status text;      -- readable | blocked | thin | unreachable
alter table source add column if not exists crawl_diagnosis jsonb;  -- full diagnosis object
