# Enterprise Knowledge Intelligence Platform (EKIP)

**Hybrid Retrieval & Reasoning Engine Specification (HRRE)**

- **Version:** 1.0
- **Status:** Foundational Architecture
- **Audience:** AI Engineers, ML Engineers, Backend Engineers, Knowledge Graph Engineers, Platform Architects

---

## 1. Purpose

The Hybrid Retrieval & Reasoning Engine is the layer that operates **over** the Semantic Business Twin to answer questions, evaluate AI answers, and produce explainable, evidence-backed reasoning.

It answers the platform's central runtime question:

> "Given what we know about this organization, what can AI retrieve, cite, and reason about — and how certain are we?"

The engine does not generate marketing copy or free-form answers. It produces **grounded, evidence-linked reasoning** that downstream applications (starting with AI Visibility) consume.

**Two engines, two questions.** AI Visibility is measured by two complementary engines:

1. **Internal Twin Simulation** — *this document (§3–§12)*. Deterministic hybrid retrieval + reasoning over **our own twin**. It answers *"what could AI conclude about this organization given its knowledge, and why?"* — fully explainable and evidence-linked.
2. **External AI Probe** — *§13*. Calls **real AI assistants (ChatGPT, Claude, Perplexity)** with buyer questions and observes their actual answers. It answers *"what does AI actually say about this organization today, and which competitors does it name?"*

The internal engine explains **why**; the external probe measures **reality**. Scores draw on both.

---

## 2. Design Principles

- **Hybrid over single-mode** — no single retrieval method is sufficient. Lexical, semantic, and graph retrieval each cover a different failure mode.
- **Evidence before generation** — the LLM reasons only over retrieved, provenance-tagged evidence, never over its own priors alone.
- **Explainability is mandatory** — every answer carries the evidence and confidence that produced it.
- **The graph is the differentiator** — graph expansion is what turns a pile of chunks into connected business knowledge.

---

## 3. Retrieval Architecture

```
Question
   ↓
┌──────────────────────────────┐
│   BM25 Search  +  Vector Search  │   (parallel)
└──────────────────────────────┘
   ↓
Graph Expansion
   ↓
Reranking
   ↓
Evidence Selection
   ↓
LLM Reasoning
   ↓
Answer + Evidence + Confidence
```

Each stage narrows and enriches the candidate set: lexical + semantic recall, graph-based context, precision reranking, evidence curation, then grounded reasoning.

---

## 4. Stage 1 — Lexical Retrieval (BM25)

- **Source:** OpenSearch BM25 index over normalized chunks.
- **Strength:** exact term and phrase matching — product names, regulation codes (`SOC2`, `HIPAA`), technology names (`SAP S/4HANA`), pricing tokens.
- **Why it exists:** dense vectors routinely miss rare, exact strings. BM25 is the safety net for precise terminology.
- **Output:** ranked chunk IDs with lexical scores.

---

## 5. Stage 2 — Semantic Retrieval (Vector)

- **Source:** Qdrant (or pgvector for MVP) over chunk embeddings.
- **Strength:** meaning-based recall — matches paraphrases and concepts ("payroll compliance" ≈ "wage regulation adherence").
- **Why it exists:** captures intent when the user's words don't match the document's words.
- **Output:** ranked chunk IDs with similarity scores.

BM25 and Vector run in **parallel**; their result sets are merged (union with score normalization) before graph expansion.

---

## 6. Stage 3 — Graph Expansion

This is the step that separates EKIP from conventional RAG.

Retrieved chunks are anchored to entities in the Semantic Business Twin. The engine then traverses the graph to pull in **connected knowledge** the raw text did not surface.

Example:

```
Question: "Can this payroll platform support multinational companies?"

Retrieved chunk anchors → Product: Acme Payroll
Graph expansion pulls:
  Product —supports→ Countries
  Product —complies_with→ GDPR, SOC2
  Product —integrates_with→ SAP, Workday
  Product —provides→ Multi-currency Capability
```

The multi-hop context lets the engine answer questions no single page states directly.

**Guardrails:** bounded hop depth (default 2), confidence-weighted edges, and provenance carried on every expanded node.

---

## 7. Stage 4 — Reranking

The merged + expanded candidate set is reranked for precision.

- **Inputs:** lexical score, semantic score, graph relevance (hop distance + edge confidence), source authority (page classification from KIPS §7), freshness.
- **Method:** cross-encoder reranker or weighted score fusion for MVP.
- **Output:** a small, high-precision, ordered candidate set.

Source authority matters here: for a compliance question, a Security page outranks a blog even at equal semantic similarity.

---

## 8. Stage 5 — Evidence Selection

From the reranked set, the engine curates the **minimal sufficient evidence** to answer the question.

Each selected evidence unit carries:

- Text span
- Source URL + page classification
- Extraction date / freshness
- Confidence (extraction × evidence × freshness — see SBTS §13)
- Linked entities / claims in the twin

If evidence is insufficient, the engine records a **knowledge gap** rather than forcing an answer.

---

## 9. Stage 6 — LLM Reasoning

The LLM receives the curated evidence and the question, and produces a grounded answer.

- The LLM **reasons over evidence**, it does not invent facts.
- Every assertion in the answer maps back to selected evidence.
- Output includes an overall confidence and the evidence set used.

Answer object:

