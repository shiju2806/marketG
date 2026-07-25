# marketG — AI Referral Attribution

**Feature Specification**

- **Version:** 1.0
- **Status:** Proposed
- **Audience:** Product, Backend, Frontend, Data, Partnerships, Legal/Privacy
- **Depends on:** account / organization tenancy; organization onboarding; event and webhook infrastructure

---

## 1. Purpose

AI Referral Attribution lets marketG measure and monetize a merchant's outcomes from a **marketG-controlled recommendation link**. It turns an eligible recommendation into an affiliate-style, auditable commission record:

```
AI recommendation surface
  → marketG tracked link → click record → merchant site / checkout
  → server-side conversion event → attribution decision → commission ledger
```

It is a separate application from AI Visibility:

| Application | Question answered | Evidence |
|---|---|---|
| AI Visibility | “Do AI assistants mention or cite this organization?” | marketG probes and visibility analysis |
| AI Referral Attribution | “Did a marketG-directed recommendation create a verified commercial outcome?” | a controlled click ID and merchant conversion event |

The feature must never present an organic ChatGPT, Claude, or other assistant citation as a paid or commissionable referral unless it passed through a marketG tracked link and satisfied the configured attribution rule.

## 2. Problem and Product Thesis

Merchants can see some traffic labelled `chatgpt.com` or `claude.ai` in analytics, but that signal is incomplete, may be absent, and cannot establish a reliable connection to a specific recommendation or later purchase. marketG needs a dependable value-capture loop that is fair to merchants and defensible in finance reconciliation.

marketG provides the technical evidence of referral and conversion. The merchant agreement defines the offer, rate, eligible products, attribution window, exclusion rules, refund treatment, and payment terms.

### 2.1 Non-negotiable attribution rule

**Commissionable attribution requires a marketG-issued `click_id` at the time of referral and a merchant-confirmed conversion containing that ID.**

`Referer`, UTM parameters supplied by a third party, IP address, device fingerprint, or an AI-probe result may enrich reporting, but cannot independently create a commission.

### 2.2 Eligible distribution surfaces

The initial release supports links displayed by a surface where marketG or its distribution partner can deliberately place the link, for example:

- A marketG-powered recommendation or comparison experience.
- An approved partner assistant, app, or publisher placement that returns a marketG link.
- A merchant-approved campaign link shared in an AI-assisted workflow.

Native organic ChatGPT/Claude citations are **not** an initial commission channel. They may be reported as unattributed AI referrals when a merchant's analytics supplies the signal, but marketG cannot make a payout claim from them. This avoids claiming control over assistant results that marketG does not control.

## 3. Personas and Jobs to Be Done

| Persona | Job |
|---|---|
| Merchant owner / partnerships lead | Create an offer and see verified revenue, leads, and amount owed to marketG. |
| marketG operator | Create approved links, monitor conversion quality, reconcile commissions, and manage payouts. |
| Merchant engineer | Install the smallest safe integration and send trustworthy conversion events. |
| Finance reviewer | Audit how every commission was calculated and approve or reverse it. |

## 4. MVP Scope

### Included

- Merchant / offer / campaign / tracked-link management for account admins.
- HTTPS redirect service issuing opaque, signed links under a marketG-controlled domain.
- Durable click capture before a 302 redirect to the merchant destination.
- One merchant web integration: JavaScript landing-page tag plus Stripe Checkout conversion webhook.
- Exact-click attribution with a configurable 30-day last-eligible-click window.
- Conversion de-duplication, refund/reversal support, commission ledger, and CSV export.
- Dashboard for clicks, conversions, attributed revenue, pending/approved/reversed commission, and per-record audit trail.
- Manual monthly reconciliation and invoicing; payout automation is deferred.

### Excluded

- Paying for, influencing, or representing organic results in ChatGPT, Claude, or other AI products.
- Attribution based only on HTTP `Referer`, device fingerprinting, or inferred cross-site identity.
- Multi-touch fractional attribution, coupon-code-only attribution, and cross-device identity graphs.
- Automatic payouts, tax forms, currency conversion, and marketplace funds custody.
- Native checkout inside a third-party assistant.
- Shopify, HubSpot, Salesforce, and other integrations beyond the initial Stripe path.

## 5. User Workflow

### 5.1 Merchant setup

