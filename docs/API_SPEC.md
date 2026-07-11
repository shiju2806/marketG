# Enterprise Knowledge Intelligence Platform (EKIP)

**API Specification**

- **Version:** 1.0
- **Status:** Foundational Architecture
- **Audience:** Backend Engineers, Frontend Engineers, AI Engineers, Platform Architects, Integration Partners

---

## 1. Purpose

This document defines the external and internal HTTP interfaces of the platform. All applications (starting with AI Visibility) consume these APIs — **no application talks to the graph, vector, or search stores directly** (SAD §17).

The API surface is organized into layers that mirror the architecture:

- **Twin API** — read entities, claims, evidence, the semantic twin.
- **Reasoning API** — run internal retrieval + reasoning over the twin (HRRE §3–12).
- **Probe API** — probe real external AI assistants (ChatGPT, Claude, Perplexity) and read results (HRRE §13).
- **Recommendation API** — evidence-backed improvement suggestions.
- **Ingestion API** — organizations, sources, crawls.

---

## 2. Conventions

- **Base URL:** `/api/v1`
- **Format:** JSON request/response; `Content-Type: application/json`.
- **Auth:** Bearer token (`Authorization: Bearer <token>`); every request is tenant-scoped.
- **Multi-tenancy:** all objects carry a `tenant_id`; propagated with lineage (SAD §20).
- **Async operations:** long-running jobs (crawl, twin build) return `202 Accepted` with a `job_id`; poll job status or subscribe to events.
- **Errors:** standard HTTP status codes + `{ "error": { "code": "...", "message": "..." } }`.
- **Pagination:** cursor-based (`?limit=&cursor=`).

---

## 3. Endpoint Overview

| Method | Path | Purpose |
|--------|------|---------|
| POST | `/organizations` | Register an organization |
| GET | `/organizations/{id}` | Get an organization |
| POST | `/sources` | Register a knowledge source |
| POST | `/crawl` | Start a crawl of a source |
| GET | `/crawl/{job_id}` | Crawl job status |
| GET | `/semantic-twin` | Get the twin summary for an org |
| GET | `/entities` | List entities |
| GET | `/entities/{id}` | Get an entity (relationships, claims, evidence) |
| GET | `/claims` | List claims |
| GET | `/claims/{id}` | Get a claim (confidence, evidence, history) |
| GET | `/evidence/{id}` | Get an evidence record |
| POST | `/reason` | Run an internal reasoning query over the twin |
| POST | `/probe` | Probe external AI assistants with buyer questions |
| GET | `/probe/{job_id}` | Get probe run status + results |
| GET | `/visibility-score` | Get AI Visibility scores |
| GET | `/recommendations` | Get evidence-backed recommendations |

---

## 4. Ingestion API

### POST /organizations

Register an organization (creates its tenant scope and empty twin).

Request:

```json
{
  "name": "Acme Payroll",
  "website": "https://acmepayroll.com",
  "industry": "HR Technology"
}
```

Response `201`:

```json
{
  "organization_id": "org_123",
  "name": "Acme Payroll",
  "industry": "HR Technology",
  "created_date": "2026-07-11T00:00:00Z"
}
```

### POST /sources

Register a knowledge source for an organization (MVP: website).

Request:

```json
{
  "organization_id": "org_123",
  "type": "website",
  "seed_url": "https://acmepayroll.com"
}
```

Response `201`:

```json
{ "source_id": "src_456", "organization_id": "org_123", "type": "website", "status": "registered" }
```

### POST /crawl

Start crawling a source. Async.

Request:

```json
{ "source_id": "src_456" }
```

Response `202`:

```json
{ "job_id": "job_789", "status": "queued" }
```

### GET /crawl/{job_id}

Response `200`:

```json
{
  "job_id": "job_789",
  "status": "running",
  "pages_discovered": 42,
  "pages_processed": 30,
  "stage": "document_intelligence"
}
```

---

## 5. Twin API

### GET /semantic-twin

Query params: `organization_id` (required).

Response `200`:

```json
{
  "organization_id": "org_123",
  "entity_count": 128,
  "relationship_count": 341,
  "claim_count": 76,
  "coverage": { "entity": 0.82, "relationship": 0.67, "evidence": 0.74, "reasoning": 0.61 },
  "last_updated": "2026-07-11T00:00:00Z"
}
```

### GET /entities

Query params: `organization_id`, `type` (optional), `limit`, `cursor`.

Response `200`:

```json
{
  "entities": [
    { "entity_id": "ent_1", "entity_type": "Product", "canonical_name": "Acme Payroll Cloud", "confidence": 0.94 }
  ],
  "next_cursor": null
}
```

### GET /entities/{id}

Response `200`:

```json
{
  "entity_id": "ent_1",
  "entity_type": "Product",
  "canonical_name": "Acme Payroll Cloud",
  "confidence": 0.94,
  "relationships": [
    { "predicate": "integrates_with", "object": "SAP", "confidence": 0.96, "evidence_id": "ev_10" }
  ],
  "claims": [ { "claim_id": "clm_5", "predicate": "certified_for", "object": "SOC2 Type II", "confidence": 0.88 } ]
}
```

