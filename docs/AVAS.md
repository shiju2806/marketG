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

It delivers immediate value to product marketing and content teams by turning "how does AI see us?" from intuition into scored, explainable, evidence-backed metrics.

AI Visibility is a **consumer of the twin**, not a parallel system. It talks only to the Reasoning, Recommendation, and Twin APIs — never directly to the graph.

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

Each question is run through the Hybrid Retrieval & Reasoning Engine (HRRE) against the twin, simulating how an AI assistant would retrieve, reason, and answer using the organization's knowledge.

### 3.5 Analyze Answers

For every simulated answer the system evaluates the four visibility metrics (§4) and records the evidence, gaps, and contradictions that drove the result.

### 3.6 Generate Recommendations

Evidence-backed recommendations are produced from the gaps and weaknesses found — each tied to a specific missing entity, relationship, claim, or weak-evidence source.

---

## 4. Metrics

Four scores form the AI Visibility index. Each is 0–100, explainable, and traceable to evidence.

### 4.1 Retrieval Score — *Can AI find us?*

Measures whether the organization's knowledge is retrievable for relevant questions (hybrid retrieval recall). Low score → the twin lacks content or the content isn't indexed/connected for that intent.

### 4.2 Citation Score — *Does AI mention us?*

Measures how often the organization / product appears as a cited source in the simulated answers, versus competitors. Low score → competitors dominate the answer space for that topic.

### 4.3 Reasoning Score — *Can AI answer complex questions about us?*

Measures the engine's ability to answer multi-hop questions (e.g. "does it support multinational payroll?") using graph-connected knowledge. Low score → relationships/coverage are missing (HRRE coverage reasoning).

### 4.4 Trust Score — *Does evidence support claims?*

Measures how well the organization's claims are backed by strong, fresh, non-contradictory evidence (SBTS confidence + contradiction management). Low score → unsupported claims, stale sources, or unresolved conflicts.

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
Reasoning API   (HRRE)
   ↓
Twin API
```

No application logic reaches into Neo4j / pgvector directly. This keeps the app evolvable and enforces business rules at the service boundary (SAD §17).

---

## 7. MVP Scope

**Included:**

- ✓ Single-website ingestion → twin build
- ✓ Automated question generation from the twin + category intents
- ✓ Retrieval simulation via HRRE
- ✓ Four visibility scores with breakdowns
- ✓ Evidence-backed, ranked recommendations
- ✓ Basic competitive comparison (presence + citation share)
- ✓ Dashboard: scores, per-question detail, evidence, recommendations

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