1. A marketG operator creates a merchant profile for an onboarded organization.
2. The operator defines an offer: eligible products, commission basis (`gross_revenue`, `net_revenue`, or `qualified_lead`), rate, attribution window, hold period, and exclusions.
3. The merchant adds the marketG tag to its approved landing pages and connects Stripe using a webhook endpoint and signing secret.
4. marketG verifies the domain and runs a test click plus test conversion before the offer can be activated.

### 5.2 Campaign and link creation

1. The operator creates a campaign with a declared distribution surface, e.g. `marketg_assistant` or `partner_assistant`.
2. The operator selects the merchant offer and approved landing-page URL.
3. marketG returns a link such as `https://go.marketg.ai/c/7Xq…`.
4. That exact link is placed on the approved surface. The campaign records the intended source; it does not infer it from the browser referrer.

### 5.3 Click and conversion

1. A visitor opens the tracked link.
2. The redirect endpoint validates the signed token, creates a UUID `click_id`, records the click, and 302-redirects to the merchant URL with `mg_click_id` and UTM values.
3. The merchant tag reads `mg_click_id`, stores it in a first-party cookie with the configured expiry, and removes the parameter from the visible URL with `history.replaceState`.
4. At checkout creation, the merchant includes `mg_click_id` as Stripe Checkout `client_reference_id` and metadata.
5. On a verified Stripe payment webhook, marketG creates an idempotent conversion event.
6. The attribution engine finds the eligible click, freezes the decision and rule version, and writes a pending commission ledger entry.
7. After the hold period, an authorized reviewer approves the entry. Refunds or cancellations reverse it; approved entries are included in the monthly invoice or payout batch.

## 6. Attribution and Commission Rules

### 6.1 MVP algorithm

For a conversion event, marketG:

1. Requires a valid `mg_click_id` issued for the same merchant.
2. Confirms the click occurred on or before the conversion and within the offer's attribution window.
3. Rejects self-referrals, test events, duplicate provider transaction IDs, invalid/cancelled payments, and excluded products.
4. Uses that exact click. If more than one eligible first-party click is available, selects the most recent eligible click.
5. Snapshots the selected click, offer version, rate, commission basis, revenue amount, rule version, and calculation in the attribution record. These values never change retroactively.

### 6.2 Commission calculation

For revenue offers:

```
commission_amount = eligible_revenue × rate
```

`eligible_revenue` is the provider-confirmed amount after the offer's configured exclusions (tax, shipping, discounts, refunds, and/or fees). All money is stored in integer minor units plus ISO currency. A qualified-lead offer uses a fixed amount instead.

### 6.3 State machine

```
conversion received → attributed / not_attributed
attributed → pending → approved → invoiced_or_paid
pending or approved → reversed
```

No record is deleted. Reversal creates a compensating ledger entry linked to the original commission.

## 7. Architecture

```
Recommendation surface
       │
       ▼
go.marketg.ai redirect service ──► click_event (Postgres)
       │  302 + mg_click_id
       ▼
Merchant page ──► first-party marketG tag ──► Stripe Checkout metadata
                                                     │
                                                     ▼
Stripe signed webhook ──► conversion_event ──► attribution engine
                                                     │
                                                     ▼
                                              commission_ledger
                                                     │
                                                     ▼
                                            Reporting / reconciliation
```

### 7.1 Service boundaries

- **Referral API:** merchants, offers, campaigns, links, reports, reconciliation actions.
- **Redirect service:** token validation, click event creation, fast redirect only. It must not block on analytics aggregation.
- **Merchant tag:** minimal browser code that persists the opaque click ID; it does not send chat content, full URLs, or advertising identifiers to marketG.
- **Conversion ingestion:** verifies provider signatures, normalizes provider payloads, writes idempotent raw events, then enqueues attribution.
- **Attribution engine:** applies versioned deterministic rules and produces append-only ledger records.

The feature is a transactional application in Postgres/Supabase. It does not access the Semantic Business Twin, vector store, or graph directly. AI Visibility can supply optional context (e.g. which category has referral demand), but it is not evidence for attribution.

## 8. Data Model

All tables carry `account_id`; merchant-facing rows also carry `organization_id` where applicable. RLS follows the existing account boundary.

