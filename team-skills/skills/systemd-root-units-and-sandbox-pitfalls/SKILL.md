---
name: systemd-root-units-and-sandbox-pitfalls
description: Use when auditing which paths or environment files control what a root systemd unit executes, running root steps (+ or !) inside a sandboxed unit, choosing OOMPolicy for a worker that spawns job processes, adding a non-failure exit code to a unit and its callers, verifying transient systemd-run oneshot units, keeping secrets off unit command lines, or checking where socket-activated OpenSSH listens. Not for writing ordinary units with no such concern.
---

# systemd root units and sandbox pitfalls

These are failure modes that looked correct on review and were wrong in practice. They complement, not replace, the systemd manual
pages. This Skill does not grant root; privileged changes follow the host's own authorisation.

**Evidence scope.** One Ubuntu host with systemd and socket-activated OpenSSH, 2026-09. Items
marked *verified* were reproduced there, not on every distribution or systemd version; items
marked *not yet verified* are reasoned risks. Reproduce the behaviour on your own host before
relying on it.

Route to the one reference you need:

- A root unit, its executable, its `EnvironmentFile`, a root step inside a sandboxed unit, or a
  secret on a command line → [references/root-inputs-and-privilege.md](references/root-inputs-and-privilege.md)
- `MemoryMax`, `OOMPolicy`, exit codes that mean "not a failure", or transient units →
  [references/memory-exit-codes-transient-units.md](references/memory-exit-codes-transient-units.md)
- Where SSH actually listens, or which `sshd_config` value wins →
  [references/ssh-socket-activation.md](references/ssh-socket-activation.md)

## The three rules that caught real problems

1. **Anything that controls what root executes is a root input.** That includes every ancestor
   directory of the executable, and the `EnvironmentFile` when its variables choose paths or
   output locations. Changing only the leaf file's owner is not a fix.
2. **Prove privilege; do not infer it from documentation.** A step meant to run as root must log
   its effective uid and the result of its reads, and the check must require that line. A guard
   that cannot read its inputs typically "passes" with nothing compared.
3. **A new state must be represented in every layer.** An exit code that means "deferred" is a
   failure to systemd, to the caller using `check=True`, and to the CI job, unless each layer is
   told otherwise.

## Audit method

To find root execution paths writable by an unprivileged account, enumerate every installed
service unit with an effective root identity (`User=root` or no `User=`), then check each
`ExecStart*` executable, absolute path arguments, `WorkingDirectory`, and `EnvironmentFile` —
and every parent directory of each — for write access by that account. Distinguish executable
or configuration paths from runtime sockets and data paths. One instance found by accident
usually means the question was never asked systematically.
