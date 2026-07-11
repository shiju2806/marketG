# marketG Backend — Sprint 1 (Ingestion)

FastAPI backend + Playwright crawler + Postgres-backed job queue, on local Supabase.

Delivers the Sprint 1 slice: **submit a brand's domain → crawl it (JS-rendered) → classified pages + raw artifacts + machine-readability signals persisted, isolated by account.**

## Prerequisites

- Python 3.11+
- [Supabase CLI](https://supabase.com/docs/guides/cli) (`brew install supabase/tap/supabase`)
- Docker (for local Supabase)

## 1. Start local Supabase

From the repo root (`~/marketG`):

```bash
supabase init            # first time only — generates config.toml
supabase start           # boots Postgres, Storage, etc.; prints keys
supabase db reset        # applies migrations in supabase/migrations + seed.sql
```

`supabase start` prints an **API URL**, **DB URL**, and a **service_role key**.

## 2. Configure the backend

```bash
cd backend
cp .env.example .env
# paste the service_role key from `supabase start` into SUPABASE_SERVICE_ROLE_KEY
```

## 3. Install dependencies

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
playwright install chromium   # one-time browser download (ADR-003)
```

## 4. Run

Two processes:

```bash
# API
uvicorn app.main:app --reload            # http://127.0.0.1:8000/docs

# Worker (separate terminal, same venv)
python -m app.jobs.worker
```

## 5. Exercise the slice

The seed created a demo account (`00000000-0000-0000-0000-000000000001`) with a
Rivian organization. Add a website source and crawl it:

```bash
ACC=00000000-0000-0000-0000-000000000001
ORG=00000000-0000-0000-0000-0000000000a1

# register the website as a source
SRC=$(curl -s -X POST localhost:8000/api/v1/sources \
  -H "X-Account-Id: $ACC" -H 'Content-Type: application/json' \
  -d "{\"organization_id\":\"$ORG\",\"seed_url\":\"https://www.rivian.com\"}" \
  | python -c "import sys,json;print(json.load(sys.stdin)['source_id'])")

# start the crawl (the worker picks it up)
JOB=$(curl -s -X POST localhost:8000/api/v1/crawl \
  -H "X-Account-Id: $ACC" -H 'Content-Type: application/json' \
  -d "{\"source_id\":\"$SRC\"}" \
  | python -c "import sys,json;print(json.load(sys.stdin)['job_id'])")

# poll status
curl -s localhost:8000/api/v1/crawl/$JOB -H "X-Account-Id: $ACC" | python -m json.tool
```

When `status` is `done`, inspect the results in Supabase Studio (`supabase start`
prints its URL) — the `document` table shows each page's classification,
`js_required`, `has_schema_org`, and `ai_crawler_policy`.

## Tests

Pure-logic unit tests (no services needed):

```bash
python -m pytest tests/test_classifier.py tests/test_robots.py -v
```

## Notes

- **Auth is a placeholder in Sprint 1:** the account comes from an `X-Account-Id`
  header. When Supabase Auth is wired, it comes from the JWT (`app_metadata.account_id`)
  — the same value RLS uses — and only `app/api/deps.py` changes.
- **Account isolation** (ADR-001/007): every query is scoped by `account_id`; the
  pipeline uses the service_role key (bypasses RLS), client access is governed by
  the RLS policies in `supabase/migrations/...rls_and_triggers.sql`.
- **Vertical pack** (ADR-006): the org carries `vertical_pack_id` (`automotive`);
  `entity_type`/`claim_type` will be open vocabularies, never DB enums.
