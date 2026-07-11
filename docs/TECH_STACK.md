# Enterprise Knowledge Intelligence Platform (EKIP)

**Technology Stack — MVP vs. Target**

- **Version:** 1.0
- **Status:** Foundational Architecture
- **Audience:** Engineering, Founders, Platform Team
- **Purpose:** Lock the concrete stack for the first build. The architecture docs (SAD §6, KIPS §23) describe the *target* polyglot system; this document decides what we actually build **first** and how it migrates to the target.

---

## 1. Guiding Decision

> **Build the thinnest stack that delivers the full end-to-end slice — twin → dual measurement → scores — then split stores out as scale demands.**

The SAD's polyglot design (Postgres + Neo4j + Qdrant + OpenSearch + Kafka + Temporal) is the **right target at scale**. But standing up five datastores + two orchestration systems before we have a single working twin would blow the timeline and add operational surface with no early payoff.

So for MVP we **collapse the stack around Supabase (managed Postgres)** — which the team already uses — and treat Neo4j, OpenSearch, Kafka, and Temporal as **deferred projections/infrastructure** we add when volume justifies them. Nothing in the collapse is a one-way door: Postgres is the authoritative source of truth in the target design too (DATABASE_DESIGN §1), so the other stores are always rebuildable projections.

---

## 2. MVP Stack (what we build now)

| Layer | MVP choice | Why |
|-------|-----------|-----|
| **Backend runtime** | **Python 3.12 + FastAPI** | Team's existing expertise (DataGenie); best AI/ML ecosystem. |
| **Frontend** | **React 18 + TypeScript + Tailwind** | Team standard; matches existing products. |
| **System-of-record DB** | **Supabase Postgres** | Managed, auth + storage + RLS built in; one datastore to run. |
| **Vector search** | **pgvector** (in the same Postgres) | Avoids a second datastore; fine to ~1M vectors at MVP scale. |
| **Lexical / BM25** | **Postgres full-text search** (`tsvector`) | Good enough for exact-term recall at MVP; no OpenSearch to operate. |
| **Graph / relationships** | **Relational tables + recursive CTEs** | The `entity` / `relationship` tables *are* the graph; 2-hop expansion (HRRE §6) is a recursive CTE. No Neo4j yet. |
| **Object storage** | **Supabase Storage** (S3-compatible) | Immutable raw documents; same platform. |
| **Auth & multi-tenancy** | **Supabase Auth + Row-Level Security** | `tenant_id` enforced at the DB; no custom auth to build. |
| **Pipeline orchestration** | **LangGraph** (extraction agents) + **Postgres-backed job queue** | LangGraph is team-known; the `job` table (DATABASE_DESIGN §3.4) + background workers replace Kafka/Temporal for now. |
| **Embeddings** | **OpenAI `text-embedding-3-small`** (swappable to BGE/E5) | Cheap, strong; interface kept provider-neutral. |
| **Extraction LLMs** | **Claude (Anthropic)** + **OpenAI**, behind one interface | Claude for careful extraction/verification; provider-abstracted. |
| **External probe targets** | **ChatGPT (OpenAI), Claude (Anthropic), Perplexity** APIs | The three locked probe targets (HRRE §13). Provider-pluggable. |
| **Web crawling** | **Playwright / httpx + a readability/boilerplate stripper** | Handles JS-rendered marketing sites; feeds Document Normalization (KIPS §9). |
| **Observability** | **Structured logs + a `metrics` JSONB on jobs/probe runs** | Per-stage latency/tokens/cost/confidence (SAD §19) without standing up Prometheus/Grafana yet. |
| **Infra / deploy** | **Docker + a single container host (Fly.io / Render / a VM)** | No Kubernetes for MVP. |

---

## 3. Deferred to Target (added when scale demands)