```json
{
  "question": "...",
  "answer": "...",
  "evidence": [ { "evidence_id": "...", "url": "...", "text_span": "...", "confidence": 0.9 } ],
  "confidence": 0.86,
  "gaps": []
}
```

---

## 10. Reasoning Capabilities

The engine exposes four core reasoning modes over the twin.

### 10.1 Coverage Reasoning

> "Do we know enough about this topic?"

Checks entity / relationship / evidence coverage (SBTS §17) for the queried topic. Returns a coverage score and the specific missing links.

### 10.2 Competitive Reasoning

> "Why is competitor X recommended?"

Compares the organization's twin against known competitor entities and claims, and explains which relationships, claims, or evidence drive a competitor's stronger AI representation.

### 10.3 Gap Reasoning

> "What information is missing?"

Identifies the knowledge gaps that prevented a confident answer — entities not present, relationships not established, or claims lacking evidence. Feeds the KIPS continuous learning loop (§21).

### 10.4 Confidence Reasoning

> "How certain are we?"

Aggregates multi-dimensional confidence across the evidence used and explains **why** confidence is high or low (weak source, stale evidence, unresolved contradiction).

---

## 11. Handling Contradictions

When evidence selection surfaces conflicting claims (SBTS §15), the engine does not silently pick one. It:

1. Surfaces both claims with their evidence and confidence.
2. Flags the contradiction's resolution status.
3. Lowers overall answer confidence accordingly.

---

## 12. MVP Scope

For the first release:

- ✓ BM25 (OpenSearch) + Vector (pgvector) hybrid retrieval
- ✓ Single-source-of-truth merge with score normalization
- ✓ Graph expansion up to 2 hops over MVP relationships (`provides`, `integrates_with`, `competes_with`, `solves`, `supports`)
- ✓ Weighted-fusion reranking (cross-encoder optional)
- ✓ Evidence selection with provenance + confidence
- ✓ Coverage, gap, and confidence reasoning
- ✓ Competitive reasoning (basic — presence + claim comparison)
- ✓ **External AI Probe** (§13): ChatGPT, Claude, Perplexity; org-mention, org-citation, competitor-mention detection, claim-consistency check

**Excluded from MVP:** multi-hop reasoning beyond depth 2, learned reranker fine-tuning, real-time streaming reasoning, full competitor twins (probe detects competitor mentions only), Google AI Overviews / Gemini probe targets.

---

## 13. External AI Probe (Live LLM Testing)

The Internal Twin Simulation (§3–§12) tells us what AI *could* conclude from our knowledge. The **External AI Probe** tells us what real AI assistants *actually* say today. Both feed AI Visibility.

### 13.1 Purpose

Answer, empirically:

- Does real AI **find** this organization when asked buyer questions? (retrieval reality)
- Does real AI **cite / mention** it? (citation reality)
- Which **competitors** does real AI name in the same answers? (competitive reality)
- Are the AI's statements **consistent with** our twin's evidence-backed claims? (trust reality)

### 13.2 Probe Targets (MVP)

- **ChatGPT** (OpenAI API)
- **Claude** (Anthropic API)
- **Perplexity** (API — the most search/citation-oriented assistant)

The probe layer is provider-pluggable; targets are added without changing the scoring logic. Google AI Overviews / Gemini are deferred (harder to access programmatically).

### 13.3 Probe Flow

```
Buyer Question (from AVAS question generation)
   ↓
Fan out to each target: ChatGPT, Claude, Perplexity
   ↓
Capture raw answer + any cited sources
   ↓
Analyze answer:
   - Is the organization mentioned?  (our-mention detection)
   - Is the organization cited/linked? (citation detection)
   - Which competitors are named?     (competitor-mention extraction)
   - Do claims agree with our twin?    (consistency check vs. SBTS claims)
   ↓
Store probe_result (per question × per model)
```

### 13.4 Competitor Handling

Per decision #4 of the MVP scope: the probe **detects and counts competitor mentions/citations** in real AI answers — it does **not** build full twins for competitors. This yields competitive signal (who dominates the answer space) cheaply. Full competitor twins are a post-MVP Competitive Intelligence feature.

### 13.5 Cost, Rate Limits & Determinism

External LLM calls are expensive, rate-limited, and **non-deterministic** (answers vary run to run). The probe therefore:

- Runs asynchronously via the event/queue architecture (SAD §18, §21).
- Records per-call latency, tokens, and cost (SAD §19 observability).
- May sample each question multiple times and aggregate, since a single answer is not stable.
- Timestamps every result — external AI answers are a point-in-time measurement, not a fixed fact.

### 13.6 Relationship to the Twin

The External AI Probe **reads** buyer questions derived from the twin and **checks** answers against the twin's claims, but its results are **observations about the outside world**, not knowledge about the organization. Probe results are stored separately (`probe_run` / `probe_result`, see Database Design) and never enter the twin as facts — they inform *scores and recommendations*, consistent with the "LLM proposes, twin decides" principle (KIPS §25).

---

## 14. Key Architectural Decision

Retrieval is hybrid **by necessity**, reasoning is grounded **by mandate**, and measurement is **two-sided by design**.

The engine's value is not that it produces answers — any LLM does that. Its value is that (a) every internal answer is **retrievable, connected through the graph, evidence-backed, and confidence-scored**, and (b) every external answer is **measured against that evidence** — which together make AI Visibility a *provable, explainable* metric rather than an anecdote.
