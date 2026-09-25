# Memory limits, exit codes, and transient units

## OOM kills the whole unit by default (verified on one host)

With the default `OOMPolicy=stop`, when the kernel OOM-kills any process in a service's cgroup
the whole unit is stopped. For a worker that spawns job processes, one oversized job then takes
the worker down; with auto-restart the unit returns, but an orchestrator may keep waiting for a
child that no longer exists.

For such workers, consider a cgroup ceiling that keeps the unit alive:

```ini
MemoryMax=<ceiling>
OOMPolicy=continue
```

If the OOM killer picks the job process, it dies with a visible failure and the worker keeps
serving. That depends on which process is killed and how the worker supervises its children, so
validate it for your unit: force an oversized job and confirm the worker survives and the job is
reported failed. Measure
`MemoryPeak`/`memory.current` per job stage before choosing the ceiling; a unit-level peak does
not attribute memory to a stage, and swap in use at rest shrinks real headroom.

## Exit codes that are not failures (verified)

If a service returns a dedicated code for an expected non-success outcome (illustration: 75 for
"deferred, retry later"), declare it:

```ini
SuccessExitStatus=75
```

and use a *different* code for the outcome that must still fail (illustration: 76 for "expired").
Choose codes and caller behaviour for your own service.
Then check each caller: a client using `check=True`, a shell with `set -e`, and a CI step will
all treat the code as failure unless they are changed too. A job shown red for a legitimate
deferral also stops later steps in the same script from running.

## Transient oneshot units lose their identity (verified)

A transient `Type=oneshot` unit started with `systemd-run` and referenced by nothing is unloaded
as soon as it becomes inactive, taking its `InvocationID` with it; a verifier that then looks up
the invocation fails. Use `RemainAfterExit=yes`, read the invocation ID while the unit is loaded,
verify its journal, then stop and remove it and reload.