| Component | Deferred choice | Trigger to adopt |
|-----------|----------------|------------------|
| **Graph database** | **Neo4j** | When traversals exceed ~2–3 hops routinely, or relationship volume makes recursive CTEs slow. |
| **Dedicated vector DB** | **Qdrant** | When vector count / QPS outgrows pgvector (multi-million vectors, high concurrency). |
| **Search index** | **OpenSearch** | When lexical relevance needs true BM25 tuning / large-scale full-text. |
| **Event streaming** | **Kafka / RabbitMQ** | When the Postgres job queue can't absorb ingestion bursts across many tenants. |
| **Durable workflows** | **Temporal** | When multi-step pipelines need retries/compensation/visibility beyond the job table. |
| **Metrics/observability** | **Prometheus + Grafana + OpenTelemetry** | When per-stage AI cost/latency needs real dashboards & alerting. |
| **Orchestration/infra** | **Kubernetes + Terraform + Vault** | When we scale services independently (SAD §21) and need horizontal workers. |

---

## 4. Why the Graph-in-Postgres Call Is Safe for MVP

The twin is conceptually a graph, so "no Neo4j" deserves justification:

- The `entity` and `relationship` tables (DATABASE_DESIGN §3.7, §3.10) already model nodes and edges relationally, with evidence, confidence, and versioning.
- MVP graph expansion is bounded to **2 hops** (HRRE §12) over five relationship types — a textbook **recursive CTE**, fast at MVP data sizes.
- Postgres remains the **source of truth** even in the target design; Neo4j is a *projection*. So adopting Neo4j later is an additive migration (build a projector), not a rewrite.
- We avoid running, backing up, and securing a second stateful database during the riskiest phase of the project.

**When this breaks:** deep multi-hop reasoning (3+ hops), pathfinding, or graph algorithms (centrality, community detection) — that's the signal to project into Neo4j.

---

## 5. Provider Abstraction (non-negotiable, even in MVP)

To keep the deferrals cheap, three seams are abstracted behind interfaces from day one:

1. **`Connector`** — source adapters (website now; industry/paid later). KIPS §7 contract.
2. **`LLMProvider`** — extraction + reasoning LLMs (Claude / OpenAI, swappable).
3. **`ProbeTarget`** — external assistants (ChatGPT / Claude / Perplexity, add Gemini later).

And two storage seams so the deferred stores drop in without touching callers:

4. **`VectorStore`** — pgvector now, Qdrant later.
5. **`SearchIndex`** — Postgres FTS now, OpenSearch later.

Everything else can be concrete. Over-abstracting the rest is premature.

---

## 6. Alignment With the Architecture Docs

- **SAD §6 (polyglot storage):** honored as the *target*; MVP collapses stores but keeps Postgres authoritative and others as rebuildable projections — exactly the SAD's own principle.
- **KIPS §23 (tech recommendation):** Temporal/Kafka deferred; LangGraph kept; embeddings/extraction models as specified.
- **DATABASE_DESIGN §1:** unchanged — Postgres is source of truth; graph/vector/search are projections. MVP simply hosts the vector projection *inside* Postgres and the graph *as* Postgres tables.
- **HRRE §6 / §12:** 2-hop expansion satisfied via recursive CTE.

No architecture doc needs to change — this document records the MVP *instantiation* of the target design.

---

## 7. Summary

| | MVP | Target |
|---|-----|--------|
| **Datastores** | Supabase Postgres (+ pgvector, + FTS, + Storage) | Postgres + Neo4j + Qdrant + OpenSearch + Object Storage |
| **Graph** | Relational tables + recursive CTE | Neo4j |
| **Events** | Postgres job queue | Kafka + Temporal |
| **Infra** | Docker on one host | Kubernetes + Terraform + Vault |
| **Observability** | Structured logs + JSONB metrics | Prometheus + Grafana + OTel |
| **Constant across both** | Python/FastAPI · React/TS · LangGraph · Claude+OpenAI · pluggable Connector/LLM/Probe/Vector/Search seams | (same) |

**Bottom line:** one database, one language, five clean abstraction seams. Ship the full twin → dual-measurement → scores slice, then split stores out along seams that already exist.
