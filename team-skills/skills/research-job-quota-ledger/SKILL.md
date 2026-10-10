---
name: research-job-quota-ledger
description: Use when designing or debugging long-running paid research jobs, quota reservations, concurrency, cancellations, retries or degraded billing; preserve exactly-once accounting despite duplicate requests and worker restarts.
---

# A queued job is a reserved obligation

**Scope:** research comparisons that run **two AI models** and consume one included subscription unit **only after both results are valid and durably available**. This is the agreed **product target**, not evidence about installed job infrastructure.

## Atomic admission

1. Authenticate the Clerk principal in FastAPI; resolve the authoritative internal `account_id`, current membership/permission and entitled feature.
2. In **one PostgreSQL transaction**, check the applicable billing period and remaining included units, storage headroom, policy-based concurrency and an account-scoped idempotency key. Reserve one comparison unit and an estimated storage ceiling; persist the eligible job atomically. Persist outbox records in that transaction **when distinct business events or a broker publisher actually require them**; research discovery via PostgreSQL pull does not require a duplicate broker message.
3. The dispatch transport is replaceable: PostgreSQL + HTTPS pull may acquire an authorized lease directly; a broker consumer may receive a job reference and then claim it at FastAPI. Neither path transports Clerk session tokens or grants authorization by possession of the reference. Preserve idempotent leases, generation fencing and settlement across duplicate deliveries. For acquisition/transport migration, use the separate `research-dispatch-transport-boundary` Skill.
4. Workers acquire execution capacity on demand and record both model outcomes. Persist validated results before marking successful and settling a unit. Reconcile abandoned reservations and completed-but-unsettled jobs.

## Settlement state machine

- `succeeded` **with both model outputs validated and stored** -> consume **one** unit once.
- Definitive failure or cancellation **before** a complete durable result -> release **all** reserved comparison quota, even if a model cost money internally; clean partial outputs according to retention policy.
- If complete result exists but browser delivery fails, it remains a successful consumed unit.
- Repeated cancel/settle requests are idempotent. A completed job cannot be retroactively cancelled.
- Cancellation in progress is cooperative; do not refund until the terminal outcome is determined. Require the submitter or authorized org admin; apply the account authorization Skill.
- Track actual computation cost separately from the included-unit ledger for margins/abuse. Stripe usage meters, if added later, report settled usage; they must not serve as immediate concurrency/quota locks.

## Protecting capacity without punishing legitimate users

Use per-account and per-user quotas, concurrency, admission queues, worker timeouts, retry budgets and rate limits. A burst of cancellations is not itself a reason to block existing-job cancellation. Count distinct effectively cancelled jobs, not repeated API calls.

**Local-only test fixtures, never production defaults:** 20 comparisons per monthly billing period, 2 simultaneous jobs, 250 MB aggregate per comparison (both models), 5 GB account storage, 10 effective cancellations per rolling hour. On reaching the cancellation threshold, temporarily block **new** submissions while continuing cancellation/read/download. Production numbers require measured cost, size and abuse patterns.

For **local degraded-billing exercises**, the agreed fixture is: verified failure >15 min -> at most 1 concurrent job/account, stop accepting new paid jobs after 60 min since last verified commercial sync; accepted jobs may finish; never waive usage/storage quotas or assume an expired right remains valid.

## Tests that must fail unsafe implementations

- 50 simultaneous submissions with only one unit left -> one successful reservation.
- Same idempotency key retried, worker redelivery, crash after model 1, crash after both results, repeated cancellation, split-brain worker lease, monthly period boundary.
- Account has 4.8 GB stored with 250 MB reservation under 5 GB cap -> new job denied.
- Artifacts exceed a reserved ceiling -> fail and release unit, clean partial objects; prove no storage race between simultaneous jobs.
- Worker stopped/restarted; a committed job is not dispatched after a lost wakeup; broker outbox not published when a broker is configured; per-account degradation; subscription revoked after job acceptance.

Stop before performing paid external model calls, touching a real queue, or cancelling live jobs without explicit authorization.

## Sources to re-check

- https://www.postgresql.org/docs/current/explicit-locking.html
- https://www.postgresql.org/docs/16/sql-select.html
- https://docs.celeryq.dev/en/v5.6.3/userguide/configuration.html
- https://docs.stripe.com/billing/subscriptions/usage-based/recording-usage-api

Operational choices require tests against the actual transport (including broker if configured), database isolation level, worker version and two real models.
