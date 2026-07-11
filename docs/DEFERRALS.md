# marketG — Deferral Register

**Purpose:** One living list of everything we consciously deferred, so nothing is silently lost. Each item records *why* it's deferred, the *interim default* (so we're never blocked), and the *trigger* that should make us revisit it.

**How to use:** When you defer something, add a row here. When you pick one up, move it to "Resolved" at the bottom with the commit/date. Review this list at the start of each sprint.

**Status key:** 🔵 planned (has a target sprint) · ⚪ someday (no committed date) · 🟢 resolved

_Last updated: 2026-07-11_

---

## 1. Deferred Decisions (defaults recorded — from ADRs)

| ID | Item | Interim default | Trigger to revisit | Status |
|----|------|-----------------|--------------------|--------|
| D-01 | Scoring formulas (the four scores + machine-readability) | Each 0–100 from normalized signals; overall = equal-weighted mean; breakdown always shown | Before **Sprint 4** | 🔵 |
| D-02 | External-probe sampling & answer analysis | 3 samples per question per model; LLM classifier for org-mention / competitor-mention / claim-consistency; aggregate by majority/mean | Before **Sprint 4b** | 🔵 |
| D-03 | Entity resolution thresholds | **Partly done (Sprint 3):** ontology-seed canonicalization + difflib fuzzy-name merge (≥0.90). **Still pending:** embedding-cosine resolution | When name-only dedup proves insufficient | 🔵 |
| D-04 | Ontology seed | **Done (Sprint 3):** small automotive seed in the vertical pack, used for canonicalization; grows over time | Revisit per vertical | 🟢 |
| D-06 | **Predicate normalization** (canonical predicate ontology) — the LLM phrases the same relation/claim differently ("has" vs "has range"), so conflict detection + relationship dedup miss real matches. Discovered in Sprint 3 verification | Interim: predicates stored verbatim; conflict logic unit-tested but under-fires e2e | Before conflict detection is relied on (Sprint 4+) | 🔵 |
| D-05 | Cost controls | **Partly done (Sprint 2):** per-stage token/cost logged to job.metrics; per-chunk LLM-input truncation cap. **Still pending:** per-account budget + enforcement | When multi-account load is real | 🔵 |

## 2. Deferred Infrastructure (MVP collapses to Supabase — from TECH_STACK)

| ID | Item | Interim (MVP) | Trigger to adopt | Status |
|----|------|---------------|------------------|--------|
| I-01 | Graph database (Neo4j) | Relational tables + recursive CTE (2-hop) | Traversals routinely >2–3 hops, or relationship volume makes CTEs slow | ⚪ |
| I-02 | Dedicated vector DB (Qdrant) | pgvector in Postgres | Vector count/QPS outgrows pgvector (multi-million vectors, high concurrency) | ⚪ |
| I-03 | Search index (OpenSearch) | Postgres full-text (`tsvector`) | Lexical relevance needs true BM25 tuning / large-scale FTS | ⚪ |
| I-04 | Event streaming (Kafka/RabbitMQ) | Postgres `job` queue + workers | Job queue can't absorb ingestion bursts across many accounts | ⚪ |
| I-05 | Durable workflows (Temporal) | Idempotent jobs in the `job` table | Multi-step pipelines need retries/compensation/visibility beyond the job table | ⚪ |
| I-06 | Observability stack (Prometheus/Grafana/OTel) | Structured logs + `metrics` JSONB | Per-stage AI cost/latency needs real dashboards & alerting | ⚪ |
| I-07 | Orchestration/infra (Kubernetes/Terraform/Vault) | Docker on a single host | Scaling services independently; horizontal workers needed | ⚪ |

## 3. Deferred Product Scope (out of MVP — from PRD/AVAS/HRRE/KIPS)

| ID | Item | Why deferred | Trigger to revisit | Status |
|----|------|--------------|--------------------|--------|
| P-01 | Non-website connectors (PDF, docs portals, GitHub, Confluence, SharePoint, CRM, Zendesk, Notion, Slack, Salesforce, HubSpot) | MVP is website-only; connector layer is pluggable (KIPS §7 contract) | Post-MVP source expansion; first paying customer needs another source | ⚪ |
| P-02 | Industry-relevant external sources (open + paid: review sites, directories, analyst reports, datasets) | MVP ingests only the customer's own site | Per-vertical enrichment after first vertical proves out | ⚪ |
| P-03 | Full competitor twins | MVP detects competitor **mentions** in AI answers only (ADR-005) | Competitive Intelligence application | ⚪ |
| P-04 | Additional probe targets (Google AI Overviews, Gemini) | Harder to access programmatically; MVP = ChatGPT/Claude/Perplexity | Demand + accessible API/automation | ⚪ |
| P-05 | Multi-language support | MVP English-only | International customers | ⚪ |
| P-06 | Automated content generation | Out of MVP (we recommend, we don't write) | Product decision post-MVP | ⚪ |
| P-07 | Workflow automation | Out of MVP | Post-MVP | ⚪ |
| P-08 | Human-review / governance UI (approve/reject uncertain facts, conflict resolution UI) | Data model supports it (validated states, `conflict` table); UI deferred | When customers need to curate the twin | ⚪ |
| P-09 | Deep reasoning (>2-hop), learned reranker fine-tuning, real-time streaming reasoning | MVP bounds reasoning to 2 hops with weighted-fusion rerank | Reasoning quality demands it | ⚪ |

## 4. Deferred Applications (the twin powers these later — from PRD/SBTS)

| ID | Item | Status |
|----|------|--------|
| A-01 | Competitive Intelligence | ⚪ |
| A-02 | Content Intelligence | ⚪ |
| A-03 | Enterprise AI Memory | ⚪ |
| A-04 | Sales Enablement / Sales Copilot | ⚪ |
| A-05 | Documentation Intelligence | ⚪ |
| A-06 | Compliance Intelligence | ⚪ |
| A-07 | M&A Knowledge Discovery | ⚪ |
| A-08 | In-app recommendation / guided-selling advisor (embeddable widget grounded in the twin — content/reasoning-based recommendations with evidence; complements behavioral recommenders, strong on cold-start + explainability) | ⚪ |

_Beachhead app is **AI Visibility**; all above reuse the same Semantic Business Twin._

## 5. Deferred Knowledge Domains (twin extensions — from SBTS §20)

| ID | Item | Status |
|----|------|--------|
| K-01 | Financial knowledge | ⚪ |
| K-02 | Customer intelligence | ⚪ |
| K-03 | Employee knowledge | ⚪ |
| K-04 | Regulatory intelligence | ⚪ |
| K-05 | Product roadmaps | ⚪ |
| K-06 | Market intelligence | ⚪ |
| K-07 | Internal enterprise systems | ⚪ |

## 6. Deferred Enterprise / Non-Functional

| ID | Item | Trigger | Status |
|----|------|---------|--------|
| E-01 | Enterprise SSO | Enterprise customer requirement | ⚪ |
| E-02 | Secrets management (Vault) | Production hardening / compliance | ⚪ |
| E-03 | Additional vertical packs (SaaS, healthcare, fintech, …) | Second vertical (design supports it — ADR-006) | ⚪ |

---

## Resolved

_(Move items here when picked up, with commit + date.)_

| ID | Item | Resolved | Commit |
|----|------|----------|--------|
| — | — | — | — |
