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

1. **Pick the right units.** Enumerate the **system manager's** service units
   (`systemctl list-unit-files`, not `--user`); a user manager's units run as that user.
2. **Establish the effective identity** with `systemctl show -p User -p DynamicUser <unit>`. A
   unit runs as root only when `User=root`, or `User=` is unset **and** `DynamicUser=` is not
   `yes`. Remember that `+` and `!` command prefixes run individual commands as root even in a
   non-root unit — include those commands too.
3. **Cover every command directive**, not just `ExecStart`: `ExecCondition=`, `ExecStartPre=`,
   `ExecStartPost=`, `ExecReload=`, `ExecStop=`, `ExecStopPost=`. For each, check the executable,
   absolute path arguments, `WorkingDirectory`, and `EnvironmentFile`, plus every parent
   directory of each.
4. **Check write access, not ownership.** A root-owned directory can still be writable by
   others through group or other mode bits or an ACL. For each path component check mode,
   group membership, and `getfacl`, and resolve symlinks (`namei -l`).

Distinguish executable or configuration paths from runtime sockets and data paths. One instance
found by accident usually means the question was never asked systematically.