### GET /claims and GET /claims/{id}

`GET /claims/{id}` response `200`:

```json
{
  "claim_id": "clm_5",
  "subject": "Acme Payroll Cloud",
  "predicate": "certified_for",
  "object": "SOC2 Type II",
  "confidence": 0.88,
  "evidence": [ { "evidence_id": "ev_11", "source_url": "https://acmepayroll.com/security", "text_span": "We are SOC2 Type II certified." } ],
  "history": [
    { "version": 1, "valid_from": "2025-01-01", "valid_to": "2026-01-01" },
    { "version": 2, "valid_from": "2026-01-01", "valid_to": null }
  ]
}
```

### GET /evidence/{id}

Response `200`:

```json
{
  "evidence_id": "ev_11",
  "source_url": "https://acmepayroll.com/security",
  "document_id": "doc_77",
  "text_span": "We are SOC2 Type II certified.",
  "extraction_date": "2026-07-11T00:00:00Z",
  "model_version": "extractor-v3"
}
```

---

## 6. Reasoning API

### POST /reason

Run a hybrid retrieval + reasoning query over the twin (HRRE).

Request:

```json
{
  "organization_id": "org_123",
  "question": "Who competes with Acme Payroll?",
  "mode": "competitive"
}
```

`mode` ∈ `answer | coverage | competitive | gap | confidence`.

Response `200`:

```json
{
  "question": "Who competes with Acme Payroll?",
  "answer": "Acme Payroll competes with Workday and ADP.",
  "evidence": [ { "evidence_id": "ev_20", "source_url": "...", "text_span": "Alternative to Workday.", "confidence": 0.82 } ],
  "confidence": 0.79,
  "gaps": ["No evidence comparing pricing vs ADP"]
}
```

---

## 6b. Probe API (External AI Testing)

Probes real external assistants (ChatGPT, Claude, Perplexity) with buyer questions and analyzes their answers (HRRE §13). External calls are expensive and non-deterministic, so `/probe` is **async** and results are point-in-time.

### POST /probe

Request:

```json
{
  "organization_id": "org_123",
  "questions": ["What is the best payroll platform for multinational companies?"],
  "targets": ["chatgpt", "claude", "perplexity"],
  "samples_per_question": 3
}
```

`questions` optional — if omitted, uses the org's generated question set (AVAS §3.3). `targets` defaults to all three.

Response `202`:

```json
{ "job_id": "probe_abc", "status": "queued", "target_count": 3, "question_count": 1 }
```

### GET /probe/{job_id}

Response `200`:

```json
{
  "job_id": "probe_abc",
  "status": "done",
  "results": [
    {
      "question": "What is the best payroll platform for multinational companies?",
      "model": "perplexity",
      "sample": 1,
      "answer": "Top options include Workday, ADP, and Acme Payroll ...",
      "organization_mentioned": true,
      "organization_cited": true,
      "competitor_mentions": ["Workday", "ADP"],
      "claim_consistency": "consistent",
      "cited_sources": ["https://acmepayroll.com/global"],
      "latency_ms": 4200,
      "tokens": 812,
      "cost_usd": 0.03,
      "probed_at": "2026-07-11T00:00:00Z"
    }
  ]
}
```

Per MVP decision #4, `competitor_mentions` are **detected from the answer**, not backed by competitor twins.

---

## 7. Application API (AI Visibility)

### GET /visibility-score

Query params: `organization_id`.

Response `200`:

```json
{
  "organization_id": "org_123",
  "overall": 68,
  "scores": { "retrieval": 74, "citation": 55, "reasoning": 61, "trust": 82 },
  "generated_at": "2026-07-11T00:00:00Z"
}
```

### GET /recommendations

Query params: `organization_id`, `limit`, `cursor`.

Response `200`:

```json
{
  "recommendations": [
    {
      "recommendation_id": "rec_1",
      "title": "Add an integrations page listing SAP S/4HANA",
      "missing": { "type": "relationship", "detail": "Product —integrates_with→ SAP S/4HANA has no evidence" },
      "affects": ["reasoning", "citation"],
      "expected_impact": "high",
      "evidence": []
    }
  ],
  "next_cursor": null
}
```

---

## 8. MVP Scope

**Included:** organizations, website sources, crawl jobs, twin summary, entities, claims, evidence, `/reason`, visibility scores, recommendations.

**Excluded:** write/annotation endpoints for human review workflow (governance UI), non-website source registration, bulk export, webhooks (events are internal for MVP).

---

## 9. Key Design Decision

The API is the **only** way into the platform's knowledge. By forcing every consumer through the Twin / Reasoning / Recommendation layers, the platform stays evolvable, enforces tenant isolation and business rules in one place, and guarantees every returned fact carries evidence and confidence.
