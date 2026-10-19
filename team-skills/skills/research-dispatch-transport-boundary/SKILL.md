---
name: research-dispatch-transport-boundary
description: Use when designing or migrating research-job dispatch in a system with an existing or explicitly chosen PostgreSQL/FastAPI lease authority; compare HTTPS pull and broker delivery while preserving fencing and worker portability.
---

# Research dispatch is a replaceable delivery mechanism

Use for research-job delivery, acquisition, remote workers and transport migration.
First verify that the target system already has, or the user explicitly selected,
PostgreSQL durable job state and an authenticated FastAPI lease authority. Locate its
actual schema, isolation level, claim/recovery paths and worker protocol. Do not impose
this stack or a migration merely because the task mentions a queue. If the prerequisite
is absent, report the mismatch and evaluate the actual architecture separately.

Quota settlement and account authorization are outside the transport decision; preserve
the existing policy. The minimum invariant is atomic accepted work/reservation state,
resource-scoped authorization and one idempotent settlement per job; delivery or ACK alone
cannot authorize work or charge it. `research-job-quota-ledger` and
`prefect-self-hosted-operations` are optional extra context if present, not prerequisites.
This package does not configure data-pipeline orchestration or define a commercial plan.

## Candidate architecture: preserve the authority

For that verified stack, evaluate PostgreSQL eligible-job queries behind an authenticated
HTTPS `AcquireWork` / `claim-next` endpoint. Workers pull with available capacity; the API
atomically issues a lease. Compare it against retaining a broker using measured delivery
requirements and operating cost. PostgreSQL 16 is the reference version, not an upgrade
instruction. `LISTEN/NOTIFY` may reduce wake-up latency, never replace durable work records.

In this design PostgreSQL owns lifecycle, reservations, attempts, fencing and results;
FastAPI arbitrates claims, heartbeat, events, cancellation and terminal transitions. Adapt
to the verified existing authority rather than inventing a second state machine. Keep
model executors separate from transport SDKs. A transport delivers job references or
already authorized grants; pull and broker modes have different claim/redelivery/ACK
semantics and are not universal plug-compatible adapters.

## Boundaries not to blur

- Submission commits the job and quota reservation atomically **before returning accepted**. No successful broker publish is required for PostgreSQL pull: the committed eligible job itself is discoverable. Use transactional outbox for distinct durable business events or if a later broker needs reliable publication.
- A worker receives an authorized lease **once** for an attempt: HTTP pull may return a lease grant; a future broker may deliver a job ID that is then claimed through the same FastAPI authority. Do **not** have a supervisor claim a second time after receiving a lease from `claim-next`.
- Lease generation and opaque lease token fence *all* persistent mutations, including event/variant writes and terminal settlement. A stale worker can still have spent compute; exactly-once external model execution is not guaranteed.
- HTTP pull does not require workers to hold database credentials or accept inbound connections. Service identities must be scoped by environment and worker/pool and authorized for eligible workload classes.
- Never tie commercial authorization or results to delivery receipt ACK. An ACK is a transport action; a valid persisted terminal state is a product action.

## How to apply

Read [references/postgres-https-pull.md](references/postgres-https-pull.md) before implementing claim, long-poll or recovery. Read [references/migration-and-choice.md](references/migration-and-choice.md) when removing RabbitMQ/Celery or considering Prefect, Hatchet, SQS or Cloudflare Queues. The optional [historical Finance evidence](references/evidence.md) records the source
decision and its limits; read it only for that context. Repository names, host estimates,
commercial tasks and two-model execution there are not generic requirements.

**Stop** before modifying queues, services, database schema, credentials, production dispatch or live jobs without the relevant environment owner's authorization and any repository governance admission. A clean Git diff or synthetic fixture is not end-to-end validation. Verify the actual executor stages and failure recovery before claiming operation; paid
model calls or production tests require their own authorization.
