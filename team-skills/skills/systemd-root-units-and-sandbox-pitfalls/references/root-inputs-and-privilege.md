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
  `/usr/local/libexec/`), `0755`, with every ancestor root-owned, not writable by any other
  account through group or other bits or an ACL, and no links through user-writable
  locations.
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
start units on that host under its change policy, start a disposable probe with the same
directives. Without that authorisation, inspect (`systemctl cat`, `systemd-analyze security
<unit>`) and hand the probe to someone who holds it. Runtime unit files and API-created
transient units are distinct. State retention depends on actual references, jobs and
`CollectMode=`; capture invocation-specific evidence before it can be collected. For a suitable
oneshot probe, `RemainAfterExit=yes` may keep it active after success, but another `start` will
not rerun it until it is stopped. Verify stop/cleanup and do not change production lifecycle
just to retain a probe result.

## Secrets on the command line (verified)

Treat a secret in `ExecStart` (for example `--token <value>`) as unsafe by default. Two separate
exposures:

- **Process arguments.** With default procfs settings any local user can read them through `ps`
  or `/proc/<pid>/cmdline`; a `hidepid=` mount option restricts that. Check the host rather than
  assuming either way.
- **The unit file.** Unit files are usually world-readable, so the value is exposed to every
  local account regardless of procfs.

First establish how the application consumes the secret. Prefer a supported token-file or
systemd credential-file interface (`LoadCredential=`) where available. The service must read
the file directly: reading its contents into an argument still leaks the value. A root-owned
`0600` `EnvironmentFile` avoids literal storage in the unit, but keeps a secret out of argv
**only if the application consumes the environment directly**. For example,
`ExecStart=/path/app --token ${TOKEN}` puts the expanded token back into argv. Environment
inheritance and inspection remain additional exposure paths; it is not equivalent to protected
credential files.

Verify the resulting argv and consumption method through a non-secret sentinel in an isolated
reproduction; do not print real process arguments or secret values as evidence. Check file
access, child inheritance and logs. Rotate a credential when exposure to an unauthorised account
or process occurred or cannot be excluded, within the approved rotation/recovery procedure.

## Group membership that is root in disguise

Do not infer privilege from a group name alone. Establish which daemon socket/API the account
can actually access, the daemon's host privileges, rootless/user-namespace mode and applicable
authorisation restrictions. Unrestricted access to a rootful Docker daemon or privileged LXD
local control can grant host-root-equivalent power; rootless or restricted configurations need
their own assessment. Compare the powers actually available with sudoers restrictions: a narrow
sudo rule cannot contain an independent host-root grant, but may remain meaningful when no such
grant exists. Test only with authorised non-destructive probes, not a privileged container launch.

## Primary references

Checked 2026-10-19; use the installed release documentation: [systemd.exec](https://www.freedesktop.org/software/systemd/man/latest/systemd.exec.html), [systemd.service](https://www.freedesktop.org/software/systemd/man/latest/systemd.service.html), [systemd.unit garbage collection](https://www.freedesktop.org/software/systemd/man/latest/systemd.unit.html#Unit%20Garbage%20Collection), [Docker post-installation security note](https://docs.docker.com/engine/install/linux-postinstall/), and [LXD security model](https://canonical.com/lxd/docs/latest/explanation/security/).
