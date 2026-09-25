# Root inputs, privilege, and secrets in units

## Root execution inputs (verified)

- A root unit executing a script under a home directory is a local privilege escalation even if
  the script itself is `root:root`: any writable ancestor lets the owner replace the file.
  Install root-executed code to a root-owned path (for example under `/usr/local/libexec/`),
  `0755`, with every ancestor root-owned.
- An `EnvironmentFile` that selects the interpreter, the checker, or a root-written log path is
  an execution input. Keep it `root:root 0600` in a root-owned directory.
- If a root job must run untrusted helper code (for example a check that lives in a working
  tree), drop privilege explicitly for that step (`runuser --user <account> -- …`) instead of
  letting it inherit root.
- Prove the fix by attempting the write as the unprivileged account (append-open the file,
  create a file in its directory) and observing `Permission denied`, not by reading modes.

## Root steps inside a sandboxed unit (verified)

The two prefixes bypass different things; check `systemd.service(5)` for your systemd version:

- `!` bypasses only the credential changes (`User=`, `Group=`, `SupplementaryGroups=`), so the
  command runs as root while the unit's other sandboxing — filesystem protection, namespaces,
  capability bounds — still applies.
- `+` runs the command with full privileges: it is not subject to `User=`/`Group=`,
  `CapabilityBoundingSet=`, or the filesystem-namespacing options (`ProtectSystem=`,
  `PrivateTmp=`, …). It does not drop every unit setting (cgroup and resource settings, for
  example, still apply), and it affects only that command line.

Choose `!` when the root step should stay inside the sandbox. Do not accept either by doctrine:
have the root phase print
something like `phase=<name> euid=0 inputs=<n> values=<m>` and make the verification require
that exact line from that invocation's journal. A root phase that silently fails to read its
inputs is indistinguishable from one that found nothing.

To test a unit's sandbox without touching the real unit, start a transient probe unit with the
same directives. A transient `Type=oneshot` unit is unloaded as soon as it becomes inactive, so
give it `RemainAfterExit=yes` and read its invocation ID and journal before removing it.

## Secrets on the command line (verified)

A token passed as an argument in `ExecStart` (for example `--token <value>`) is readable by every
local user through `ps` and the process table, and usually also sits in a world-readable unit
file. Move it to a root-owned `0600` `EnvironmentFile`, a token file option if the program has
one, or systemd credentials (`LoadCredential=`), then rotate it, because it has already been
exposed. These are not equivalent: an `EnvironmentFile` keeps the value off the command line but
places it in the process environment, readable by the same user and root through `/proc`;
credentials are delivered as files readable only by the service's user and root.

## Group membership that is root in disguise

Membership in `docker` or `lxd` is root-equivalent. A narrowly scoped sudoers entry for such an
account is decorative. Treat these memberships as privilege grants when auditing boundaries.
