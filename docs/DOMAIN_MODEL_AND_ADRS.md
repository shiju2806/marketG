# Enterprise Knowledge Intelligence Platform (EKIP)

**Domain Model & Architecture Decision Records (ADRs)**

- **Version:** 1.0
- **Status:** Foundational — locked before first code
- **Audience:** Engineering (this is the source of truth the schema and code follow)
- **Purpose:** Pin the decisions that shape the database schema and are expensive to change later, and record defaults for the ones we defer. Where this document and the earlier specs differ, **this document wins** for MVP implementation; the specs describe the target design.

---

## Decision Status Summary

| # | Decision | Status |
|---|----------|--------|
| ADR-001 | Account → many brands hierarchy | **Locked** |
| ADR-002 | Automotive domain layer (Vehicle/Model first-class) | **Locked** |
| ADR-003 | Crawler renders all pages headless (Playwright) | **Locked** |
| ADR-004 | Machine-readability is a first-class score | **Accepted** |
| ADR-005 | Probe records source provenance (earned vs owned) | **Accepted** |
| ADR-006 | Vertical portability — industry is a pluggable pack | **Locked** |
| ADR-007 | Horizontal scale is a first-class design constraint | **Locked** |
| D-01…D-05 | Scoring, probe analysis, entity resolution, etc. | **Deferred** (defaults recorded) |

> All deferred items are tracked in the running register: [`DEFERRALS.md`](DEFERRALS.md).

---

## ADR-001 — Account ↔ Brand Hierarchy

**Decision:** One **customer account** owns a **portfolio of organizations**. Each organization has its own twin; the account rolls them up. A customer like GM is *one account* holding *five organizations* (GM parent + Chevrolet, GMC, Buick, Cadillac).

**Core identity tables (supersede DATABASE_DESIGN §3.1–3.2 tenancy):**

