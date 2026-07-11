# Enterprise Knowledge Intelligence Platform (EKIP)

**Glossary & Concept Map**

- **Version:** 1.0
- **Status:** Foundational Architecture
- **Audience:** Everyone touching the product — engineers, product, founders, new hires
- **Purpose:** One shared vocabulary. If a term is used in code, specs, or conversation, its plain meaning is here. This is the drift-prevention document — read it before writing code.

---

## 1. The One-Paragraph Version

marketG builds a **Semantic Business Twin** — a continuously-updated, machine-readable mirror of what a company knows and claims about itself, with **evidence** and **confidence** attached to every fact. The first product on top of it, **AI Visibility**, measures how well AI assistants can find, understand, cite, and reason about that company — both by **simulating** our own twin and by **probing** real assistants (ChatGPT, Claude, Perplexity). This is **GEO** — the successor to SEO.

---

## 2. Product & Positioning Terms

| Term | Plain meaning |
|------|---------------|
| **marketG** | The product / company name. The repo. |
| **EKIP** | Enterprise Knowledge Intelligence Platform — the formal name for the whole platform. |
| **GEO** | *Generative Engine Optimization.* The category. Where **SEO** optimized web pages for search engines, **GEO** optimizes an organization's *knowledge* so AI assistants find, understand, and recommend it. We sell GEO in place of SEO tools. |
| **AI Visibility** | The first commercial application. Answers: can AI *retrieve, understand, reason about, and cite* us? Produces four scores + recommendations. |
| **Beachhead** | The first vertical we focus on: **B2B SaaS**. |

---

## 3. The Core Concept: Semantic Business Twin

### Semantic Business Twin (SBT) — a.k.a. "the twin"

The heart of the product. Borrowed from **"digital twin"** (a live virtual replica of a physical machine). Here it's a live, machine-readable replica of **what a company *is*** — its products, capabilities, claims, integrations, competitors, compliance — not the documents it publishes.

- **Semantic** → meaning-based & machine-readable (structured entities/relationships/claims, not prose).
- **Business** → models the business itself.
- **Twin** → a living mirror that evolves as the company's real knowledge changes.

**Plain-English synonym for internal use:** an *evidence-backed knowledge graph of the business*. If the website is the company's story, the twin is its structured, fact-checked profile that an AI can query.

> **Rule:** nothing enters the twin without evidence. The LLM *proposes* knowledge; the governed twin *decides* whether it's trustworthy enough to keep.

---

## 4. The Knowledge Model (what's inside the twin)

These five distinctions are the most important in the whole system. Getting them right in code prevents most confusion.

| Term | Plain meaning | Example |
|------|---------------|---------|
| **Entity** | A *thing* that exists in the business domain. | `Acme Payroll` (Organization), `SAP` (Technology), `Workday` (Competitor) |
| **Relationship** | A *connection* between two entities. First-class: it carries its own evidence & confidence. | `Acme Payroll —integrates_with→ SAP` |
| **Claim** | A *statement / assertion* about reality that could be true, false, versioned, or contradicted. **A claim is NOT an entity.** | "SOC2 certified", "reduces payroll time by 50%" |
| **Evidence** | The *proof* a fact came from — the source text span, URL, section, date, extraction model. Every entity/relationship/claim traces to evidence. | The sentence *"We are SOC2 Type II certified"* on `/security`, extracted 2026-07-11 |
| **Provenance** | The *lineage* of a fact: who/what created it (which model version), from which source, when, validated by whom. | "Created by Entity Extraction Model v3, human-approved" |

### Why Claim ≠ Entity (the distinction people trip on)

- An **entity** just *exists* (`SOC2` is a regulation).
- A **claim** *asserts something* about an entity (`Acme is_certified SOC2`) — and that assertion can be wrong, expire, or conflict with another source.

Claims are the thing GEO/AI-Visibility actually cares about, because they're what AI repeats or gets wrong.

---

## 5. Trust & Change Over Time

| Term | Plain meaning |
|------|---------------|
| **Confidence** | *How much we trust a fact* — and it's **multi-dimensional**, not one number: **Extraction** (how sure was the AI?), **Evidence** (how authoritative the source?), **Freshness** (how recent?), and an **Overall** blend. |
| **Versioning** | Knowledge is **immutable**; new information creates a *new version* and marks the old one's validity window. History is never destroyed. |
| **Temporal validity** | Every fact has a *valid_from / valid_to*. "Supported SAP ECC in 2025" and "supports SAP S/4HANA in 2026" both exist historically. |
| **Contradiction / Conflict** | When two sources disagree (pricing page says $99, docs say $149), the system records a **Conflict** with status `pending_review` instead of silently picking one. |
| **Ontology** | The *canonical vocabulary* that stops chaos. Maps `SAP`, `SAP ERP`, `S/4`, `S4 HANA` → one canonical `SAP S/4HANA → ERP → Enterprise Software`. |

---

## 6. How Knowledge Gets Built (the pipeline)

