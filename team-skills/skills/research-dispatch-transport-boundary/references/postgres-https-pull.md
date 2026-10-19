# PostgreSQL + HTTPS pull: protocol and failure checklist

Use only after confirming the PostgreSQL/FastAPI authority and actual transaction semantics.
Endpoint names are example contracts, not evidence that the target implements them.

## One atomic acquisition; no long transaction while idle

1. Authenticate the **service** identity at the FastAPI boundary. Verify environment, permitted pool/capability and client rate/concurrency; do not trust worker-declared account, plan or arbitrary resource fields.
2. If no worker slot is available, do **not** request a job. Otherwise make one `AcquireWork` call with a bounded deadline, idempotent request ID where supported and a capability filter enforced server-side.
3. Within a **short PostgreSQL transaction**, choose a bounded set of eligible jobs with a suitable partial index and deterministic tie-breaker, using `SELECT ... FOR UPDATE SKIP LOCKED`; update exactly one to a new lease generation, random lease token, deadline and attempt marker. Return a grant with job ID, generation, lease token, execution descriptor and cancellation status. Use database/server authoritative time for deadlines, not a remote worker's clock. If already terminal, do not grant another attempt.
4. Commit **before** returning the grant. If empty, release connection/transaction **before** any long-poll wait. Waiting with a held SQLAlchemy session or FastAPI sync thread can exhaust connection and thread pools.
5. Wake from local short timer/jitter, DB notification or another safe event mechanism; re-query at timeout, startup, reconnect and recovery intervals. `LISTEN/NOTIFY` notifications are not persisted for disconnected listeners; subscribe/commit and inspect table state before relying on notifications. Do not rely on notification delivery for correctness.
6. Only one component owns lease grant semantics. A supervisor consuming a returned grant must **not** call the old `/{job_id}/claim` again. A transport delivering only an ID *can* use that older claim contract.
7. Bounded heartbeats, abort-on-lease-loss and fencing are required. For large artifacts/results, validate the object/metadata commit ordering before settling quota. Do not hold transactions across model calls or HTTP waits.

`SKIP LOCKED` is a concurrency tool, not strict FIFO: locked rows may be bypassed, and an ordering by creation time with tie-breaker is only best-effort under concurrent locks. Fairness/aging, priorities and starvation protections need explicit policy if required.

## Hard failure matrix

| Failure | Required recovery |
| --- | --- |
| Job committed, API crashes before response | Client retries submission idempotently; job remains discoverable |
| Claim transaction commits, HTTP response lost | Lease expires; job becomes eligible again; never erase from DB |
| Two workers claim concurrently | At most one active grant/generation for a job |
| Claim timeout/cancel during long-poll | No orphan DB transaction or occupied pool slot |
| Worker dies after a partial execution stage | Lease recovery, idempotent artifact writes, no double quota charge |
| Old worker completes after fencing | Reject generation/token, including events and variants |
| Backend or Tunnel is offline | Workers back off; durable jobs stay in PostgreSQL |
| PostgreSQL restart | No accepted job lost; abandoned leases recover on restart |
| `NOTIFY` missed | Periodic scan finds work; alert if backlog grows |
| Worker repeatedly returns 5xx | Bounded exponential backoff and jitter; do not thundering-herd |
| Lease expired during long external call | Worker detects loss and stops best-effort; external cost may have occurred |
| Subscription changed after acceptance | Apply documented policy for accepted/reserved work, not a new untrusted decision |

Use short transactions, indexed eligibility scans, bounded page size and account/environment scoping. Query plans, dead tuples, autovacuum, WAL pressure, lock contention and pool exhaustion must be monitored at the **actual deployed database isolation level**.

## Operational acceptance

Measure p50/p95/p99 time from eligible to granted; duplicate attempt rate; leases expired; failed heartbeats; backlog age; DB CPU, locks, dead tuples, autovacuum lag, WAL, pool occupancy; worker slot utilization and concurrent long-polls. Test in an authorized isolated environment with the actual schema and executor stages,
representative inputs and network interruptions. Include constrained memory, backup overlap
and outbound-only remote workers where relevant to that topology; do not introduce those
constraints into an unrelated system. Real paid calls need explicit authorization.

Choose review thresholds from the application's measured baseline and approved SLOs. The
source proposal used >1 job/s, >100 concurrent waits or p95 dispatch >5s as illustrative
review triggers only, not database limits or defaults. Machine count alone is not a
transport migration trigger.

## Sources (version-aware; re-check)

- PostgreSQL 16 locking and `SKIP LOCKED`: https://www.postgresql.org/docs/16/sql-select.html
- PostgreSQL 16 LISTEN startup race: https://www.postgresql.org/docs/16/sql-listen.html
- PostgreSQL 16 monitoring: https://www.postgresql.org/docs/16/monitoring-stats.html
