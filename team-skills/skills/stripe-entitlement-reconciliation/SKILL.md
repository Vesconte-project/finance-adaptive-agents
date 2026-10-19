---
name: stripe-entitlement-reconciliation
description: Use when integrating Stripe Checkout, subscription lifecycle webhooks, Stripe Entitlements and an application's local access projection; prevent incorrect paid-access grants, stale subscription state and webhook ordering bugs.
---

# Billing is not an authorization check

**Scope:** paid access for a SaaS already using Stripe Billing and a separately authenticated user/account. Identify the actual authentication provider, account ownership model, authorization layer
and persistence capabilities before implementation. This describes a design method,
**not verified live state** of another repository.

## Split authorities

- The identity provider authenticates the principal; Stripe supplies commercial state. The
  application authorization layer decides which action/resource is allowed **now**. Clerk,
  FastAPI and PostgreSQL are conditional examples when present, not required architecture.
- Model a stable internal `billing_account` for personal or organizational ownership, mapped to a Stripe Customer for each environment. Where Clerk Organizations are used, personal ownership need not imply an organization.
- Use Stripe Entitlements' feature lookup keys as commercial inputs and store a durable local projection. Add separate local policies for quotas, concurrency, grants, suspensions and resource authorization. Neither identity-session metadata nor an untrusted frontend plan claim grants paid
  access by itself; verify the source and freshness of the commercial grant.
- Do not round-trip to Stripe for every ranking/CSV/job read. Record projection age, effective interval, grant source and last verified state.

## Safe purchase and reconciliation

1. Create Checkout Sessions server-side for the **authenticated internal account** and its
   Stripe Customer. Resolve the plan/Price and validate client-supplied purchase options
   against the server's authorized catalog and commercial rules for that account and
   environment, including quantity, billing interval and discounts where applicable.
   A client-supplied Price ID is a selection input, not authority to buy that offer.
   A maintained allowlist is one option; a static list is not required if equivalent
   server-side catalog/rule validation exists. Persist a purchase attempt/idempotency key.
   Do not treat an editable Payment Link URL parameter or arbitrary metadata user ID as
   proof of the buyer.
2. Verify webhook signatures against the **raw request body** and environment-specific endpoint secret. Durable-inbox the event ID with uniqueness, acknowledge promptly, and reconcile asynchronously.
3. Expect duplicates, retries and out-of-order events. Serialize reconciliation for each billing account or enforce monotonically correct state. Fetch current subscription and the complete paginated active-entitlements list from
   Stripe; summary payloads may be truncated. An old event must not overwrite new account
   state. Event creation timestamps alone are not a total ordering or a deduplication key.
4. Sync purchase, renewal, trial, grace, schedule change, cancellation, failed payment, refunds/disputes where relevant, and entitlement changes. Do not grant access from the browser's successful redirect.
5. Reconcile periodically or on suspected drift; alert on stale accounts and failed webhook delivery. Treat entitlement rollout timing for existing subscribers explicitly.
6. Keep Stripe Live and test/sandbox customers, keys, destinations and data separate.

## Degraded commercial availability

Do **not** infer a Stripe outage merely from absence of webhooks. Track reconciliation health and per-account last-confirmed validity. Separate read-only paid content from initiating high-cost operations. Stale-state TTL is an **operational risk policy**, not a hard guarantee of revocation while Stripe is unavailable.

Obtain the target application's authorized risk policy before choosing stale-state
thresholds, high-cost admission limits or treatment of already accepted work. For an
**illustrative simulation only**, explicitly select: confirmed failure for 15 minutes
triggers a one-concurrent-job limit per account, and 60 minutes since last successful
sync blocks new paid jobs while accepted work can finish. These are not defaults or
evidence of a prior agreement. Exercise them with synthetic time/state; do not apply
them to production implicitly. A simulation must still require previously verified,
unexpired rights and enforce usage/storage limits. Never silently promote unpaid
accounts when billing state is unknown.

## Verification checklist

- Unauthorized or wrong-environment Price, altered quantity/discount; two concurrent purchases for one account; mismatched Customer; modified `client_reference_id`; webhook replay; cancellation before renewal event; late entitlement event; forced reconciliation failure; concurrent downgrade/job create.
- Compare local projection with Stripe by account and `environment`; record why access was granted/denied.
- Stop before changing active prices, subscriptions or production webhooks without an explicit authorized change.

## Sources to re-check

- https://docs.stripe.com/billing/entitlements?dashboard-or-api=api
- https://docs.stripe.com/webhooks
- https://docs.stripe.com/billing/subscriptions/webhooks
- https://docs.stripe.com/api/checkout/sessions/create
- https://docs.stripe.com/payment-links/url-parameters

Webhook and Entitlements documentation rechecked 2026-10-19; verify the target
API version and integration before relying on provider behavior.

Checkout parameter documentation rechecked 2026-10-20; authorized offer selection is an
application policy, not a guarantee provided by accepting a valid Stripe Price ID.
