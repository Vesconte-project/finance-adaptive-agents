# Releasing Prefect components without interrupting runs

## Readiness after a worker restart

"Worker `ONLINE`" can be a stale record from before the restart, and so can a heartbeat: the old
process may heartbeat after activation begins but before it is stopped. Tie the evidence to the
restart itself — record the new PID with start time, service invocation, intended release, and
worker identifier. Require a fresh heartbeat from a unique identity bound to that instance.
A reused worker name with a later timestamp is insufficient: another process can emit it.
If a unique identifier is unavailable, corroborate the new invocation's connection logs and
release evidence, and establish that prior/concurrent instances cannot heartbeat under that
name. Without those links, report readiness unverified. A ready worker still does not prove a
flow executed the intended Git commit.

## Which runs a restart affects

- A worker restart may terminate its flow processes. Inspect launch method, process ownership,
  process groups/cgroups, service-manager termination settings (including systemd `KillMode=`
  where applicable), and the installed worker shutdown behaviour. A detached or independently
  supervised flow may survive, but do not rely on that without evidence. Protect all potentially
  affected runs and verify their post-change state rather than assuming survival or termination.
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

In the recorded 2026-08 → 09 deployment, server 3.7.x and workers 3.8.x operated with a
warning in the server log. This is one bounded observation, not a compatibility guarantee.
Prefer a documented supported combination; verify publication, fresh instance-bound heartbeats,
API operations used by the release gate, and one representative run per pool whenever either
side changes. Record exact versions and unverified operations; newer clients are not assumed
compatible with older servers.

For systemd-managed workers, consult the installed [systemd.kill](https://www.freedesktop.org/software/systemd/man/latest/systemd.kill.html) documentation for cgroup termination modes (upstream reference checked 2026-10-19); this does not establish the installed Prefect worker's shutdown behaviour.
