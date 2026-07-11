# Enterprise Knowledge Intelligence Platform (EKIP)

**Database Design**

- **Version:** 1.0
- **Status:** Foundational Architecture
- **Audience:** Data Engineers, Backend Engineers, Knowledge Graph Engineers, Platform Architects, DBAs

---

## 1. Purpose

This document defines the concrete schemas across the platform's **polyglot persistence** layer (SAD §6). Different data lives in the store optimized for it:

| Store | Holds | Role |
|-------|-------|------|
| PostgreSQL | organizations, users, sources, jobs, entities, claims, evidence metadata, versions, conflicts, recommendations, scores | System of record + application data |
| Object Storage | raw HTML, PDFs, crawl artifacts | Immutable evidence documents |
| Vector DB (pgvector / Qdrant) | chunk embeddings | Semantic retrieval |
| Neo4j | the Semantic Business Graph | Relationship traversal / reasoning |
| OpenSearch | BM25 index over chunks | Lexical retrieval |

PostgreSQL is the durable source of truth; Neo4j, the vector DB, and OpenSearch are **projections** built from it and are rebuildable.

---

## 2. Design Principles

- **Every knowledge object carries tenant + provenance + confidence** (SBTS §2, SAD §20).
- **Knowledge is immutable and versioned** — updates create new versions; history is never destroyed (SBTS §14).
- **Claims are separate from entities** — they can be validated, versioned, and contradicted (SBTS §4).
- **Evidence is first-class** — nothing enters the twin without a traceable evidence row (SBTS §2, Principle 2).

---

## 3. PostgreSQL Schema

All tables include `tenant_id` for isolation (omitted from individual field lists below for brevity, present on every table).

### 3.1 organization

| Column | Type | Notes |
|--------|------|-------|
| organization_id | UUID PK | |
| name | TEXT | |
| industry | TEXT | |
| website | TEXT | |
| created_date | TIMESTAMPTZ | |

### 3.2 users

| Column | Type | Notes |
|--------|------|-------|
| user_id | UUID PK | |
| organization_id | UUID FK → organization | |
| email | TEXT UNIQUE | |
| role | TEXT | admin / analyst / reviewer |
| created_date | TIMESTAMPTZ | |

### 3.3 source

| Column | Type | Notes |
|--------|------|-------|
| source_id | UUID PK | |
| organization_id | UUID FK → organization | |
| type | TEXT | `website` (MVP) |
| seed_url | TEXT | |
| status | TEXT | registered / crawling / done |
| created_date | TIMESTAMPTZ | |

### 3.4 job

Tracks async work (crawl, extraction, twin build).

| Column | Type | Notes |
|--------|------|-------|
| job_id | UUID PK | |
| organization_id | UUID FK | |
| source_id | UUID FK → source | nullable |
| type | TEXT | crawl / extract / twin_update |
| status | TEXT | queued / running / done / failed |
| stage | TEXT | current pipeline stage |
| metrics | JSONB | latency, tokens, cost, counts |
| created_date | TIMESTAMPTZ | |
| updated_date | TIMESTAMPTZ | |

### 3.5 document

Metadata for a crawled/ingested document; the bytes live in object storage.

| Column | Type | Notes |
|--------|------|-------|
| document_id | UUID PK | |
| source_id | UUID FK → source | |
| url | TEXT | |
| page_classification | TEXT | homepage / product / pricing / security / … (KIPS §7) |
| object_storage_key | TEXT | immutable raw artifact |
| content_hash | TEXT | change detection |
| crawled_at | TIMESTAMPTZ | |

### 3.6 chunk

Semantic chunk (KIPS §11). Embedding lives in the vector store; this row holds metadata + linkage.

| Column | Type | Notes |
|--------|------|-------|
| chunk_id | UUID PK | |
| document_id | UUID FK → document | |
| type | TEXT | integration_capability / security_compliance / … |
| text | TEXT | |
| vector_ref | TEXT | id in vector store |
| created_date | TIMESTAMPTZ | |

### 3.7 entity

| Column | Type | Notes |
|--------|------|-------|
| entity_id | UUID PK | |
| organization_id | UUID FK | |
| entity_type | TEXT | Organization / Product / Feature / Technology / Integration / Industry / Competitor |
| canonical_name | TEXT | post entity-resolution name |
| aliases | TEXT[] | |
| ontology_ref | TEXT | canonical ontology id (SBTS §16) |
| confidence | NUMERIC(3,2) | |
| created_by | TEXT | model version / human |
| validated | TEXT | auto / human_approved / pending |
| created_date | TIMESTAMPTZ | |

### 3.8 claim

Claims are separate from entities (SBTS §4).

| Column | Type | Notes |
|--------|------|-------|
| claim_id | UUID PK | |
| organization_id | UUID FK | |
| subject | TEXT | entity_id or canonical name |
| predicate | TEXT | certified_for / reduces / supports / … |
| object | TEXT | |
| value | TEXT | e.g. "50%" (nullable) |
| claim_type | TEXT | capability / performance / compliance / market / competitive |
| evidence_id | UUID FK → evidence | primary evidence |
| confidence | NUMERIC(3,2) | overall |
| version | INT | |
| valid_from | DATE | |
| valid_to | DATE | nullable = current |
| created_date | TIMESTAMPTZ | |

### 3.9 evidence

| Column | Type | Notes |
|--------|------|-------|
| evidence_id | UUID PK | |
| organization_id | UUID FK | |
| source_url | TEXT | |
| document_id | UUID FK → document | |
| text_span | TEXT | |
| section | TEXT | e.g. "Compliance" |
| extraction_date | TIMESTAMPTZ | |
| model_version | TEXT | |
| timestamp | TIMESTAMPTZ | evidence capture time |

