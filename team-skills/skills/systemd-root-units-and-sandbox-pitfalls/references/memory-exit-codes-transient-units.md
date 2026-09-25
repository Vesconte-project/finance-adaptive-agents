# Memory limits, exit codes, and transient units

## OOM kills the whole unit by default (verified)

With the default `OOMPolicy=stop`, when the kernel OOM-kills any process in a service's cgroup
the whole unit is stopped. For a worker that spawns job processes, one oversized job then takes
the worker down; with auto-restart the unit returns, but the parent orchestration may wait for a
child that no longer exists (observed: 19 hours).

For such workers set a cgroup ceiling and keep the unit alive:

```ini
MemoryMax=<ceiling>
OOMPolicy=continue
```

The job process then dies with a visible failure and the worker keeps serving. Measure
`MemoryPeak`/`memory.current` per job stage before choosing the ceiling; a unit-level peak does
not attribute memory to a stage, and swap in use at rest shrinks real headroom.

## Exit codes that are not failures (verified)

If a service returns a dedicated code for an expected non-success outcome (for example 75 for
"deferred, retry later"), declare it:

```ini
SuccessExitStatus=75
```

and use a *different* code for the outcome that must still fail (for example 76 for "expired").
Then check each caller: a client using `check=True`, a shell with `set -e`, and a CI step will
all treat the code as failure unless they are changed too. A job shown red for a legitimate
deferral also stops later steps in the same script from running.

## Transient oneshot units lose their identity (verified)

A transient `Type=oneshot` unit started with `systemd-run` and referenced by nothing is unloaded
as soon as it becomes inactive, taking its `InvocationID` with it; a verifier that then looks up
the invocation fails. Use `RemainAfterExit=yes`, read the invocation ID while the unit is loaded,
verify its journal, then stop and remove it and reload.

## Retry after a failed apply

A scripted host change that rolls itself back should record `FAILED_ROLLED_BACK` in a way that
permits a later attempt with an incrementing attempt counter, after validating the retained
backup against baseline hashes. A receipt that permanently blocks retries turns a clean
rollback into a manual repair.
