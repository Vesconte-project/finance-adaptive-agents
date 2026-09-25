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

The `!` prefix on `ExecStart*` runs that command with elevated credentials while the unit's
other sandboxing (`ProtectSystem=`, `ProtectHome=`, `ReadWritePaths=`, `NoNewPrivileges=`) still
applies; `+` would drop the sandbox too. Do not accept this by doctrine: have the root phase print
something like `phase=<name> euid=0 inputs=<n> values=<m>` and make the verification require
that exact line from that invocation's journal. A root phase that silently fails to read its
inputs is indistinguishable from one that found nothing.

To test a unit's sandbox without touching the real unit, start a transient probe unit with the
same directives — but see the transient-unit caveat in the next reference.

## Secrets on the command line (verified)

A token passed as an argument in `ExecStart` (for example `--token <value>`) is readable by every
local user through `ps` and the process table, and usually also sits in a world-readable unit
file. Move it to a root-owned `0600` `EnvironmentFile`, a token file option if the program has
one, or systemd credentials; then rotate it, because it has already been exposed.

## Group membership that is root in disguise

Membership in `docker` or `lxd` is root-equivalent. A narrowly scoped sudoers entry for such an
account is decorative. Treat these memberships as privilege grants when auditing boundaries.
