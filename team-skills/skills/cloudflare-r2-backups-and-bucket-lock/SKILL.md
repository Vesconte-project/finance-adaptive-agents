---
name: cloudflare-r2-backups-and-bucket-lock
description: Use when uploading backups or other objects to Cloudflare R2 with rclone, diagnosing 403 errors on R2 uploads, or designing, testing, changing, or removing R2 Bucket Lock retention rules.
---

# Cloudflare R2 backups and Bucket Lock

This Skill records R2 behaviour that was established empirically while operating database and
source backups, and that differs from what an S3-experienced engineer would assume. It does not
grant bucket, token, or dashboard access. Cloudflare can change R2; where a rule below decides a
destructive or irreversible action, re-check it against current Cloudflare documentation or a
disposable probe first.

**Evidence scope.** Observed 2026-09-18 → 09-20 on one account with an account API token scoped
to one bucket (Object Read & Write) and `rclone v1.60.1-DEV`. Bucket Lock semantics were
established with disposable probe objects, not by reading documentation.

## rclone uploads that fail with 403

Older rclone, invoked without R2 compatibility flags, first issues `PUT /<bucket>` — an attempt
to **create the bucket** — before uploading. A bucket-scoped token cannot create buckets, so R2
answers `403 AccessDenied`. It looks like a permission problem on the object write and is not:
the same key succeeds with another client. Current rclone with `provider = Cloudflare` may not do
this, so **first confirm the wire call** (`-vv --dump headers`) instead of assuming this bug.

- **The fix is `--s3-no-check-bucket`.** It suppresses the bucket-creation call; the upload then
  becomes a plain `PUT /<bucket>/<key>`.
- The working invocation also carried `--s3-no-head --s3-no-system-metadata
  --s3-disable-checksum --use-server-modtime`. These are **optional** compatibility and speed
  choices, not part of the 403 fix, and they were not proven necessary one by one. They reduce
  client-side checks: `--s3-no-head` skips the post-upload read-back and `--s3-disable-checksum`
  drops the MD5 rclone would store and compare. Add them only for a stated reason, and if you do,
  the independent checksum read-back below becomes the only integrity check — mandatory.
- If uploads go through a wrapper script, put the required flag inside it (`exec rclone ...`)
  and do not let a caller's environment override it. A rule that depends on remembering flags
  will be forgotten, and the next bare invocation will reproduce the misleading 403.
- Verify an upload at the **object**: `LastModified` matching the job's end, size equal to the
  local file, and a companion checksum read back from R2 and compared. Exit status alone is not
  proof — check that the call is not inside a pipeline without `pipefail`, a conditional, or
  followed by `||`, and prove failure propagation with a stub that exits non-zero.

## What R2 does not give you

- **No object versioning.** `GetBucketVersioning` / `PutBucketVersioning` are not implemented. A
  deleted or overwritten object is gone.
- Several S3 configuration reads (`GetBucketPolicy`, `GetPublicAccessBlock`, lifecycle, object
  lock configuration) return `AccessDenied` or are unimplemented through the S3 API. Public
  access, other tokens' scope, and retention rules can only be read in the Cloudflare dashboard.
  Record them as unknown until someone reads the dashboard.

## Bucket Lock: the semantics that matter

- **Prevention, not recovery.** A matching rule refuses overwrite and delete with
  `409 ObjectLockedByBucketPolicy`. It keeps no prior versions; uploads under new names continue;
  reads are unaffected.
- **Evaluated dynamically.** Protection follows the rules configured *now*. Removing a rule
  immediately restores overwrite/delete, including for objects written while it was active. This
  is unlike S3 Object Lock, which stamps a retain-until date on each object at write time.
- **Retroactive.** A new rule protects objects already present under its prefix.
- **Age counts from each object's upload, not from rule creation.** A 42-day rule protects only
  the most recent 42 days of objects — a rolling window, never a floor under history. Older
  objects stay deletable by the host credential, permanently.
- **Indefinite retention captures whatever is already in the prefix**, including test markers
  and partial uploads. The only exit is an administrator removing the rule for the whole prefix.
- The bucket token cannot administer rules, which is the point: Bucket Lock is a boundary
  against the host credential, **not** against the account owner, and not a replacement for a
  second copy under independent credentials.

For a rule rollout, change, or removal, read
[references/bucket-lock-rollout.md](references/bucket-lock-rollout.md).

## Authorization gate

Creating an indefinite rule, extending a duration, removing a rule, and the "remove, delete,
recreate" path each either make data permanently undeletable or expose a whole prefix. Before
any of them, obtain explicit confirmation from the bucket or account owner for that specific
change — holding dashboard access is not approval — and record it next to the before/after
prefix listings. Without it, prepare the change and stop.

## Stop conditions

Stop and report before acting if: the owner has not confirmed an irreversible or
exposure-creating rule change; you cannot read the rule configuration back from the dashboard;
the target prefix has not been listed completely and successfully (a timed-out listing is not an
empty prefix); the data may carry erasure obligations and nobody has decided how an urgent
deletion would work under retention; or the operation needs a credential you do not already
legitimately hold.
