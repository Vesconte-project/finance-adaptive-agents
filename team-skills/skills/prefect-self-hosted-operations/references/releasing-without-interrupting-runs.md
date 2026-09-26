# Releasing Prefect components without interrupting runs

## Readiness after a worker restart

"Worker `ONLINE`" can be a stale record from before the restart, and so can a heartbeat: the old
process may heartbeat after activation begins but before it is stopped. Tie the evidence to the
restart itself — record the time the service manager reports the new process started (and its
PID), then require the exact worker name to report a `last_heartbeat_time` **later than that
start**. Only that proves the new process connected.

## Which runs a restart affects

- Restarting a worker kills the flow processes it runs.
- Restarting the Prefect **server** takes the API away from every pool: running flows cannot
  report state or logs, and workers cannot submit scheduled runs. Whether an active flow process
  survives that depends on the deployment, so treat it as a control-plane availability risk and
  wait for a free window in all pools, not just one.

## A window gate instead of a blind restart

A release channel that activates on merge should ask the API before restarting. The numbers
below are what one workspace chose for its schedules and run lengths; they are illustrations,
not defaults. Derive yours from your schedules, measured run durations, and release policy.

- defer if a run is `RUNNING`/`PENDING` in an affected pool, or if one is scheduled within a
  safety margin (there: 45 minutes, for runs of tens of minutes);
- retry on a short timer (there: 5 minutes, costing about 1.5 s of CPU per attempt once
  dependencies were installed);
- expire after a fixed limit (there: 6 hours) and alert;
- fail closed when the API does not answer.

Measure how often the gate closes before relying on it. In that workspace, with 15 scheduled runs a day and a
45-minute margin, one pool was closed about 9 hours in 24, with a longest block of 90 minutes;
a pool with one daily run was closed under an hour.

## Warn relative to the forecast, not a fixed threshold

A fixed "still pending after N minutes" warning fires falsely whenever a merge lands before a
dense block of scheduled runs. Compute the expected clear time from the schedules and
conservative per-deployment durations at the first deferral, keep that first forecast, record
revisions with a reason, and warn only when reality exceeds the forecast. Give "orchestrator API
unreachable" its own, earlier signal.

## Client and server versions

Workers on a newer Prefect client than the server work, with a warning in the server log. Treat
it as an unmeasured risk: pick one reference version, and whenever either side upgrades, verify
deployment publication, heartbeats, and one run per pool.
