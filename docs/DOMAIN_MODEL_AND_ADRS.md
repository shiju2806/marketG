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
| D-01…D-05 | Scoring, probe analysis, entity resolution, etc. | **Deferred** (defaults recorded) |

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

1. `account`, `user`, `organization` (with `parent_organization_id`, `org_role`, `account_id`) — ADR-001.
2. `source`, `job`, `document` (with `machine_readability` fields), object-storage layout — ADR-003/004.
3. RLS by `account_id` (Supabase Auth) — ADR-001.
4. Playwright-based crawler with page classification — ADR-003.
5. Entity/claim tables carry the automotive extensions from ADR-002 (used from Sprint 3, defined now so migrations don't churn).

**We are ready to start Sprint 1.**
