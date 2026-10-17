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
- Confirm on the real repository with the same `prune` and the flag set, followed by a full
  `check` with no errors and no remaining locks, before changing the runtime.
- Failed attempts can leave extra index files. The next successful `prune` consolidates them; a
  `check` confirms the repository is consistent.

## Make the next diagnosis cheap

restic errors often contain the remote URL. Rather than printing stderr to the journal, keep a
filtered tail (credentials and remote redacted) in a private receipt on failure, and log only the
receipt name. Pin a recent rclone by checksum instead of the distribution package, the same way
the restic binary is pinned.
