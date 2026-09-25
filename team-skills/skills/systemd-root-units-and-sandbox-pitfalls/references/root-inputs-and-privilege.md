# Root inputs, privilege, and secrets in units

## Root execution inputs (verified)

- A root unit executing a script under a home directory is usually a local privilege escalation
  even if the script itself is `root:root`. Whoever can write the script's directory can rename
  it away and put their own file in its place. In a sticky (`+t`) directory only the entry's
  owner, the directory's owner, or root may rename or remove it — so a sticky directory is safe
  only if the unprivileged account owns neither. Whoever can write a higher ancestor can rename the whole
  subtree and substitute their own. Symlinks move the question to their targets: assess the
  resolved path (`namei -l <path>` lists owner and mode of every component, including links)
  and each link itself. Install root-executed code to a root-owned path (for example under
  `/usr/local/libexec/`), `0755`, with every ancestor root-owned and no links through
  user-writable locations.
- An `EnvironmentFile` that selects the interpreter, the checker, or a root-written log path is
  an execution input. Keep it `root:root 0600` in a root-owned directory.
- If a root job must run untrusted helper code (for example a check that lives in a working
  tree), drop privilege explicitly for that step (`runuser --user <account> -- …`) instead of
  letting it inherit root.
- Prove the fix as the unprivileged account, without touching the real file:
  - append-open the file itself: expect `Permission denied`;
  - for each **non-sticky** directory on the resolved path, create and remove a scratch entry:
    expect `Permission denied`;
  - for each **sticky** directory, creating a scratch entry may legitimately succeed and proves
    nothing; instead confirm that the account owns neither the directory nor the next entry on
    the path (`stat -c '%U %A'`).
  Reading modes alone is not proof for the non-sticky cases.

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

To test a unit's sandbox without touching the real unit, and only where you are authorised to
start units on that host under its change policy, start a transient probe unit with the same
directives. Without that authorisation, inspect (`systemctl cat`, `systemd-analyze security
<unit>`) and hand the probe to someone who holds it. A transient `Type=oneshot` unit is unloaded as soon as it becomes inactive, so
give it `RemainAfterExit=yes` and read its invocation ID and journal before removing it.

## Secrets on the command line (verified)

Treat a secret in `ExecStart` (for example `--token <value>`) as unsafe by default. Two separate
exposures:

- **Process arguments.** With default procfs settings any local user can read them through `ps`
  or `/proc/<pid>/cmdline`; a `hidepid=` mount option restricts that. Check the host rather than
  assuming either way.
- **The unit file.** Unit files are usually world-readable, so the value is exposed to every
  local account regardless of procfs.

Move it to a root-owned `0600` `EnvironmentFile`, a token file option if the program has one, or
systemd credentials (`LoadCredential=`). Rotate it if either exposure applied to any account or
process that should not hold it, or if you cannot tell — which is the usual case. These are not equivalent: an `EnvironmentFile` keeps the value off the command line but
places it in the process environment, readable by the same user and root through `/proc`;
credentials are delivered as files readable only by the service's user and root.

## Group membership that is root in disguise

Membership in `docker` or `lxd` is root-equivalent. A narrowly scoped sudoers entry for such an
account is decorative. Treat these memberships as privilege grants when auditing boundaries.