### 3.10 relationship

Relationships are first-class (SBTS §7). The authoritative traversal copy lives in Neo4j; this table is the durable, versioned record.

| Column | Type | Notes |
|--------|------|-------|
| relationship_id | UUID PK | |
| organization_id | UUID FK | |
| subject_entity_id | UUID FK → entity | |
| predicate | TEXT | provides / integrates_with / competes_with / solves / supports |
| object_entity_id | UUID FK → entity | |
| evidence_id | UUID FK → evidence | |
| confidence | NUMERIC(3,2) | |
| version | INT | |
| valid_from | DATE | |
| valid_to | DATE | nullable = current |
| created_date | TIMESTAMPTZ | |

### 3.11 confidence_metadata

Multi-dimensional confidence (SBTS §13), referenced by entity / claim / relationship.

| Column | Type | Notes |
|--------|------|-------|
| confidence_id | UUID PK | |
| object_type | TEXT | entity / claim / relationship |
| object_id | UUID | |
| extraction | NUMERIC(3,2) | |
| evidence | NUMERIC(3,2) | |
| freshness | NUMERIC(3,2) | |
| overall | NUMERIC(3,2) | |
| computed_at | TIMESTAMPTZ | |

### 3.12 conflict

Contradiction management (SBTS §15, KIPS §17).

| Column | Type | Notes |
|--------|------|-------|
| conflict_id | UUID PK | |
| organization_id | UUID FK | |
| object_type | TEXT | claim / relationship |
| object_a_id | UUID | |
| object_b_id | UUID | |
| description | TEXT | |
| resolution_status | TEXT | pending_review / resolved / dismissed |
| resolved_by | TEXT | nullable |
| created_date | TIMESTAMPTZ | |

### 3.13 visibility_score

| Column | Type | Notes |
|--------|------|-------|
| score_id | UUID PK | |
| organization_id | UUID FK | |
| retrieval | INT | 0–100 |
| citation | INT | 0–100 |
| reasoning | INT | 0–100 |
| trust | INT | 0–100 |
| overall | INT | 0–100 |
| generated_at | TIMESTAMPTZ | |

### 3.14 recommendation

| Column | Type | Notes |
|--------|------|-------|
| recommendation_id | UUID PK | |
| organization_id | UUID FK | |
| title | TEXT | |
| missing_type | TEXT | entity / relationship / claim / evidence |
| missing_detail | TEXT | |
| affects | TEXT[] | which scores |
| expected_impact | TEXT | high / medium / low |
| status | TEXT | open / applied / dismissed |
| created_date | TIMESTAMPTZ | |

---

## 4. Neo4j — Semantic Business Graph

Nodes and relationships projected from PostgreSQL; used for multi-hop reasoning and graph expansion (HRRE §6).

**Node labels:** `Organization`, `Product`, `Capability`, `Feature`, `Technology`, `Integration`, `Industry`, `Regulation`, `Competitor`, `CustomerProblem`, `UseCase`.

Node properties (all): `entity_id`, `canonical_name`, `ontology_ref`, `confidence`, `tenant_id`.

**Relationship types (MVP):** `PROVIDES`, `CONTAINS`, `INTEGRATES_WITH`, `COMPETES_WITH`, `USED_BY`, `SOLVES`, `SUPPORTS`, `COMPLIES_WITH`.

Relationship properties: `relationship_id`, `confidence`, `evidence_id`, `valid_from`, `valid_to`, `version`.

Example Cypher:

```cypher
MATCH (p:Product {entity_id: $id})-[r:INTEGRATES_WITH]->(t)
WHERE r.valid_to IS NULL
RETURN t.canonical_name, r.confidence, r.evidence_id
```

---

## 5. Vector Store (pgvector / Qdrant)

One record per chunk:

- `chunk_id` (matches PostgreSQL `chunk.chunk_id`)
- `embedding` (vector)
- payload: `organization_id`, `document_id`, `chunk_type`, `entity_ids[]`, `page_classification`

Used by HRRE Stage 2 (semantic retrieval).

---

## 6. OpenSearch (BM25 Index)

One document per chunk for lexical retrieval:

- `chunk_id`, `organization_id`, `text`, `chunk_type`, `page_classification`, `entity_names[]`

Used by HRRE Stage 1.

---

## 7. Object Storage

Immutable raw artifacts, keyed by `object_storage_key` from the `document` table:

```
{tenant_id}/{source_id}/{document_id}/raw.html
{tenant_id}/{source_id}/{document_id}/raw.pdf
```

Never modified. Re-crawls create new documents with new keys and a new `content_hash`.

---

## 8. Referential & Lifecycle Rules

- Deleting an organization cascades to its sources, documents, chunks, entities, claims, relationships, evidence, scores, and recommendations (tenant teardown).
- Entities/claims/relationships are **never hard-deleted** on update — a new version is written and the prior version's `valid_to` is set.
- Evidence rows are immutable once written.
- Neo4j / vector / OpenSearch are rebuildable projections; PostgreSQL is authoritative.

---

## 9. MVP Scope

**Included:** all PostgreSQL tables above, Neo4j MVP node/relationship types, pgvector chunk index, OpenSearch chunk index, object storage layout.

**Excluded:** partitioning/sharding strategy, read replicas, per-tenant physical isolation, financial/customer/employee entity tables (future extensions per SBTS §20).

---

## 10. Key Design Decision

PostgreSQL is the **single durable source of truth** with full provenance and versioning; the graph, vector, and search stores are performance-optimized **projections**. This keeps knowledge auditable and rebuildable — any projection can be dropped and regenerated from Postgres without losing a single evidence-backed fact.
