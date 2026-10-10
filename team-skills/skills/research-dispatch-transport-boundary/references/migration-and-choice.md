# From reference broker to durable pull, without changing execution semantics

This is a **proposed change plan**. Before changing any repo, read its active AGENTS/governance requirements and verify current HEADs. GitHub source visibility is not authorization to deploy.

## Workstream by owner

**finance-backend**
- Existing path persists job, quota reservation and outbox, with Celery publication of `research.execute`, `research.purge`, `billing.reconcile` and `billing.customer-reconcile`. Verify latest schema and tests: no assumed current state.
- Implement HTTP `AcquireWork` / `claim-next` using the **existing job/lease authority** rather than creating a second independent queue state machine. Separate the request's idle waiting from the SQL transaction and connection.
- Update scheduler recovery: expired leases must become discoverable through the job store without requiring fresh `research.execute` broker messages. Prevent old reference-publishing paths from publishing a duplicate stream.
- Keep durable Stripe/commercial business events; consume the existing outbox through a backend-owned worker with idempotent claims, bounded retries, backoff, dead-letter/operator visibility and recovery. Separate commercial and research capacity. Do not silently discard pending outbox rows.

**finance-research-orchestrator**
- Replace Celery's delivery loop with a bounded HTTPS pull loop. Preserve `NativeSupervisor` process-group cleanup, heartbeats, cancellation and event/result reporting.
- Existing supervisor calls the backend claim endpoint after receiving a **job ID**. Change the boundary so a grant from `AcquireWork` is used directly; else it might double-claim/revoke its own attempt. Keep the execution engine ignorant of the acquisition transport.
- Add correct shutdown and capacity-aware polling, jitter/backoff, worker identity rotation, disconnect handling and idempotent stop/retry. Prove success with **real model pair**; fixtures alone do not prove cost, cancellation or resource behavior.

**finance-infra**
- Keep dev/staging/production isolation via credentials, endpoints, DBs and worker pools. Run local and remote workers over identical protocol code paths, varying only configuration and capacity.
- Verify memory/CPU limits, PostgreSQL pool bounds, resource pressure while backups run, service restarts and monitoring.
- Remove RabbitMQ, outbox publisher and Celery dependencies/containers **only after** the new integration passes recovery tests and there is no outstanding unprocessed reference or commercial event. Prelaunch cutover can be direct; preserve a tested, explicitly fenced rollback.
- Never run two independent acquisition transports simultaneously without a deliberate migration/fencing plan: this can duplicate leases and compute even if terminal settlement is protected.

## Selection and reversibility

- **PostgreSQL/HTTPS pull** is preferred for minutes-long research jobs and the reported initial volume (tens to thousands/day) because FastAPI already owns the execution lease and remote workers require only outbound HTTPS. It is not a benchmarked guarantee for thousands of workers.
- **RabbitMQ/Celery** makes sense with complex broker routing, shared multi-service event distribution or measurable dispatch latency/DB contention. Quorum queues and late ACKs do not replace application fencing or idempotency. Test exact Celery/Kombu/RabbitMQ versions, queue declarations, QoS and redelivery.
- **SQS/Cloudflare Queues** becomes appropriate when managed message distribution, cross-region topology or operational load outweighs the second queue state. Use outbox publisher + reference payload; ACK after the defined safe product state, and reconcile expired/lost delivery. External pull consumers require scoped vendor credentials. Managed queue uptime does not cure failure of the FastAPI/DB lease authority.
- **Prefect** is already used for data pipelines; it may be suitable if research itself becomes a durable multistep workflow with independently resumable activities. Avoid dual authorities over a single job state without a designed state mapping. Hatchet/Temporal require a separate evaluation if workflow complexity warrants them.
- **PostgreSQL direct from workers** changes trust boundaries by distributing DB credentials and connectivity; don't introduce it merely to avoid a small HTTPS API.
- Do not fabricate zero-cost “adapter swaps”. A new transport has its own visibility timeout, ACK/retry, DLQ, credentials and operational tests. Stable **domain contracts** minimize rewrites but do not eliminate integration work.

## Rollout gates

1. Capture existing research and commercial states and all outbox rows; record baseline versioned source and infrastructure topology.
2. Define one lease grant data contract and concurrency/fencing tests shared by reference and pull modes.
3. Verify from commit to grant; timeout-after-commit; duplicate claims; expired leases; process-group crash after model one/two; cancel; artifact persistence and quota settlement; remote NAT-only access; Stripe event retries.
4. Load-test actual PostgreSQL 16 schema, FastAPI worker/thread/pool behavior and degraded-memory/backup scenario, with measured SLOs and alerts.
5. Use isolated dev/staging cutover rehearsal. Check pending work (prelaunch should be empty); activate exactly one route; run real-model canaries with approval; verify observability.
6. Record rollback conditions and avoid re-enabling the old publisher against already migrated jobs without reconciliation.

Only declare “implemented”, “validated”, or “operational” after the corresponding evidence exists.
