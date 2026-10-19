---
name: research-job-quota-ledger
description: Use when designing or debugging transactional quota reservation and settlement for paid research comparison jobs, including duplicate admission, partial results and cancellation races; not for generic worker concurrency or subscription billing alone.
---

# A queued job is a reserved obligation

Confirm the product's settlement contract before implementation: what constitutes a valid
result, how many units are reserved/consumed, whether partial work is billable, and how
cancellation and entitlement changes affect accepted work. A two-model comparison consuming
one unit only when both outputs are durable is a useful **conditional example**, not an
agreed target for every product. Historical Finance fixtures are optional in
[references/finance-settlement-example.md](references/finance-settlement-example.md).

Identify the actual identity provider, authorization boundary, persistence layer and its
transaction/isolation guarantees. Clerk, FastAPI and PostgreSQL are implementation examples;
do not introduce them into an existing system merely to use this method.

## Atomic admission

1. Authenticate the principal; resolve authoritative account/tenant, current permission and
   required feature grant. Possession of a job ID, membership alone or a frontend plan claim
   does not authorize submission or access. Derive cancellation authority from the target's
   explicit action/resource policy, not a role name.
2. In one transaction supported by the actual store, check the applicable billing period,
   remaining units, storage headroom and concurrency policy. Apply an account-scoped
   idempotency key, reserve the policy-defined quantity, and persist the eligible job
   atomically. Enforce uniqueness/locking or equivalent database guarantees; an application
   precheck followed by independent writes is not atomic admission. If cross-store writes
   prevent this, design explicit consistency/recovery semantics before claiming equivalence.
3. Dispatch only references or authorized grants, never user session tokens. The execution
   authority must issue leases, fence every mutation by generation/token and reject stale
   completion. Transport receipt is not authority or successful settlement. For PostgreSQL
   pull, a committed eligible job is discoverable; a broker/outgoing business event may
   require a transactional outbox. Neither is assumed present.
4. Persist validated results before the terminal success/settlement decision. Make that
   decision transactional and idempotent; reconcile abandoned reservations and completed
   but unsettled jobs. Keep execution attempts distinct from a single billable job.

## Settlement state machine

Write the state table for the confirmed product contract. For the **selected two-model,
one-unit example** only:

- Both required outputs valid and durably stored: consume one reserved unit once.
- Definitive failure or cancellation before the complete durable result: release the whole
  reservation, even if internal compute cost was incurred; clean partial outputs under the
  authorized retention policy.
- Complete durable result but failed browser delivery: settlement remains successful.

In any contract, repeated cancellation/settlement must not double consume or release.
Resolve races between cancellation and completion against durable state; a request to cancel
is not a terminal outcome. A completed job cannot simply be retroactively cancelled to
refund usage. Record refunds/adjustments as explicit ledger operations if supported.
Track compute cost separately from included units. Stripe usage reporting, if present, is a
separate downstream concern, not an immediate quota or concurrency lock.

## Capacity and degraded billing

Use the product's own concurrency, timeout, retry and abuse policy. Repeated API calls to
cancel the same job are not distinct cancelled jobs. Do not prevent legitimate cancellation
merely to throttle new admissions. Set degraded-mode thresholds from authorized risk policy,
not silence from webhooks; state how stale grants and already reserved work are handled.

## Exercises

Use local fixtures or an authorized isolated environment with the chosen policy:

- Concurrent submissions with one unit left: at most one successful unit reservation.
- Same idempotency key, worker redelivery, crash after partial output, crash after all output
  persistence, duplicate terminal events, cancellation/completion race and stale worker.
- Billing-period boundary: settlement/abandonment applies to the correct reserved period.
- Near-full storage plus concurrent reservations; output exceeds reservation; partial object
  cleanup failure. Expected charging follows the selected product contract.
- Lost dispatch wakeup, restart, unpublished outbox where configured and entitlement revoked
  after admission. Acknowledgment must not erase the durable obligation or bypass its policy.

Companion skills `research-dispatch-transport-boundary` and
`organization-resource-authorization` are optional additional context if installed; the
minimum authorization, lease and accounting invariants above stand on their own.
Stop before paid external model calls, real queues or live job cancellation without explicit
authorization. Fixtures do not prove actual database isolation or model-cost behavior.

## Sources to re-check for the selected implementation

- https://www.postgresql.org/docs/16/sql-select.html
- https://www.postgresql.org/docs/current/explicit-locking.html
- https://docs.stripe.com/billing/subscriptions/usage-based/recording-usage-api

PostgreSQL locking documentation rechecked 2026-10-19; verify actual store/transport versions.
