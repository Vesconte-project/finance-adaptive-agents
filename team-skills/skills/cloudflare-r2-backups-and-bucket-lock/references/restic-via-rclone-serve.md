# restic through `rclone serve restic`

**Evidence scope.** Observed 2026-10-17 in production: restic 0.19.1 talking to Cloudflare R2
through `rclone serve restic --stdio`, using the distribution rclone `v1.60.1-DEV`. A local
S3-compatible server in CI did **not** reproduce the failure without the flag, so treat the cause
as confirmed for that rclone build against R2, not as universal behaviour. Re-check with a newer
rclone before relying on it.

## Symptom

A weekly `prune` that repacks data fails with
`Fatal: failed to rewrite indexes: LoadUnpacked(<id>): <index/…> does not exist`. The named index
was written by the same `prune` seconds earlier, and reads fine from a new session. Backups and
restores keep working; maintenance only fails when there is something to repack, so it can pass
for weeks and then fail.

## Cause and fix

`rclone serve restic` caches the object listing taken at startup (`--cache-objects`, on by
default in that build). Objects written after the listing are reported as missing within the same
session. The fix is `--cache-objects=false`:

- Put it in the **single constant** every restic invocation uses (backup, restore, check, forget,
  prune and any retirement path). A second copy of the arguments will miss it.
- Reproduce first on a disposable repository with representative data and the same client path,
  within existing authorization. A local S3-compatible endpoint alone did not reproduce this
  incident; report that limit rather than treating a passing local run as an R2 verification.
- A real-repository `prune` requires authorization for that exact destructive maintenance and
  confirmation of retention compatibility and recovery prerequisites. If those are unavailable,
  prepare the proposed flag change and leave real validation pending. Do not remove retention
  rules or repository locks to force the probe through.
- After an authorized prune, check structure and locks, and distinguish that result from reading
  stored data. A full `check --read-data` verifies data within its actual coverage and resource
  budget; it is not a restore exercise. Failed attempts can leave extra indexes; reconcile their
  state before any cleanup rather than promising the next prune is safe or repairs every failure.

The distinction between structure and data checks is documented in
[restic integrity checks](https://restic.readthedocs.io/en/stable/045_working_with_repos.html#checking-integrity-and-consistency);
the destructive maintenance boundary is described in
[restic forget/prune](https://restic.readthedocs.io/en/stable/060_forget.html).
These documentation points were checked on 2026-10-19; they do not independently reproduce the
version-specific R2 incident above.

## Make the next diagnosis cheap

restic errors often contain the remote URL. Rather than printing stderr to the journal, keep a
filtered tail (credentials and remote redacted) in a private receipt on failure, and log only the
receipt name. Record the tested rclone version and artifact digest. If the deployment's approved
installation policy permits a separately managed binary, pin that tested artifact and checksum;
otherwise use the approved distribution mechanism and record its version. Do not assume an
existing restic pinning practice or replace the installation policy implicitly.
