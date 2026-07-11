# Enterprise Knowledge Intelligence Platform (EKIP)

**AI Visibility Application Specification — MVP (AVAS)**

- **Version:** 1.0
- **Status:** Foundational Architecture
- **Audience:** Product, AI Engineers, Backend Engineers, Frontend Engineers, Founders

---

## 1. Purpose

AI Visibility is the **first commercial application** built on the Semantic Business Twin. It answers, measurably:

- Can AI **retrieve** us?
- Can AI **understand** us?
- Can AI **reason** about us?
- Can AI **cite** us?

It delivers immediate value to product marketing and content teams by turning "how does AI see us?" from intuition into scored, explainable, evidence-backed metrics. It is the flagship application of marketG's **GEO (Generative Engine Optimization)** positioning, with **B2B SaaS** as the beachhead vertical.

AI Visibility is a **consumer of the twin**, not a parallel system. It talks only to the Reasoning, Recommendation, Probe, and Twin APIs — never directly to the graph.

---

## 2. Value Proposition

- Measure AI representation instead of guessing at it.
- Understand **why** competitors dominate AI-generated answers.
- Get **evidence-backed recommendations** that improve the twin (and therefore AI's understanding).
- Build a reusable semantic asset as a byproduct.

---

## 3. User Workflow

```
Add Website
   ↓
Build Twin
   ↓
Generate Questions
   ↓
Run AI Simulations
   ↓
Analyze Answers
   ↓
Generate Recommendations
```

### 3.1 Add Website

User enters a domain. The system registers the organization and seeds the crawler (KIPS §5–7).

### 3.2 Build Twin

The Knowledge Intelligence Pipeline runs end-to-end: crawl → document intelligence → semantic chunking → multi-agent extraction → governance → Twin update. Progress is reported per stage (event-driven, SAD §18).

Output: a populated Semantic Business Twin with entities, relationships, claims, evidence, and confidence.

### 3.3 Generate Questions

The system generates a representative set of buyer- and analyst-style questions the organization *should* be findable for.

Examples:

- "What is the best payroll platform for multinational companies?"
- "Which CRM integrates with SAP?"
- "Is [Product] SOC2 certified?"
- "Compare [Product] and [Competitor]."

Questions are derived from the twin (products, capabilities, industries, competitors) plus common category intents.

### 3.4 Run AI Simulations

Each question is measured **two ways** (HRRE §1 "Two engines"):

1. **Internal Twin Simulation** — run through the Hybrid Retrieval & Reasoning Engine against the twin, showing how an AI *could* retrieve, reason, and answer from the organization's knowledge. Deterministic and fully explainable (the *why*).
2. **External AI Probe** — the same question is sent to **real AI assistants (ChatGPT, Claude, Perplexity)**, and their actual answers are captured and analyzed: is the organization mentioned? cited? which competitors are named? do the statements match our twin's evidence? (HRRE §13 — the *reality*.)

Per MVP decision #4, competitor handling is **mention/citation detection in real AI answers**, not full competitor twins.

### 3.5 Analyze Answers

For every question the system evaluates the four visibility metrics (§4) across both engines and records the evidence, gaps, contradictions, and real-AI answers (with competitor mentions) that drove the result.

### 3.6 Generate Recommendations

Evidence-backed recommendations are produced from the gaps and weaknesses found — each tied to a specific missing entity, relationship, claim, or weak-evidence source.

---

## 4. Metrics

Four scores form the AI Visibility index. Each is 0–100, explainable, and traceable to evidence. Each score declares which engine produces it — **Internal** (twin simulation, HRRE §3–12), **External** (live AI probe, HRRE §13), or **Both**.

### 4.1 Retrieval Score — *Can AI find us?* · **Internal + External**

Internal: whether the organization's knowledge is retrievable for relevant questions (hybrid retrieval recall). External: whether real assistants surface the organization at all when asked those questions. Low score → the twin lacks content / isn't connected for that intent, and/or real AI doesn't find it.

### 4.2 Citation Score — *Does AI mention us?* · **External (primary)**

Measures how often the organization / product is mentioned or cited by **real AI assistants** (ChatGPT, Claude, Perplexity), versus how often competitors are named in the same answers. Low score → competitors dominate the real answer space for that topic. This is the score that most directly proves GEO impact.

### 4.3 Reasoning Score — *Can AI answer complex questions about us?* · **Internal (primary)**

Measures the ability to answer multi-hop questions (e.g. "does it support multinational payroll?") using graph-connected knowledge. Low score → relationships/coverage are missing (HRRE coverage reasoning). Cross-checked against whether real AI can reason to the same conclusion.

### 4.4 Trust Score — *Does evidence support claims?* · **Both**

Internal: how well the organization's claims are backed by strong, fresh, non-contradictory evidence (SBTS confidence + contradiction management). External: whether real AI's statements about the organization are *consistent* with that evidence. Low score → unsupported claims, stale sources, unresolved conflicts, or real AI asserting things our evidence doesn't support.

**Overall AI Visibility Score** = weighted composite of the four, with the breakdown always shown.

---

## 5. Recommendations

Every recommendation must be **evidence-backed** and tied to a concrete twin improvement (mirrors PRD Design Principles).

Each recommendation includes:

- **What's missing / weak** — the specific entity, relationship, claim, or source.
- **Why it matters** — which metric it depresses and for which questions.
- **Suggested action** — e.g. "publish an integrations page listing SAP S/4HANA," "add evidence for the SOC2 claim," "resolve pricing contradiction between marketing and docs."
- **Expected impact** — which score(s) improve.

Recommendations are ranked by expected visibility impact.

---

## 6. Application Architecture (consumes services only)

```
AI Visibility App
   ↓
Recommendation API
   ↓
Reasoning API (HRRE — internal)  +  Probe API (HRRE §13 — external LLMs)
   ↓
Twin API
```

No application logic reaches into Neo4j / pgvector directly. This keeps the app evolvable and enforces business rules at the service boundary (SAD §17).

---

## 7. MVP Scope

**Included:**

- ✓ Single-website ingestion → twin build (website connector; pluggable for future sources)
- ✓ Automated question generation from the twin + B2B SaaS category intents
- ✓ Internal twin simulation via HRRE
- ✓ External AI probing of ChatGPT, Claude, Perplexity (real answers captured + analyzed)
- ✓ Competitor mention/citation detection from real AI answers (no full competitor twins)
- ✓ Four visibility scores with breakdowns (each tagged Internal / External / Both)
- ✓ Evidence-backed, ranked recommendations
- ✓ Dashboard: scores, per-question detail, evidence, real-AI answers, recommendations

**Excluded (per PRD MVP definition):**

- Internal enterprise connectors
- Multi-language support
- Automated content generation
- Workflow automation
- Enterprise governance features

---

## 8. Success Metrics (product)

- Time to build a twin and produce the first visibility report.
- Recommendation acceptance rate.
- AI Visibility score improvement over time as recommendations are applied.
- Reduction in detected knowledge gaps per re-crawl.

---

## 9. Key Product Thesis

Conventional AI-SEO tools ask *"which pages should I optimize?"* AI Visibility asks *"what does AI know about this organization, how certain is it, and what specific knowledge would change the answer?"* — and it can prove the answer because it is built on the governed, evidence-backed twin.
