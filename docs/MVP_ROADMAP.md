# Enterprise Knowledge Intelligence Platform (EKIP)

**MVP Engineering Roadmap**

- **Version:** 1.0
- **Status:** Foundational Architecture
- **Audience:** Engineering Managers, Tech Leads, Founders, Product, Platform Team

---

## 1. Purpose

This roadmap translates the architecture (SAD, SBTS, KIPS, HRRE, AVAS, API, DB) into an ordered, buildable implementation plan for the MVP.

The MVP goal, per the PRD: **ingest a single website → build a Semantic Business Twin → run AI Visibility via internal simulation *and* external probing of ChatGPT/Claude/Perplexity → produce scores (with competitor mentions) and evidence-backed recommendations.** GEO positioning; B2B SaaS beachhead.

Each sprint delivers a working, demonstrable slice. The sequence is dependency-driven: storage before extraction, twin before reasoning, reasoning before the app.

---

## 2. Guiding Principles

- **Vertical slices** — every sprint ends with something runnable end-to-end for its scope, not a half-integrated layer.
- **The twin is the product** — sprints 1–3 exist to produce a trustworthy twin; sprints 4–5 consume it.
- **Provenance from day one** — evidence + confidence are wired in from the first extraction, not retrofitted.
- **Projections are rebuildable** — Postgres is authoritative; graph/vector/search are built from it.

---

## 3. Sprint Plan

### Sprint 1 — Foundation

**Goal:** stand up the platform skeleton and get raw content into storage.

- User & organization management (auth, tenant scoping).
- Website crawler: URL seed → discovery → page classification → content extraction (KIPS §5–7).
- Storage layer: PostgreSQL (organization, users, source, job, document tables) + object storage for raw artifacts.
- Ingestion API: `POST /organizations`, `POST /sources`, `POST /crawl`, `GET /crawl/{job_id}`.

**Exit criteria:** submit a domain, crawl it, and see classified pages + raw artifacts persisted with provenance.

---

### Sprint 2 — Knowledge Extraction

**Goal:** turn raw pages into structured, embedded, semantically-chunked knowledge.

- Document normalization (strip nav/footers/ads; preserve headings, tables, lists — KIPS §9).
- Semantic chunking engine (concept-based, not token-based — KIPS §10–11).
- Entity extraction (NER + LLM verification — KIPS §12).
- Embeddings → vector store (pgvector) + BM25 index (OpenSearch).

**Exit criteria:** a crawled site yields semantic chunks with entities, embeddings indexed for both lexical and vector retrieval.

---

### Sprint 3 — Semantic Business Twin

**Goal:** build the governed, evidence-backed twin.

- Graph database (Neo4j) with MVP node/relationship types.
- Ontology resolution + entity resolution (dedupe, canonicalization — KIPS §13, SBTS §16).
- Relationship, claim, and evidence extraction agents (KIPS §14).
- Governance layer: duplicate detection, conflict detection, confidence calculation, confidence-threshold review (KIPS §17–18).
- Versioning + provenance wired through (SBTS §12–14).
- Twin API: `GET /semantic-twin`, `/entities`, `/claims`, `/evidence`.

**Exit criteria:** an evidence-backed twin exists in Neo4j + Postgres, with claims separate from entities, confidence scores, and conflict detection working.

---

### Sprint 4 — AI Visibility (Internal Engine)

**Goal:** measure what AI *could* conclude from the twin, explainably.

- Query generation from the twin + B2B SaaS category intents (AVAS §3.3).
- Hybrid retrieval + reasoning engine: BM25 + vector → graph expansion → rerank → evidence selection → LLM reasoning (HRRE §3–12).
- Reasoning modes: coverage, gap, confidence, basic competitive (HRRE §10).
- Internal simulation across generated questions.
- Scoring (internal portion): Retrieval, Reasoning, Trust (AVAS §4).
- Reasoning/App API: `POST /reason`, partial `GET /visibility-score`.

**Exit criteria:** run internal simulations for a built twin and get the internally-sourced scores with per-question evidence and gaps.

---

### Sprint 4b — External AI Probe

**Goal:** measure what real AI *actually* says today.

