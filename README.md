# marketG — Enterprise Knowledge Intelligence Platform (EKIP)

marketG is a **GEO (Generative Engine Optimization)** platform — the successor to SEO. Where SEO optimized web pages for search engines, GEO optimizes an organization's *knowledge* for AI assistants.

We build the world's most accurate machine-readable representation of organizational knowledge — a continuously evolving **Semantic Business Twin (SBT)** that AI systems can reliably retrieve, reason over, and cite.

The first commercial application is **AI Visibility**: measuring whether AI can retrieve, understand, reason about, and cite an organization — both by simulating our own twin *and* by probing real AI assistants (ChatGPT, Claude, Perplexity). Beachhead vertical: **B2B SaaS**.

## Documentation

- [Product Requirements Document](docs/PRD.md) — vision, strategy, pillars, personas, MVP scope.
- [System Architecture Document](docs/SAD.md) — layers, storage, pipeline, semantic twin, governance.
- [Semantic Business Twin Specification](docs/SBTS.md) — data model, entities, relationships, claims, evidence, confidence.
- [Knowledge Intelligence Pipeline Specification](docs/KIPS.md) — acquisition, document intelligence, semantic chunking, multi-agent extraction, governance, learning loop.
- [Hybrid Retrieval & Reasoning Engine](docs/HRRE.md) — hybrid retrieval, graph expansion, evidence selection, reasoning modes.
- [AI Visibility Application Spec (MVP)](docs/AVAS.md) — the first product: user workflow and the four visibility scores.
- [API Specification](docs/API_SPEC.md) — Twin, Reasoning, Recommendation, and Ingestion HTTP interfaces.
- [Database Design](docs/DATABASE_DESIGN.md) — polyglot schemas: PostgreSQL, Neo4j, vector, search, object storage.
- [MVP Engineering Roadmap](docs/MVP_ROADMAP.md) — sprint-by-sprint implementation plan.
- [Glossary & Concept Map](docs/GLOSSARY.md) — shared vocabulary; **start here** to understand the terms.
- [Technology Stack (MVP vs. Target)](docs/TECH_STACK.md) — the concrete stack we build first and how it scales.
- [Domain Model & ADRs](docs/DOMAIN_MODEL_AND_ADRS.md) — **locked pre-build decisions**; the schema follows this.
- Pilots: [GM](docs/pilots/gm-ai-visibility-pilot.md) · [Rivian](docs/pilots/rivian-ai-visibility-pilot.md) · [GM-vs-Rivian one-pager](docs/pilots/gm-vs-rivian-onepager.html) — hypothesis validation.

## Status

Foundational architecture. Repository scaffolding in progress.