- **`account`** — the paying customer (the tenant boundary). `account_id` is the value carried on every row and enforced by RLS. *(Replaces the abstract `tenant_id` → it is now concretely `account_id`.)*
- **`user`** — belongs to an `account`; roles `owner | admin | analyst | reviewer`.
- **`organization`** — a brand/company. New fields:
  - `account_id` → owning account.
  - `parent_organization_id` (nullable) → models corporate hierarchy (Chevrolet.parent = GM).
  - `org_role` → `owned_brand` (the customer's own brands, fully twinned) | `competitor_tracked` (a rival held as a *light* entity for comparison — see ADR-005; **not** fully crawled).
- The **twin is per-organization.** Cross-brand/portfolio reasoning happens at the account level by querying across its organizations.

**Why:** matches the validated pilot (GM's parent + sub-brands), enables portfolio roll-up and cross-brand reasoning, and keeps competitor tracking in the same model without crawling competitors.

**Consequence:** every twin table (`entity`, `relationship`, `claim`, `evidence`, …) carries `account_id` **and** `organization_id`. RLS is by `account_id`.

---

## ADR-002 — Automotive Domain Layer

**Decision:** Add a first-class automotive layer now rather than retrofitting later. Keep the generic entity model from SBTS; **extend** it.

**New / promoted entity types:**

- **`Vehicle` (a.k.a. Model)** — first-class entity. Attributes: `model_year`, `body_style` (truck/SUV/sedan/…), `trims[]`, `powertrain` (ICE/hybrid/EV), `price_msrp`, `range_mi`, `mpg`, `horsepower`, `torque`, `towing_lbs`, `seating`, `drivetrain`, `lifecycle_status`.
- Existing generic types remain: `Organization` (brand), `Feature`, `Technology`, `Industry`, `Competitor`.

**New claim types (extend SBTS §10):**

- `spec` — a factual attribute ("410-mile range").
- `performance` — a measured outcome ("0–60 in 2.9s").
- `comparison` — relative to a rival ("more range than F-150 Lightning").
- `award` — third-party recognition ("won US News off-road EV award").
- `safety` — ratings ("IIHS Top Safety Pick+").
- (existing: `capability`, `integration`, `compliance`, `market`, `competitive`.)

**New / emphasized relationships:**

- `makes` (Organization → Vehicle), `variant_of` (Vehicle → Vehicle), `competes_with` (Vehicle → Vehicle), `won` (Vehicle → Award).

**Why:** the beachhead is automotive and the pilots proved buyer questions are model-level and spec/comparison-driven. Building generic and retrofitting would rework extraction, schema, and scoring together.

**Consequence:** extraction agents (KIPS §14) get a Vehicle/spec emphasis for the automotive vertical; the ontology seed (D-04) includes automotive categories. The design stays extensible to other verticals (the automotive layer is additive, not hardcoded into the core).

---

## ADR-003 — Crawler Renders All Pages (Headless)

**Decision:** The Sprint-1 crawler uses **Playwright headless rendering on every page**. Brand sites are JS/SPA (both GM and Rivian were in the pilots), so static fetch would capture almost nothing.

**Policy:**

- Render each page, capture the **post-JS DOM**; store raw rendered HTML immutably in object storage (DATABASE_DESIGN §7).
- We crawl **only the customer's own, authorized sites** (`org_role = owned_brand`). The customer authorizes crawling of their property at onboarding.
- **Competitors are never crawled** — competitive signal comes from the External AI Probe only (ADR-005, HRRE §13).
- Politeness/config: concurrency cap, per-domain rate limit, crawl depth limit, page budget, and a captured-at timestamp. Respect a customer's request to exclude paths.
- Record HTTP status + a `machine_readability` signal per page (status, was-JS-required, schema.org present) — feeds ADR-004.

**Why:** reliably captures modern brand-site content; the customer relationship removes the robots.txt ambiguity for their own domain.

**Consequence:** heavier per-page cost and infra (a headless browser in the pipeline). Acceptable for MVP volumes; revisit static-first optimization at scale.

---

## ADR-006 — Vertical Portability: Industry Is a Pluggable Pack

**Decision:** The automotive layer (ADR-002) is **not hardcoded**. It is the first instance of a **Vertical Pack** — a data/config-driven module the core platform loads. Switching industries (automotive → SaaS → healthcare → …) means loading a different pack, **never** changing core code or migrating core tables. This is a sixth abstraction seam alongside the five in TECH_STACK (`Connector`, `LLMProvider`, `ProbeTarget`, `VectorStore`, `SearchIndex`) → **`VerticalPack`**.

**A Vertical Pack defines (as config/seed data, not code):**

- **Entity-type extensions** (automotive: `Vehicle`; SaaS: `Product`/`API`; etc.).
- **Claim-type extensions** (automotive: `spec`/`performance`/`comparison`/`award`/`safety`).
- **Ontology seed** for the vertical (D-04).
- **Buyer-question templates** used by question generation (AVAS §3.3).
- **Scoring emphasis** (which claim types weigh into which scores).
- **Extraction prompt hints** for the vertical.

**Schema consequence (critical — set now):** `entity.entity_type` and `claim.claim_type` are **open vocabularies** — a small fixed *core* set plus pack-provided extensions, validated against the **active pack** — **not** hardcoded Postgres `ENUM`s. Adding a vertical must never require an `ALTER TYPE`. The core twin tables (`entity`, `relationship`, `claim`, `evidence`) are vertical-agnostic; verticals ride on the `type` fields + an `attributes` JSONB, plus a `vertical_pack_id` on the organization.

**Why:** the founder's requirement — deploying marketG to a new industry or company must be seamless. The account/org model (ADR-001) already makes onboarding a new *company* a data operation (create account + org + crawl). This ADR makes onboarding a new *industry* a data operation too (author a pack).

**Deploying to a new company** = create `account` → add `organization`(s) with a `vertical_pack_id` → authorize + crawl. No code change.
**Deploying to a new industry** = author a Vertical Pack (config + seed) → assign it. No core-schema change.

---

## ADR-007 — Horizontal Scale Is a First-Class Design Constraint

**Decision:** Scaling is designed in from Sprint 1, not retrofitted. The MVP collapses *infrastructure* (TECH_STACK: one Supabase), but the *design* must never assume a single node or block the scale-out path.

**Principles (binding on all code):**

1. **Account-partitioned.** `account_id` is the leading key on twin tables; **no query crosses accounts**. This keeps sharding/partitioning by account trivial later.
2. **Stateless, queue-driven workers.** Every heavy stage (crawl, extract, embed, probe) is an idempotent, resumable job behind a queue (the Postgres `job` table now; Kafka/Temporal later — DEFERRALS). Each stage scales independently (SAD §21).
3. **Authoritative store + rebuildable projections.** Postgres is the source of truth; vector/graph/search are projections that scale out independently and can be rebuilt (DATABASE_DESIGN §1). No projection holds unique state.
4. **Idempotency & resumability.** Jobs are safe to retry; a crashed crawl/extract resumes without duplication (content hashing, upserts keyed by natural keys).
5. **Cost as a scale dimension.** Per-account token/cost budgets (D-05) from the first LLM call — LLM spend is the real scaling ceiling, not CPU.

**Why:** the founder's requirement — scaling must not be a limiting factor. These constraints cost little now and preserve the full horizontal path (independent workers, partition-by-account, projection split-out) without a rewrite.

**Consequence:** connection pooling from day one; natural keys for upserts; no in-memory cross-request state; queue + worker abstraction even while it's Postgres-backed.

---

## ADR-004 — Machine-Readability Is a First-Class Score (Accepted)

**Decision:** Add **machine-readability** as a scored dimension (surfaced by the pilots; the GM 403s made it the most visceral metric). It feeds **Retrieval** and **Trust**.

**Signals:** crawlability (HTTP status), AI-crawler policy (robots.txt: GPTBot/ClaudeBot/PerplexityBot/Google-Extended allowed?), SSR vs. SPA (was JS required for content?), structured data presence (schema.org `Vehicle`/`Product`/`Organization`).

**Consequence:** add a `machine_readability` signal to the page/document record and to the score model (AVAS §4 will be updated when scoring is pinned, D-01).

---

## ADR-005 — Probe Records Source Provenance: "Earned vs Owned" (Accepted)

**Decision:** The External AI Probe records **which domains AI cites** and classifies each as **first-party (owned)** vs **third-party (earned)** — the single most persuasive insight from the pilots ("who authors your answer").

**Consequence:** `probe_result.cited_sources[]` (DATABASE_DESIGN §3.16) gains per-source classification; a derived "earned vs owned share" metric feeds the report and Trust score.

---

## Deferred Decisions (defaults recorded, revisit just-in-time)

These are tunable and low-debt. Each has a working default so nothing blocks; finalize before the noted sprint.

- **D-01 — Scoring formulas (before Sprint 4).** *Default:* each score 0–100 from normalized signal inputs; overall = equal-weighted mean of the five; breakdown always shown. Weights become tunable config.
- **D-02 — Probe sampling & answer analysis (before Sprint 4b).** *Default:* 3 samples per question per model; org-mention, competitor-mention, and claim-consistency detected by an **LLM classifier** (not string match) over each answer; aggregate by majority/mean across samples.
- **D-03 — Entity resolution (before Sprint 3).** *Default:* candidate match if embedding cosine ≥ 0.90 **and** fuzzy name match; else new candidate entity. Human-review threshold per KIPS §18.
- **D-04 — Ontology seed (before Sprint 3).** *Default:* start with a small seeded automotive ontology (brand → model → body-style → powertrain; regulations; common technologies) and let it grow; no giant upfront taxonomy.
- **D-05 — Cost controls (before Sprint 2).** *Default:* per-account token/cost budget with a cap; log latency/tokens/cost per stage (SAD §19) from the first LLM call.

---

## What This Locks for Sprint 1

The schema we write in Sprint 1 is now determined:

1. `account`, `user`, `organization` (with `parent_organization_id`, `org_role`, `account_id`, **`vertical_pack_id`**) — ADR-001/006.
2. `source`, `job`, `document` (with `machine_readability` fields), object-storage layout — ADR-003/004.
3. RLS by `account_id`; `account_id` as the **leading partition key** on every twin table; no cross-account queries — ADR-001/007.
4. Playwright-based crawler with page classification; idempotent, queue-driven, resumable jobs — ADR-003/007.
5. Entity/claim tables use **open-vocabulary `type` fields + `attributes` JSONB** (not Postgres ENUMs), so the automotive pack — and any future vertical — rides on data, not schema changes — ADR-002/006.

**We are ready to start Sprint 1.**
