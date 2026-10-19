# Choosing and migrating a dispatch transport

Applies after confirming a PostgreSQL/FastAPI lease authority as described in the entrypoint.
The [optional Finance proposal](finance-migration-case.md) retains repository-specific
workstreams and assumptions; it does not prescribe them for another workspace.

## Inventory before choosing

Locate durable job/reservation/attempt state, every publisher/consumer and recovery path,
worker claim contract, administrative tasks and unrelated business events sharing transport.
Record actual versions, topology, service identities and measured demand. An empty new
product can differ materially from a system with live queued work.

- PostgreSQL/HTTPS pull can fit long jobs with existing application-owned leases and
  outbound-only remote workers. Measure eligibility scans, database pools and waiters before
  choosing it. Worker count or an estimated volume alone is not a capacity demonstration.
- RabbitMQ/Celery may fit routing or shared-service delivery requirements. Check deployed
  versions, acknowledgments, redelivery, QoS and durability; none replaces application fencing.
- Managed queues such as SQS or Cloudflare Queues may reduce distribution operations, but
  add credentials, visibility/acknowledgment and redelivery semantics. Their availability does
  not repair an unavailable application lease authority. Map durable publication/recovery,
  including an outbox when needed, rather than assuming messages and database commit are atomic.
- A workflow orchestrator can fit independently resumable multistep work. Do not assume
  Prefect or another product is installed, or create competing authorities over one job state.
- Giving remote workers database credentials changes the trust boundary. Evaluate that
  independently instead of treating direct SQL as a drop-in replacement for authenticated HTTPS.

## Migration without losing obligations

1. Define the desired claim contract: an ID still needs an authorized claim; an already issued
   lease grant must not be claimed a second time. Preserve fencing, heartbeat, cancellation,
   event/result reporting and process cleanup at this boundary.
2. Adapt expired-lease recovery and scheduled work to the chosen discovery path. Preserve
   unrelated commercial or maintenance tasks with bounded retries and operator visibility;
   removing one queue must not silently remove every function using it.
3. Inventory pending messages and durable records. Reconcile/drain or explicitly migrate
   them before deleting publishers, dependencies or infrastructure. A staged cutover must
   fence competing acquisition paths; a direct prelaunch cutover still needs verified empty
   state and a tested rollback. Never assume both transports can run independently safely.
4. Rehearse in an authorized isolated environment: lost response after commit, duplicate claim,
   expired lease, stale result, worker restart, partial output, cancellation and settlement.
   Include every actual executor stage and unrelated task type, not a universal two-model pair.
5. Load-test the actual schema, isolation level, API/thread/connection pools and topology;
   measure backlog, lease loss and dispatch latency under representative constraints. Backup
   overlap or NAT-only workers matter only where the deployment has those conditions.
6. Cut over only within authorized scope. Reconcile before rollback so old publishers do not
   redispatch migrated work. External paid canaries require approval; synthetic evidence alone
   does not establish real executor cost or production recovery.

Stable domain contracts reduce migration work but do not make transports plug-compatible.
Declare implementation, validation and operation separately, with their actual evidence.
