---
name: stripe-entitlement-reconciliation
description: Use when integrating Stripe Checkout, subscription lifecycle webhooks, Stripe Entitlements and an application's local access projection; prevent incorrect Pro grants, stale subscription state and webhook ordering bugs.
---

# Billing is not an authorization check

**Scope:** paid access for a SaaS already using Stripe Billing and a separately authenticated user/account. This captures a proposed target architecture, **not verified live state** of another repository.

## Split authorities

- Clerk answers who authenticated. Stripe answers which Customer purchased which subscriptions and commercial features. The application's FastAPI/PostgreSQL authorization layer answers which action/resource is allowed **now**.
- Model a stable internal `billing_account` for personal or organizational ownership, mapped to a Stripe Customer for each environment. Never require every personal customer to be a Clerk Organization.
- Use Stripe Entitlements' feature lookup keys as commercial inputs and store a durable local projection. Add separate local policies for quotas, concurrency, grants, suspensions and resource authorization. Neither Clerk session metadata nor an untrusted frontend plan claim grants Pro by itself.
- Do not round-trip to Stripe for every ranking/CSV/job read. Record projection age, effective interval, grant source and last verified state.

## Safe purchase and reconciliation

1. Create Checkout Sessions server-side for the **authenticated internal account** and its Stripe Customer; persist a purchase attempt/idempotency key. Do not treat an editable Payment Link URL parameter or arbitrary metadata user ID as proof of the buyer.
2. Verify webhook signatures against the **raw request body** and environment-specific endpoint secret. Durable-inbox the event ID with uniqueness, acknowledge promptly, and reconcile asynchronously.
3. Expect duplicates, retries and out-of-order events. Serialize reconciliation for each billing account or enforce monotonically correct state. Fetch current subscription and active entitlements from Stripe; an old event must not overwrite new account state.
4. Sync purchase, renewal, trial, grace, schedule change, cancellation, failed payment, refunds/disputes where relevant, and entitlement changes. Do not grant access from the browser's successful redirect.
5. Reconcile periodically or on suspected drift; alert on stale accounts and failed webhook delivery. Treat entitlement rollout timing for existing subscribers explicitly.
6. Keep Stripe Live and test/sandbox customers, keys, destinations and data separate.

## Degraded commercial availability

Do **not** infer a Stripe outage merely from absence of webhooks. Track reconciliation health and per-account last-confirmed validity. Separate read-only paid content from initiating high-cost operations. Stale-state TTL is an **operational risk policy**, not a hard guarantee of revocation while Stripe is unavailable.

For a local-only exercise agreed in the design discussion: enter degraded mode after **15 minutes** of confirmed failure; admit at most **1 concurrent job per account** until **60 minutes** since last successful sync; then block **new** paid jobs, not already accepted ones. Only for previously verified, unexpired rights and within local usage/storage quotas. Production TTLs remain to be set from risk/SLOs. If the authoritative billing state cannot be trusted, never silently promote Free to Pro.

## Verification checklist

- Two concurrent purchases for one account; mismatched Customer; modified `client_reference_id`; webhook replay; cancellation before renewal event; late entitlement event; forced reconciliation failure; concurrent downgrade/job create.
- Compare local projection with Stripe by account and `environment`; record why access was granted/denied.
- Stop before changing active prices, subscriptions or production webhooks without an explicit authorized change.

## Sources to re-check

- https://docs.stripe.com/billing/entitlements
- https://docs.stripe.com/webhooks
- https://docs.stripe.com/billing/subscriptions/webhooks
- https://docs.stripe.com/api/checkout/sessions/create
- https://docs.stripe.com/payment-links/url-parameters

Provider references last reviewed 2026-10-10.