| Term | Plain meaning |
|------|---------------|
| **Connector** | A source adapter. Outputs a **Raw Document** only, no intelligence. MVP has one: the **website connector**. Pluggable so industry/open/paid sources add later. |
| **Raw Document** | Unprocessed captured content (HTML/PDF), stored immutably. |
| **Semantic Chunk** | A retrieval unit segmented by **business concept** (Pricing, Security, Integrations), *not* by fixed token count. The concept is the unit. |
| **Knowledge Extraction** | Turning chunks into entities/relationships/claims via specialized **extraction agents** (Entity, Relationship, Claim, Use Case, Competitive). |
| **Knowledge Governance** | The gate between raw extraction and the twin: dedupe, conflict detection, confidence calculation, human-review thresholds. Turns *extracted info* into *trusted knowledge*. |
| **Entity Resolution** | Deciding whether an extracted entity is *new* or *the same as* one already in the twin (dedupe + canonicalize). |

---

## 7. How AI Visibility Is Measured (the two engines)

**This is the single most important architectural distinction to keep straight.** There are two separate engines answering two different questions.

| Engine | Question it answers | Nature |
|--------|--------------------|--------|
| **Internal Twin Simulation** (HRRE §3–12) | "What *could* AI conclude about this company from its knowledge — and *why*?" | Deterministic, explainable, runs over **our own twin**. |
| **External AI Probe** (HRRE §13) | "What does real AI *actually* say today — and who does it name instead of us?" | Empirical, non-deterministic, calls **real assistants** (ChatGPT, Claude, Perplexity). |

> **Critical rule:** External probe results are *observations about the outside world*. They **never enter the twin as facts** — they only inform scores and recommendations. (Same "LLM proposes, twin decides" principle, applied to external LLMs.)

### Supporting retrieval terms

| Term | Plain meaning |
|------|---------------|
| **Hybrid Retrieval** | Combining **BM25** (exact keyword) + **Vector** (meaning) search, then **Graph Expansion**, then reranking. No single method is enough. |
| **BM25 / Lexical** | Exact term matching — catches precise strings like `SOC2`, `SAP S/4HANA`. |
| **Vector / Semantic** | Meaning-based matching — catches paraphrases. |
| **Graph Expansion** | Pulling in *connected* knowledge from the twin's graph that raw text didn't state (the step that separates us from plain RAG). |
| **Evidence Selection** | Choosing the minimal sufficient evidence to answer — or recording a **knowledge gap** if there isn't enough. |
| **Reasoning Modes** | Coverage ("do we know enough?"), Gap ("what's missing?"), Confidence ("how sure?"), Competitive ("why does rival X win?"). |

---

## 8. The Four Scores (AI Visibility output)

Each is 0–100, explainable, evidence-traceable. Each is produced by a specific engine.

| Score | Question | Engine |
|-------|----------|--------|
| **Retrieval Score** | Can AI *find* us? | Internal + External |
| **Citation Score** | Does AI *mention / cite* us (vs. competitors)? | **External** (primary) |
| **Reasoning Score** | Can AI answer *complex* questions about us? | **Internal** (primary) |
| **Trust Score** | Is our evidence *strong enough* to back the claims? | Both |
| **Overall** | Weighted composite, breakdown always shown. | — |

---

## 9. Application & Delivery Terms

| Term | Plain meaning |
|------|---------------|
| **Recommendation** | An evidence-backed, ranked suggestion tied to a *specific* twin gap ("add an integrations page listing SAP S/4HANA — raises Reasoning + Citation"). |
| **Knowledge Gap** | A missing entity/relationship/claim/evidence that prevented a confident answer. Feeds recommendations and the learning loop. |
| **Competitor Mention** | A rival named/cited in a *real AI answer*. MVP detects these; it does **not** build full twins for competitors. |
| **Twin API / Reasoning API / Probe API / Recommendation API** | The service layer. Applications talk *only* to these — never directly to the database. |
| **Tenant** | An isolation boundary — one marketG customer. Every stored object carries a `tenant_id`. |

---

## 10. Concept Map (how it all connects)

```
                Website  ──connector──►  Raw Document
                                              │
                                     Semantic Chunking
                                              │
                            Extraction Agents (Entity / Relationship / Claim ...)
                                              │
                                   Knowledge Governance   ◄── evidence + confidence
                                     (dedupe / conflict / threshold)
                                              │
                                              ▼
                             ┌────────────────────────────────┐
                             │      SEMANTIC BUSINESS TWIN     │
                             │  Entities · Relationships ·     │
                             │  Claims · Evidence · Confidence ·│
                             │  Versions · Ontology            │
                             └────────────────────────────────┘
                                              │
                     ┌────────────────────────┴────────────────────────┐
                     ▼                                                  ▼
        Internal Twin Simulation                            External AI Probe
        (retrieval + reasoning,                          (ChatGPT / Claude / Perplexity,
         explains WHY)                                    measures REALITY + competitors)
                     └────────────────────────┬────────────────────────┘
                                              ▼
                             Four Scores + Evidence-backed Recommendations
                                              ▼
                                     AI Visibility (the app)  ==  GEO
```

---

## 11. Terms We Deliberately Avoid Confusing

- **Twin vs. Document store** — the twin models *knowledge*; a document store just holds *pages*. We are not the latter.
- **Claim vs. Fact vs. Entity** — a claim is an *assertion* (may be false); an entity is a *thing*; a fact is a claim we've validated with strong evidence.
- **Internal simulation vs. External probe** — the former is *our twin reasoning*; the latter is *real AI answering*. Different engines, different tables, different guarantees.
- **GEO vs. SEO** — SEO optimizes pages for crawlers; GEO optimizes knowledge for AI assistants. Our whole pitch lives in this distinction.