- External probe layer: fan buyer questions out to **ChatGPT, Claude, Perplexity** (provider-pluggable), async via queue (HRRE §13).
- Answer analysis: org-mention, org-citation, **competitor-mention detection** (no competitor twins), claim-consistency vs. the twin.
- `probe_run` / `probe_result` persistence + observability (latency, tokens, cost).
- Probe API: `POST /probe`, `GET /probe/{job_id}`.
- Fold external signal into Citation (primary), Retrieval, and Trust scores; finalize overall `GET /visibility-score` (AVAS §4).

**Exit criteria:** probe the three assistants for a built twin's questions and see real answers, competitor mentions, and the completed four-score index.

---

### Sprint 5 — Dashboard

**Goal:** make it usable and actionable.

- Reports: overall + four sub-scores with breakdowns and per-question detail.
- Evidence-backed recommendations tied to specific twin gaps (AVAS §5).
- Recommendation API: `GET /recommendations`.
- Frontend: add-website flow, twin-build progress, visibility report, recommendation list.

**Exit criteria:** a user adds a website and, end-to-end, sees a visibility report with ranked, evidence-backed recommendations.

---

## 4. Cross-Cutting (built alongside, not a separate sprint)

- **Event-driven orchestration** — crawler → document → extraction → governance → twin-update events (SAD §18, KIPS §22). Introduced in Sprint 1, extended each sprint.
- **Observability** — per-stage latency, tokens, cost, confidence, errors, retries (SAD §19). Wired from Sprint 2 (first LLM calls).
- **Security & lineage** — tenant, source, permissions, classification, version on every object (SAD §20). From Sprint 1.

---

## 5. Dependency Map

```
Sprint 1 (storage + crawl)
        ↓
Sprint 2 (chunks + entities + indexes)
        ↓
Sprint 3 (twin + governance)   ← the product core
        ↓
Sprint 4  (internal retrieval + reasoning + partial scores)
        ↓
Sprint 4b (external AI probe + competitor mentions + full scores)
        ↓
Sprint 5 (dashboard + recommendations)
```

Nothing in Sprint 4 can be trusted until Sprint 3's governance and evidence are in place — reasoning quality is bounded by twin quality. Sprint 4b depends on Sprint 4's question generation but its external calls are independent, so it can run partly in parallel.

---

## 6. MVP Definition of Done

- ✓ Single-website ingestion (pluggable connector layer) → governed twin → AI Visibility report, end-to-end.
- ✓ Entities: Company, Product, Feature, Technology, Integration, Industry, Competitor.
- ✓ Relationships: provides, integrates_with, competes_with, solves, supports.
- ✓ Claims: capability, integration, compliance.
- ✓ Internal twin simulation **and** external probing of ChatGPT, Claude, Perplexity.
- ✓ Competitor mention/citation detection from real AI answers (no competitor twins).
- ✓ Four visibility scores (tagged Internal/External/Both) + evidence-backed recommendations.
- ✓ Every fact traceable to evidence with multi-dimensional confidence.
- ✓ GEO positioning, B2B SaaS beachhead.

**Explicitly out of MVP** (per PRD §12): internal enterprise connectors, multi-language, automated content generation, workflow automation, enterprise governance features.

---

## 7. Suggested Team Alignment

Mirrors the SAD's capability-based team structure so each team owns a coherent slice:

| Team | Sprints | Owns |
|------|---------|------|
| Knowledge Acquisition | 1 | Crawler, connectors, document ingestion |
| Knowledge Intelligence | 2–3 | Chunking, extraction, ontology, governance |
| Semantic Twin Platform | 1–3 | Storage, graph, versioning, Twin API |
| Reasoning & Retrieval | 4, 4b | Hybrid retrieval, reasoning, external AI probe, scoring |
| Application | 4b–5 | AI Visibility app, dashboard, recommendations |

---

## 8. Key Sequencing Decision

Build the **twin before the application**. The temptation is to demo AI Visibility scores early, but scores computed over an ungoverned, evidence-poor twin are noise. The roadmap front-loads storage, extraction, and governance (Sprints 1–3) precisely because every downstream metric and recommendation is only as trustworthy as the twin beneath it.