| Entity | Key fields | Notes |
|---|---|---|
| `merchant_profile` | `merchant_id`, `organization_id`, `status`, `verified_domains` | Commercial eligibility and integration state. |
| `commission_offer` | `offer_id`, `merchant_id`, `basis`, `rate_bps`, `fixed_amount_minor`, `currency`, `window_days`, `hold_days`, `version`, `status` | Immutable version after activation. |
| `referral_campaign` | `campaign_id`, `offer_id`, `surface`, `declared_source`, `status` | Source is declared by placement, not guessed. |
| `tracked_link` | `link_id`, `campaign_id`, `destination_url`, `token_hash`, `status` | Token is opaque and signed; destination must be allowlisted. |
| `click_event` | `click_id`, `link_id`, `occurred_at`, `landing_url`, `referrer_host`, `user_agent_hash`, `ip_hash` | Raw IP/user agent are not retained; hashes are only short-lived fraud signals. |
| `conversion_event` | `conversion_id`, `merchant_id`, `provider`, `provider_event_id`, `provider_transaction_id`, `click_id`, `amount_minor`, `currency`, `status`, `occurred_at`, `raw_payload_ref` | `provider_event_id` is unique per merchant/provider. Raw payload is access-controlled and retained on a defined schedule. |
| `attribution` | `attribution_id`, `conversion_id`, `click_id`, `decision`, `reason_code`, `rule_version`, `rule_snapshot` | Exactly one final decision per conversion version. |
| `commission_ledger_entry` | `ledger_entry_id`, `attribution_id`, `entry_type`, `amount_minor`, `currency`, `status`, `available_at`, `reverses_entry_id` | Append-only financial record. |
| `reconciliation_batch` | `batch_id`, `merchant_id`, `period_start`, `period_end`, `status`, `total_minor` | Monthly review/invoice batch. |

Critical constraints:

- `tracked_link.token_hash` is unique.
- `conversion_event (merchant_id, provider, provider_event_id)` is unique.
- Money is never a float.
- A `commission_offer` cannot be edited once active; creating a change creates the next version.
- `click_event`, `conversion_event`, `attribution`, and ledger rows are append-only; corrections use new linked rows.

## 9. API Surface

All endpoints are under `/api/v1`, account-scoped, and require the established bearer authentication except redirect and provider webhook routes.

| Method | Path | Purpose |
|---|---|---|
| POST | `/merchants` | Create merchant profile and verify domains. |
| POST | `/offers` | Create a draft commission offer. |
| POST | `/offers/{id}/activate` | Activate a validated offer version. |
| POST | `/referral-campaigns` | Create campaign. |
| POST | `/tracked-links` | Create an approved destination link. |
| GET | `/tracked-links/{id}` | Read link, click, and conversion summary. |
| GET | `/referral-report` | Aggregate clicks, conversions, revenue, and commission. |
| GET | `/commission-ledger` | Paginated audit ledger. |
| POST | `/reconciliation-batches` | Create a monthly review batch. |
| POST | `/reconciliation-batches/{id}/approve` | Approve eligible entries. |
| POST | `/webhooks/stripe` | Receive and verify Stripe events. |
| GET | `/c/{token}` | Public click capture and 302 redirect. |

### 9.1 Create a tracked link

Request:

```json
{
  "campaign_id": "a6c4e09a-95f5-41b8-b6ad-5049f5cc05a4",
  "destination_url": "https://merchant.example/pricing",
  "utm_campaign": "payroll-recommendations-q3"
}
```

Response `201`:

```json
{
  "link_id": "9c39d37f-af56-457e-a967-d9dd05e07a9a",
  "url": "https://go.marketg.ai/c/7Xqv6pKF…",
  "status": "active"
}
```

### 9.2 Conversion ingestion contract

The browser tag is a convenience mechanism, not the source of truth. Conversions arrive server-to-server. Providers must include the opaque click ID in a signed event or a merchant-side server event.

Normalized example:

```json
{
  "provider": "stripe",
  "provider_event_id": "evt_…",
  "provider_transaction_id": "pi_…",
  "merchant_id": "…",
  "mg_click_id": "…",
  "event_type": "payment_succeeded",
  "amount_minor": 120000,
  "currency": "usd",
  "occurred_at": "2026-07-25T18:06:00Z"
}
```

## 10. UX Requirements

### Merchant dashboard

- Summary cards: tracked clicks, verified conversions, conversion rate, attributed revenue, pending commission, approved commission.
- Filter by date, offer, campaign, declared surface, and conversion status.
- Conversion table showing timestamp, campaign, click ID, transaction ID (partially masked), revenue, attribution decision, commission, and state.
- Drill-down audit trail showing the click, provider event, rule snapshot, and any reversal.
- A visible “Attribution quality” label: `verified click ID`, `merchant-confirmed but unattributed`, or `observed referrer only`.

