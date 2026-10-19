# Decision evidence and epistemic status

**Recorded 2026-10-11.** Proposed user-requested target architecture; **not** Company OS Acceptance, proof of deployment or confirmation that the real research executor works.

## Evidence from GitHub main inspected on 2026-10-11

- `Vesconte-project/finance-backend` at `30db935bcd7fc6255c6f38eead775d7f2018b795`:
  - `app/platform_queue.py` configures Celery quorum routing and `OutboxPublisher.publish_one` using `SKIP LOCKED` with send/confirm in the open DB transaction. Research and commercial topics share transport but not necessarily domain semantics.
  - `app/platform_native_worker_api.py` offers authenticated job-ID claim, heartbeat, events, variants, complete and fail; **no claim-next endpoint observed** in that file.
  - `app/platform_scheduler.py` schedules recovery via new `research.execute` outbox references: this dependency must be replaced if broker notifications are removed.
  - `app/platform_commercial_worker.py` registers Celery tasks for Stripe reconciliation; cannot merely delete the broker and forget these functions.
- `Vesconte-project/finance-research-orchestrator` at `9ed4252ed0a5d5f26f1b8a8bd2abe163bbe77c57`:
  - `finance_research_orchestrator/platform_celery.py` consumes the research reference.
  - `platform_transport.py` speaks HTTPS to FastAPI using a worker credential; `platform_supervisor.py` receives an ID then calls claim and supervises a subprocess group. Accepting a **grant** needs an explicit boundary change.
- `Vesconte-project/finance-infra` at `3953718cf670a826a1931f0f180d711105c7ba0a`: `platform-local/compose.yaml` declares PostgreSQL 16 and RabbitMQ 4.3.6 with a 512 MiB container limit; a limit is not measured RSS. Production installed state was **not** examined. The orchestrator dependency pins Celery 5.6.3 and Kombu 5.6.2.

These observations are about Git sources, not proof of current running deployments, functional workload or independent end-to-end testing. The operator reports 7.1 GiB RAM and memory pressure during backups; no host memory sampling was performed here.

## Primary documentation and what it actually proves

- PostgreSQL 16 `FOR UPDATE SKIP LOCKED` explicitly permits queue-like use but yields an inconsistent view, not strict FIFO: https://www.postgresql.org/docs/16/sql-select.html
- PostgreSQL 16 LISTEN has an initialization race and is a signal, not a durable work record: https://www.postgresql.org/docs/16/sql-listen.html
- Celery 5.6 quorum support (introduced in 5.5) requires confirmation publishing and QoS care; this **does not certify** all Celery 5.6.3 + RabbitMQ 4.3.6 behavior in the target environment: https://docs.celeryq.dev/en/v5.6.3/userguide/configuration.html
- Cloudflare Queues supports HTTP pull consumers external to Workers, but that is a **different managed product** from in-house FastAPI HTTPS pull: https://developers.cloudflare.com/queues/configuration/pull-consumers/
- Quorum queues provide node-failure tolerance only with sufficient replicas/nodes; a single-node configuration does not create HA: https://www.rabbitmq.com/docs/quorum-queues

## Decision rationale and falsification

The recommended PostgreSQL + HTTPS pull path is driven by **existing** FastAPI lease authority, low expected demand, no clients to migrate, limited host resources and optional future remote workers. A broker may be justified later, but the trigger is **observed bottlenecks or delivery requirements**, not a company valuation or 30 worker servers alone. Worker count, network topology and DB read/write load need representative measurements before asserting safe scale.

Verify with independent tests and production-like model runs. Revisit this Skill if schema/SDK versions, company requirements, queue semantics or real traffic contradict these assumptions. Do not repeat vendor performance examples as Vesconte measurements.
