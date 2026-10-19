---
name: research-dispatch-transport-boundary
description: Use when designing, migrating, or reviewing research-job dispatch using PostgreSQL HTTPS pull, RabbitMQ/Celery, or managed queues while preserving FastAPI leases, fencing, quotas, and worker portability.
---

# Research dispatch is a replaceable delivery mechanism

Use for Vesconte research-job **delivery, acquisition, remote workers, and transport migration**. For quota reservation, settlement, and billing, use `research-job-quota-ledger`; for Prefect **data pipelines**, use `prefect-self-hosted-operations`. This Skill records a **reviewed architectural recommendation requested on 2026-10-11**, not proof of production rollout, organizational Acceptance, successful model execution, or measured scale.

## Architecture decision: keep stable the things that matter

**Recommended initial dispatch:** PostgreSQL 16 job-state queries through a FastAPI HTTPS `AcquireWork` / `claim-next` endpoint. Workers pull when they have capacity; the API atomically selects eligible work and issues a lease. `LISTEN/NOTIFY` may improve wake-up latency but is never a durable queue. Run commercial reconciliation and maintenance from durable PostgreSQL work records using independent backend workers.

**Permanent contract:** PostgreSQL owns job lifecycle, quota reservations, attempts, lease generation/fencing, and results; FastAPI authenticates workers and arbitrates every claim, heartbeat, event, result, cancellation and terminal transition; model executors know none of PostgreSQL, Celery, AMQP, SQS or Cloudflare Queues. The transport only discovers/delivers **job references or already-authorized work grants**. Do not promise a universal plug-compatible adapter: pull and broker modes differ in claim, redelivery and acknowledgment semantics.

## Boundaries not to blur

- Submission commits the job and quota reservation atomically **before returning accepted**. No successful broker publish is required for PostgreSQL pull: the committed eligible job itself is discoverable. Use transactional outbox for distinct durable business events or if a later broker needs reliable publication.
- A worker receives an authorized lease **once** for an attempt: HTTP pull may return a lease grant; a future broker may deliver a job ID that is then claimed through the same FastAPI authority. Do **not** have a supervisor claim a second time after receiving a lease from `claim-next`.
- Lease generation and opaque lease token fence *all* persistent mutations, including event/variant writes and terminal settlement. A stale worker can still have spent compute; exactly-once external model execution is not guaranteed.
- HTTP pull does not require workers to hold database credentials or accept inbound connections. Service identities must be scoped by environment and worker/pool and authorized for eligible workload classes.
- Never tie commercial authorization or results to delivery receipt ACK. An ACK is a transport action; a valid persisted terminal state is a product action.

## How to apply

Read [references/postgres-https-pull.md](references/postgres-https-pull.md) before implementing claim, long-poll or recovery. Read [references/migration-and-choice.md](references/migration-and-choice.md) when removing RabbitMQ/Celery or considering Prefect, Hatchet, SQS or Cloudflare Queues. Read [references/evidence.md](references/evidence.md) for the exact repository facts, versioned provider evidence, unverified assumptions and refresh triggers.

**Stop** before modifying queues, services, database schema, credentials, production dispatch or live jobs without the relevant environment owner's authorization and any repository governance admission. A clean Git diff or synthetic fixture is not end-to-end validation. Verify two real-model execution and failure recovery before claiming the architecture is operational.