### Operator workflow

- Draft → test → activate checklist for each offer/integration.
- Link generation only permits merchant domain allowlist destinations.
- Review queue for disputed, refunded, late, or suspicious conversions.
- Export one reconciliation CSV per merchant and billing period.

## 11. Security, Privacy, and Compliance

- Use HTTPS, short opaque signed tokens, and destination-domain allowlists. Never accept arbitrary redirect targets.
- Redirect tokens must be revocable; disabled offers/links must not issue commissionable new clicks.
- Verify Stripe webhook signatures; apply idempotency at webhook receipt and conversion normalization.
- Do not collect prompts, assistant conversation content, payment-card data, raw IP addresses, or cross-site fingerprints.
- The merchant owns consent for its first-party cookie/tag. The tag must be configurable to respect consent before writing non-essential storage.
- Hash identifiers with a rotating keyed salt, restrict access, and set retention periods. Fraud fields must not be used to build behavioral profiles.
- Show clear sponsored/compensated-recommendation disclosure on any marketG-controlled recommendation surface where an offer may affect compensation.
- Agreements and UI must disclose the attribution model, lookback window, exclusions, refund/reversal treatment, dispute process, and payment timing.

Legal review is required before launch for the target markets, including privacy/cookie requirements, endorsement/affiliate disclosures, tax treatment, and payments regulation. MarketG should invoice merchants initially rather than hold or disburse funds.

## 12. Reliability and Fraud Controls

- Redirect availability target: 99.9%; p95 redirect processing under 100 ms excluding destination latency.
- Click writes use an outbox/queue fallback so analytics degradation does not prevent a safe redirect.
- Retry provider event processing; preserve an immutable raw payload reference and processing attempt history.
- Flag, but do not automatically reject without review: repeated clicks from one hash, abnormal click-to-conversion timing, unexpected country mismatch, self-referral, and high refund rate.
- Reconciliation compares provider gross/net amounts and refund events to the commission ledger daily; raise an exception for any difference.

## 13. Success Metrics

| Metric | MVP target |
|---|---|
| Click capture completeness | ≥99% of successful redirect responses create a click event. |
| Conversion match rate | ≥95% of eligible integrated checkout conversions include a click ID. |
| Duplicate conversion rate | 0 accepted duplicate provider events. |
| Ledger reconciliation | 100% of approved commission entries reconcile to a merchant-confirmed event. |
| Merchant activation | First test click and test conversion completed in under 30 minutes. |
| Dispute rate | <2% of approved commission value, reviewed monthly. |

## 14. Delivery Plan

### Phase 1 — Verified referral MVP

1. Schema, RLS, audit/event conventions, offers, campaigns, signed redirect links.
2. Merchant tag, Stripe Checkout metadata helper, Stripe webhook ingestion, exact-click attribution.
3. Operator + merchant reporting, manual reconciliation export, reversal workflow.
4. End-to-end tests: link, cookie, checkout, signed webhook, duplicate delivery, refund, expiration, disabled offer.

### Phase 2 — Merchant integrations and operations

- Shopify and CRM lead-event adapters.
- Offer/product eligibility rules, coupon support, dispute portal, finance approval workflow.
- Automated anomaly detection and scheduled reconciliation.

### Phase 3 — Payments and advanced attribution

- Optional payout provider after legal, tax, and custody design.
- Configurable multi-touch models only where all touchpoints are consented, deterministic, and merchant-approved.

## 15. Acceptance Criteria

- A user can create an active offer, campaign, and tracked link only for a verified merchant destination.
- Opening an active link generates one durable `click_id`, preserves destination query parameters, appends marketG attribution parameters, and redirects to the approved host.
- A signed Stripe payment webhook containing that click ID produces one conversion and one pending ledger entry calculated from the activated offer version.
- Re-delivering the same Stripe event produces no duplicate conversion or commission.
- A refund produces a linked reversal and removes the amount from the next approved reconciliation batch.
- A direct merchant conversion, an unknown click ID, a click outside the window, or a referrer-only visit is reported as unattributed and creates no commission.
- A reviewer can trace every commission to its click, provider transaction, rule snapshot, and offer version.
- Organization/account isolation is enforced by RLS for every merchant, link, click, conversion, and ledger query.

