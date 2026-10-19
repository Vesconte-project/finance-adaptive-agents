---
name: systemd-service-exit-and-oom-semantics
description: Use when a systemd service that spawns job processes is stopped by an OOM kill, when choosing MemoryMax or OOMPolicy for such a worker, when adding an exit code that must not count as a failure to a unit and its callers, or when a later lookup of a transient systemd-run oneshot unit or its InvocationID fails. Not for writing ordinary units or for tuning application memory use.
---

# systemd service exit and OOM semantics

How systemd decides a service failed, and what that does to its callers — behaviour that looked
correct on review and was wrong in practice. It complements `systemd.service(5)` and
`systemd.resource-control(5)`. This Skill does not grant root; unit changes follow the host's own
authorisation.

**Evidence scope.** One Ubuntu host, 2026-09; the original systemd version, kernel version and
cgroup mode were not recorded and remain unknown. *Verified* below denotes that historical
observation, not a reproducible version matrix. Before relying on it, record `systemctl --version`,
kernel and effective cgroup/controller setup for the target, check supported directives and
properties in that release, then reproduce in an authorised disposable environment.

## OOM policy can stop the whole unit (observed on one host)

With an effective `OOMPolicy=stop`, a kernel OOM kill in the service can cause the rest of the
unit to be stopped. Do not infer the effective policy from an omitted unit directive: the
manager's `DefaultOOMPolicy=` applies, except that units with `Delegate=yes` default to
`continue` in the documented current contract. Inspect the effective unit, manager settings,
installed version and logs; a different termination mechanism (including systemd-oomd) needs
its own evidence. For a worker that spawns job processes, one oversized job can then take
the worker down; a configured successful restart can bring the unit back, while an orchestrator
may keep waiting for a child that no longer exists.

For such workers, a candidate design to test is a cgroup ceiling with continued supervision:

```ini
MemoryMax=<ceiling>
OOMPolicy=continue
```

If the OOM killer picks the job process, it dies with a visible failure and the worker keeps
serving. That depends on which process is killed and how the worker supervises its children, so
validate it in an authorised isolated representative test: trigger an oversized job, confirm
which process was killed, worker survival and the reported job outcome. Do not inject OOM on a
production host merely to test this guidance. Consider per-job isolation where the worker
supports it; `continue` does not guarantee the main process survives.

Detect measurement support before choosing a ceiling: the manager's `MemoryPeak` property is
not available on every systemd version, and kernel `memory.current`/`memory.peak` files depend on
the actual cgroup/controller setup and kernel. Missing or unsupported data is **unmeasured**,
not zero. Record the supported sampling method and interval; a unit-level peak does not
attribute memory to a stage. Measure swap, pressure and other consumers separately to estimate
headroom.

## Exit codes that are not failures (verified)

If a service returns a dedicated code for an expected non-success outcome (illustration: 75 for
"deferred, retry later"), declare it:

```ini
SuccessExitStatus=75
```

and use a *different* code for the outcome that must still fail (illustration: 76 for "expired").
Choose codes and caller behaviour for your own service.

Then check each caller, because they see different things:

- **Callers that run the program directly** — a script, `subprocess.run(..., check=True)`, a
  shell with `set -e`, a CI step invoking the binary — receive the raw exit code.
  `SuccessExitStatus=` does not affect them; each needs its own handling.
- **Callers that observe the unit** — `systemctl start` on a oneshot, `systemctl is-failed`,
  `OnFailure=`, dependent units, monitoring of the unit state — see systemd's verdict, which
  `SuccessExitStatus=` changes. Something that waits on the unit and returns its own status
  (for example `systemd-run --wait`) may pass the raw code through; confirm on your version.

A caller that treats the deferral code as failure can skip later steps. Test both the expected
deferral and genuine failure through each actual caller, including `systemd-run --wait` where
used; its exit-status behaviour must be checked against the installed version.

## A later lookup can lose the invocation (observed on one host)

A oneshot unit can become eligible for garbage collection when inactive and no longer needed.
Whether it is unloaded depends on actual references, jobs, running processes, failure state and
`CollectMode=`. Runtime files under `/run/systemd/system` are distinct from transient units
created through the manager API (`systemd-run`); location alone does not establish lifecycle.
Capture the `InvocationID` while the relevant execution is observable and verify only its
journal (for example `journalctl _SYSTEMD_INVOCATION_ID=<captured-id>`), preserving evidence
before cleanup. A missing or ambiguous ID means the lookup did not establish that invocation.

For an authorised disposable oneshot probe, `RemainAfterExit=yes` can retain `active (exited)`
after success; another `start` then does not rerun it until it is stopped. Validate that lifecycle
before adopting it; do not add the setting to production solely to preserve an audit lookup.

Clean up only the probe you created, after collecting evidence:

- For an API-created transient unit, stop the exact probe; if failed, reset its failed state
  when appropriate and authorised. Do not delete manager-generated files or run `daemon-reload`
  as generic transient-unit cleanup. References/jobs may still retain the unit: stop or
  reset-failed does not promise immediate unloading. Verify state and residual resources.
- If the probe instead created its own runtime unit file/drop-ins, stop it, remove only those
  owned probe artefacts and reload the changed unit configuration. Verify cleanup and report
  residual state; do not remove unrelated files or confuse retained journal evidence with a
  still-running process.

## Primary references

Checked 2026-10-20; use the installed release documentation: [OOMPolicy and SuccessExitStatus](https://www.freedesktop.org/software/systemd/man/latest/systemd.service.html), [resource controls](https://www.freedesktop.org/software/systemd/man/latest/systemd.resource-control.html), [manager properties including MemoryPeak](https://www.freedesktop.org/software/systemd/man/latest/org.freedesktop.systemd1.html), [unit garbage collection](https://www.freedesktop.org/software/systemd/man/latest/systemd.unit.html#Unit%20Garbage%20Collection), and [systemd-run](https://www.freedesktop.org/software/systemd/man/latest/systemd-run.html). These references do not recover the missing historical versions.
