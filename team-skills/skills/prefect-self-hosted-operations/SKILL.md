---
name: prefect-self-hosted-operations
description: Use when deploying, operating, or diagnosing a self-hosted Prefect 3 server with process workers and git-based deployment pull steps — crashed or zero-duration runs, parent flows waiting on child deployments, deployment job variables, worker restarts, or releasing new code without interrupting scheduled runs.
---

# Self-hosted Prefect 3 operations

Practice learned running a self-hosted Prefect 3 control plane with process workers on one host,
where deployments pull code from Git at run time. It covers behaviour that the documentation does
not make obvious and that produced real incidents.

**It authorises nothing.** Restarting a worker or the server, republishing deployments, changing
schedules, job variables or environments, rotating credentials, and touching production data
must be covered by the user's authorisation and the workspace's own change procedure. Existing
authorisation suffices within its scope; obtain it only when missing. Otherwise diagnose and propose.

**Evidence scope.** Prefect server 3.7.x with workers on 3.8.x, two work pools, `git_clone` pull
steps over SSH, 2026-08 → 09. Re-check version-sensitive API behaviour on other versions.

## Diagnose from the full run record, not the summary

- A run can be `CRASHED` with `total_run_time=0` **after** real work happened: the worker
  submitted it, ran the pull step, `git clone` failed (exit 128), Prefect retried the clone once,
  and the flow code never started. Zero run time is consistent with a flow that never began, but does not prove it: correlate
  state history, infrastructure/worker logs and flow-side evidence. It never proves nothing was attempted.
- The short failure summary can hide the decisive detail. In one incident three identical
  summaries omitted the repository URL; the full log message (`/api/logs/filter` for the run)
  showed the pull step pointing at the wrong owner and host. Read the complete message before
  declaring a cause unknown.
- A run's Prefect state duration is not compute time. A run left waiting on a dead child can show
  tens of thousands of seconds in state while doing nothing.
- Separate failure modes before measuring anything: startup (pull/clone) failures, in-flow
  failures in a stage, and process kills (OOM) need different fixes and must not be averaged into
  one "instability".

## Pull steps run on every flow run

- `git_clone` pull steps execute at the start of **every** run, with the configuration stored in
  the deployment version that run used. Fixing `prefect.yaml` does nothing until deployments are
  republished; check the run's `deployment_version`.
- Pin the pull step to the exact commit being deployed and verify **every** stored pull step
  after publication. When listing deployments, compare the count endpoint with the listed items
  and fail closed if pagination could hide some.
- Add a read-only preflight that compares each pull step's repository (owner and SSH host alias)
  with the canonical remote and refuses divergence, so a wrong remote is caught before the nightly
  run, not by it.

## Deployment job variables are a hidden configuration layer

Deployment job variables are persisted configuration, potentially including plaintext secrets.
For process workers, inspect the actual work-pool base job template, deployment and per-run
overrides, worker version, and subprocess environment construction: a conflicting `env` entry
may override an inherited worker value, but neither inheritance nor precedence is universal.
Use a disposable non-secret sentinel to verify which source reaches the flow; variable presence
in the worker alone does not prove the child consumed it.

Version ordinary per-deployment configuration where appropriate. Use the workspace's approved
secret injection (for example a runtime secret store or service credential mechanism supported
by the application), with access limited to the intended process. Do not assume the worker's
environment is always the right or safer destination. Check whether publication resolves a
reference to plaintext in API-visible configuration; assess access and rotate credentials where
unauthorised exposure occurred or cannot be excluded. Avoid broad API/log/environment dumps.

Reference checked 2026-10-19: [Prefect job variables](https://docs.prefect.io/v3/how-to-guides/deployments/customize-job-variables). It documents overrides and publication-time environment templating; verify the installed template rather than assuming it.

## Parent flows and child deployments

- `run_deployment(..., timeout=None)` returns when the child reaches **any** final state. A parent
  that does not check for `COMPLETED` will report success after a failed or crashed child.
- Compute a run's logical date once, at flow start. Computing it at decision time lets a run that
  starts before midnight UTC ask for a day that does not exist yet.
- A trigger flag that controls whether a parent launches a child belongs in versioned deployment
  parameters, not in a manual API edit that the next publication silently reverts.

Read [references/releasing-without-interrupting-runs.md](references/releasing-without-interrupting-runs.md)
before restarting workers or the server as part of a deploy.

## "Completed" is not "produced"

Flows that return early — missing provider configuration, missing model pointer, watermark gate —
finish `COMPLETED` with nothing written. Emit an explicit outcome (for example
`skipped_configuration`, `blocked_precondition`, `no_work_expected`, `produced`, `partial`) and
check destinations for freshness independently; a green run is not evidence of new data.
