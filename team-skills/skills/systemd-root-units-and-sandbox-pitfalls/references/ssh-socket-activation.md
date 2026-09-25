# SSH under socket activation

## Where SSH actually listens (verified)

On Ubuntu releases where OpenSSH runs by socket activation, the listening sockets belong to
`ssh.socket`, not to `sshd`. `sshd -T` reports `sshd`'s own view (for example
`listenaddress 0.0.0.0:22`) even when the socket is bound only to one address. Always verify with
the kernel:

```text
ss -tlnp | grep ':22'
systemctl cat ssh.socket     # plus drop-ins under /etc/systemd/system/ssh.socket.d/
```

Consequences:

- A restriction to one interface (for example a VPN or tailnet address) that lives only in a
  socket drop-in is invisible to `sshd -T`. Document it and check the kernel listener in any
  hardening verifier, or a later switch to `ssh.service`, or a package upgrade that regenerates
  the socket from `sshd_config`, can silently re-expose SSH on every interface.
- *Not yet verified:* binding the socket to an address owned by a VPN interface can fail at boot
  if the socket starts before the interface has its address. Confirm `FreeBind=yes` or explicit
  ordering against the VPN service before relying on it for the only remote access path.

## Which configuration value wins (verified)

In `sshd_config`, **the first obtained value for a keyword wins** — the opposite of many
configuration systems and of systemd `EnvironmentFile` stacking. Drop-ins in
`sshd_config.d/` are read in lexical order, so `00-hardening.conf` beats a later
`50-cloud-init.conf` that sets `PasswordAuthentication yes`. Rely on `sshd -T` (run as root) for
the effective authentication settings, not on reading one file.

## Before disabling password authentication

Confirm at least one working key per person or device that needs access, in its own key pair
with an identifying comment, and keep an existing session open while testing a new login. One
key per device lets each be revoked alone.
