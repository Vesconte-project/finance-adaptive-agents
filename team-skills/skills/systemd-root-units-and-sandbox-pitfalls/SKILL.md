---
name: systemd-root-units-and-sandbox-pitfalls
description: Use when auditing or changing what a root-run systemd unit executes — its executable and ancestor directories, EnvironmentFile, root steps marked + or ! inside a sandboxed unit, or secrets passed on its command line. Not for ordinary non-root units, memory or exit-code tuning, or SSH listener checks.
---

# systemd root units and sandbox pitfalls

Failure modes around what root executes under systemd, each of which looked correct on review
and was wrong in practice. They complement, not replace, `systemd.exec(5)` and
`systemd.service(5)`. This Skill does not grant root; privileged changes follow the host's own
authorisation.

**Evidence scope.** One Ubuntu host with systemd, 2026-09. Items marked *verified* were
reproduced there, not on every distribution or systemd version. Reproduce the behaviour on your
own host before relying on it.

For the details, read
[references/root-inputs-and-privilege.md](references/root-inputs-and-privilege.md).

## The two rules that caught real problems

1. **Anything that controls what root executes is a root input.** That includes every ancestor
   directory of the executable, and the `EnvironmentFile` when its variables choose paths or
   output locations. Changing only the leaf file's owner is not a fix.
2. **Prove privilege; do not infer it from documentation.** A step meant to run as root must log
   its effective uid and the result of its reads, and the check must require that line. A guard
   that cannot read its inputs typically "passes" with nothing compared.

## Audit method

To find root execution paths writable by an unprivileged account:

1. **Pick the right units.** Inventory the **system manager**, not just a user manager:
   inspect both `systemctl --system list-unit-files --type=service --no-pager` for installed
   files/templates and `systemctl --system list-units --type=service --all --no-pager` for
   currently loaded instances, including active, failed and transient services. Reconcile the
   union by unit identity and inspect relevant templates, runtime/generated configuration and
   drop-ins. Record command failures, access limits, version and capture time; neither listing
   alone nor their union proves every short-lived service over an interval was captured.
   Recheck or use authorised lifecycle records if services can appear during the audit. A user
   manager's units run as that user; include its privileged interactions only when in scope.
2. **Establish the effective identity** with `systemctl show -p User -p DynamicUser <unit>`.
   Resolve `User=` to its numeric UID: `root`, `0`, or another account resolving to UID 0
   are all root identities. An unset `User=` in a system service normally defaults to root
   unless `DynamicUser=yes` allocates a service identity. If resolution is unavailable, mark
   identity unknown, not non-root. Inspect the running process effective UID and namespace
   as corroboration; UID 0 in a user namespace need not grant host-root access. `+` and `!`
   prefixes bypass configured identity changes for individual commands; include them even
   in otherwise non-root units and verify their effective privilege.
3. **Cover every command directive**, not just `ExecStart`: `ExecCondition=`, `ExecStartPre=`,
   `ExecStartPost=`, `ExecReload=`, `ExecStop=`, `ExecStopPost=`. For each, check the executable,
   absolute path arguments, `WorkingDirectory`, and `EnvironmentFile`, plus every parent
   directory of each.
4. **Check write access, not ownership.** A root-owned directory can still be writable by
   others through group or other mode bits or an ACL. For each path component check mode,
   group membership, and `getfacl`, and resolve symlinks (`namei -l`).

Distinguish executable or configuration paths from runtime sockets and data paths. One instance
found by accident usually means the question was never asked systematically.

Inventory references checked 2026-10-20: [systemctl list-units/list-unit-files](https://www.freedesktop.org/software/systemd/man/latest/systemctl.html) and [systemd.unit load paths](https://www.freedesktop.org/software/systemd/man/latest/systemd.unit.html). Check the installed release; listing output is a time-bound view, not a universal completeness guarantee.
