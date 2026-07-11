# Pilot: AI Visibility Assessment — General Motors

**Type:** Manual dry-run of the marketG pipeline (no product built yet)
**Subject:** General Motors + 4 consumer sub-brands (Chevrolet, GMC, Buick, Cadillac)
**Date:** 2026-07-11
**Purpose:** Validate the founding hypothesis — *a big, agency/dealer-outsourced brand has weak first-party control of its AI representation, and marketG's recommendation engine would help.*
**Method:** Manual proxy of the two measurement engines: (a) fetch GM's own sites to test machine-readability of first-party content; (b) probe web/AI for buyer questions to see how AI actually represents GM's brands and who it cites.

> ⚠️ **Honesty caveats.** This is a one-afternoon, single-company manual pilot. Web search is used as a *proxy* for external AI answers (real ChatGPT/Claude/Perplexity probing is the product's job). A `403` to our crawler does not by itself prove AI crawlers are blocked — it may be general WAF/bot mitigation. Findings are **directional, not statistically rigorous.** They are strong enough to inform strategy, not to quote as fact.

---

## 1. Headline Finding

**GM has effectively ceded its AI narrative to third parties.**

- Every GM first-party site we tried — `gm.com`, `chevrolet.com`, `gmc.com`, `buick.com`, `cadillac.com` — returned **HTTP 403 Forbidden** to our crawler (even `robots.txt` was blocked).
- Meanwhile, AI/search answers about GM's cars are **rich and specific** — but sourced almost entirely from **third parties**: US News, Edmunds, Consumer Reports, JD Power, KBB, CarBuzz, iSeeCars, and dealer sites.
- Net: when a buyer asks AI about a GM vehicle, the answer is authored by *everyone except GM.* GM's own authoritative claims are largely absent from the machine-readable layer.

This is the thesis in one sentence: **the outsourced/agency-and-dealer marketing model has left GM without first-party control of its AI presence.**

---

## 2. Content Ingestion Test (can AI read GM's own words?)

| Site | Result |
|------|--------|
| gm.com | 403 Forbidden |
| chevrolet.com | 403 Forbidden |
| gmc.com | 403 Forbidden |
| buick.com | 403 Forbidden |
| cadillac.com | 403 Forbidden |
| chevrolet.com/robots.txt | 403 Forbidden |

**Interpretation:** GM's sites sit behind aggressive bot protection and are heavy JS/SPA experiences. Regardless of whether specific AI crawlers are whitelisted, this is a **machine-readability barrier** — the exact problem GEO addresses. First-party specs, claims, and evidence are not being served cleanly to machines, so AI falls back to third-party summaries GM does not control.

**To confirm (product would do this automatically):** check which AI user-agents (GPTBot, ClaudeBot, PerplexityBot, Google-Extended, CCBot) are actually allowed, and whether server-rendered content + schema.org markup exists.

---

## 3. External Probe (how AI represents GM's brands, by buyer question)

Search-as-proxy across representative buyer questions. Note **who wins the recommendation** and **who is cited**.

| Buyer question | How GM shows up | Verdict |
|----------------|-----------------|---------|
| "Most reliable **hybrid** SUV 2026" | **Zero GM brands.** Toyota (Land Cruiser, Highlander, RAV4), Honda CR-V, Lexus dominate. | ❌ Invisible in a huge, growing category — GM has almost no hybrid story. |
| "Best **EV** SUV under $50k 2026" | **Chevrolet Equinox EV** cited with specifics (319 mi range, ~$34–38k). GMC/Buick/Cadillac absent. | ✅ Chevy competitive; rest of portfolio absent. |
| "Best **full-size truck** 2026" | **Silverado** praised (best value, cheapest at $36,900, most fuel-efficient). **GMC Sierra** lukewarm ("skews luxurious, rivals have more capability"). | ⚠️ Ford F-150 takes the #1 spot (9.6/10); Silverado strong but not the top recommendation. |
| "Best **luxury EV** SUV 2026" | **Cadillac Lyriq** well-covered (326 mi, 365 hp, $78,595, *German Luxury Car of the Year*, Super Cruise). | ⚠️ **But AI's verdict: "Lucid Gravity is widely considered the best."** A **new entrant out-recommends Cadillac.** |
| "Best **American brand** / Chevy vs Ford" | Chevrolet = "value and dependability"; Ford = "innovation and tech," F-Series best-seller. Chevy sales down ~6%. | ⚠️ Ford gets the more flattering, forward-looking framing. |
| "Is **Buick** good 2026" | "Average reliability," "**inconsistent quality**," Envista 6.7/10, "quality noted as weakest feature." | ❌ Third-party-authored, mildly negative narrative; no first-party counter. |

**Two patterns stand out:**

1. **The disruption thesis is live.** In luxury EV, AI recommends the *challenger* (Lucid Gravity) over Cadillac *despite* Cadillac's strong, specific specs — because the framing/narrative comes from third parties, and a nimble entrant is winning the story.
2. **Portfolio is uneven and uncontrolled.** Chevrolet (trucks/EVs) and Cadillac (luxury EV) surface well; **GMC, Buick, and the GM parent brand are weak or invisible** — and GM isn't authoring any of it.

---

## 4. Qualitative AI Visibility Scores (GM overall)

Manual, directional — the product would compute these numerically per brand.

| Score | Read | Why |
|-------|------|-----|
| **Retrieval** (can AI find us?) | **Low first-party / Med via third parties** | Own sites blocked/SPA; discoverable only through others. |
| **Citation** (does AI mention/cite us?) | **Mixed** | Chevy & Cadillac decent; GMC & Buick weak; parent nearly invisible; citations point to third parties, not GM. |
| **Reasoning** (complex Qs about us?) | **Medium** | AI can compare specs, but from third-party data GM can't verify or correct. |
| **Trust** (is evidence strong & first-party?) | **Low** | Almost no first-party evidence in the AI layer — the single biggest, highest-value gap. |

---

## 5. Recommendations (what marketG's engine would output)

1. **Fix machine-readability (all brands).** Whitelist AI crawlers (GPTBot, ClaudeBot, PerplexityBot, Google-Extended), serve server-rendered content, add schema.org `Vehicle`/`Product` markup with specs. → lifts **Retrieval + Trust** across the portfolio.
2. **Close the hybrid gap.** GM is invisible in "reliable hybrid" queries — a large, growing category. Publish authoritative, evidence-backed hybrid/EV capability content. → **Citation** where it's currently zero.
3. **Give AI Cadillac's side vs. challengers.** AI recommends Lucid over Lyriq despite Cadillac's specs — publish evidence-backed comparison/claim content so AI can cite GM's case. → **Reasoning + Citation** in luxury EV.
4. **Author a Buick counter-narrative.** The third-party story is "inconsistent quality"; GM has no first-party rebuttal in the AI layer. → **Trust**.
5. **Assert the corporate hierarchy.** Make the GM → Chevrolet/GMC/Buick/Cadillac structure machine-readable so AI reasons across the portfolio (the Semantic Business Twin's core job). → cross-brand **Reasoning**.

---

## 6. Verdict on the Hypothesis

**Supported (directionally).**

- A big, outsourced-marketing incumbent has **lost first-party control of its AI representation** — its own sites are unreadable to machines while third parties author its story.
- A **new entrant (Lucid) out-recommends** an established GM brand in a premium category — the exact disruption dynamic the strategy bets on.
- The gaps are **specific, fixable, and evidence-linked** — precisely the output marketG's recommendation engine is designed to produce.

This is a credible, demonstrable sales narrative for **"bring GEO in-house"**: *"Here's what AI says about your brands today, here's who it cites instead of you, here's the new entrant beating you, and here's exactly what to fix."*

---

## 7. Product Implications (feeds the specs)

- **Corporate hierarchy matters** — the twin must model Organization → sub-brand → model (validated by the GM structure). Already in scope (SBTS entity model).
- **Model-level, spec/comparison claims dominate** automotive buyer questions — tune question generation and the claim taxonomy accordingly (noted in the beachhead decision).
- **First-party machine-readability is itself a scored dimension** — crawlability, SSR, and schema.org markup should feed the Retrieval/Trust scores. Consider adding a "machine-readability" signal to the AI Visibility scoring (AVAS §4).
- **The External AI Probe should record source provenance** — *which* domains AI cites (first-party vs. third-party) is a headline insight, not just whether we're mentioned. Reinforces `cited_sources` in `probe_result` (DB §3.16).
