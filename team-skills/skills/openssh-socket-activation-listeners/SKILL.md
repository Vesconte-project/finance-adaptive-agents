---
name: openssh-socket-activation-listeners
description: Use on hosts with confirmed or suspected systemd socket activation of OpenSSH (ssh.socket) to check listening addresses, investigate disagreement between sshd -T and kernel listeners, or interpret sshd configuration precedence for that socket-activated setup. Not for general sshd hardening without socket activation, SSH clients, or key generation.
---

# OpenSSH under socket activation

Practice learned hardening remote access on a host where OpenSSH runs by socket activation. It
does not grant root or authorise changing a host's remote access; keep an existing session open
and follow the host's own authorisation for any change.

**Evidence scope.** One Ubuntu host with socket-activated OpenSSH, 2026-09. Confirm the behaviour
on your release before relying on it.

## Where SSH actually listens (verified)

On Ubuntu releases where OpenSSH runs by socket activation, the listening sockets belong to
`ssh.socket`, not to `sshd`. `sshd -T` reports `sshd`'s own view (for example
`listenaddress 0.0.0.0:22`) even when the socket is bound only to one address. Always verify with
the kernel:

```text
systemctl cat ssh.socket     # includes applicable drop-ins
ss -tlnp                    # inspect exact local address and port columns
```

Discover all expected ports and address families from the effective socket configuration and
compare exact kernel endpoints; do not assume port 22 or use substring matching that also
accepts 2222. An inaccessible process-owner field does not make a listener absent.

Consequences:

- A restriction to one interface (for example a VPN or tailnet address) that lives only in a
  socket drop-in is invisible to `sshd -T`. Document it and check the kernel listener in any
  hardening verifier, or a later switch to `ssh.service`, or a package upgrade that regenerates
  the socket from `sshd_config`, can silently re-expose SSH on every interface.
- *Not yet verified:* binding the socket to an address owned by a VPN interface can fail at boot
  if the socket starts before the interface has its address. Confirm `FreeBind=yes` or explicit
  ordering against the VPN service before relying on it for the only remote access path.

## Which configuration value wins (verified)

In `sshd_config`, **most keywords use the first obtained value**, unless their own documentation
says otherwise. Some accumulate multiple occurrences, including `ListenAddress` and `Port`;
check the target release's keyword documentation before applying a precedence rule. Drop-in files count only where
an `Include` line pulls them in, and they are read at that point, in lexical order. On a host
whose main file starts with `Include /etc/ssh/sshd_config.d/*.conf` (as on the one observed),
`00-hardening.conf` beats a later `50-cloud-init.conf` that sets `PasswordAuthentication yes`,
and both beat the main file's own lines after the `Include`. Check where your `Include` sits and
which files it matches before reasoning about order.

Use `sshd -T` to inspect effective settings where the installed configuration and file access
allow it. Required privileges depend on that setup; permission failure is not evidence of the
settings and does not authorise broader access. Use authorised output supplied by an operator
when needed. For a `Match` block, pass the connection context, for example
`sshd -T -C user=<name>,host=<host>,addr=<ip>`.

## Before disabling password authentication

Confirm at least one working key per person or device that needs access, in its own key pair
with an identifying comment, and keep an existing session open while testing a new login. One
key per device lets each be revoked alone.

Source checked 2026-10-19: [OpenSSH sshd_config](https://man.openbsd.org/sshd_config), including `Include`, `ListenAddress`, `Port`, and `Match`. This upstream manual does not establish how a distribution generates `ssh.socket`; inspect the installed packaging and effective socket.
