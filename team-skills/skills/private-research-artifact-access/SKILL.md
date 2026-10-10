---
name: private-research-artifact-access
description: Use when implementing authorization, private S3-compatible downloads, storage reservations, retention and deletion of paid research results or artifacts after downgrade or account cancellation.
---

# Artifact possession must not bypass account authorization

**Scope:** research outputs in private object storage, including signed downloads, retention and data lifecycle. These are proposed target policies (2026-10-10), **not evidence that production buckets or retention jobs are configured**.

## Download boundary

1. FastAPI authenticates the principal, resolves `account_id`, and checks current membership, current feature access, job ownership/account scope, artifact status and retention deadline **before each issuance**.
2. Use private buckets, opaque object keys scoped to account/job, and single-object `GET` pre-signed URLs with **60-second issuance TTL** for ordinary downloads. Do not store signed URLs in persistent records, analytics, browser-visible public caches or logs.
3. No new URL after access is revoked. An **already issued** bearer URL may remain usable until expiry; a transfer started before expiry may finish. Never promise instant revocation of existing links. For high-sensitivity content requiring verification on each request, use an authenticated streaming/proxy design and account for its resource cost.
4. A pre-signed URL's validity is not proof of entitlement; the decision is made during issuance. Verify actual S3-compatible provider semantics and signature limits before promising AWS-specific behavior.

## Storage and retention

- Reserve storage capacity transactionally at job admission alongside usage. On completion, settle to measured bytes and release unused reservations; cleanup of failed jobs must remove partial objects and orphaned multipart uploads.
- **Local test fixture only:** 250 MB combined for both models and 5 GB stored per account. Exceeding the per-job test ceiling means no successful comparison/unit charge; garbage-collect partial objects. Production thresholds are **not** established.
- Proposed paid product retention: keep successful premium outputs while entitlement is active **subject to quotas and deletion requirements**; after loss of Pro, block premium result/URL access and retain for **90 days** after effective paid access ends, then delete. If Pro is restored before deletion, grant access only after reauthorization.
- Basic history may remain independently (safe job label/date/status), but exclude prompts, private names, premium findings and signed object URLs. Define actual history retention/privacy separately.
- Deletion must cover object store, metadata, cached renders, expired multipart uploads and backups according to documented recovery/erasure windows. Enterprise contracts and legal obligations may override product defaults; do not make irreversible bucket retention changes without authorization.

## Events and ownership

Read/list/status/SSE/download endpoints reauthorize `account_id` and resource on each request or reconnect. Never broadcast artifact keys or user-specific data in global events. Joining an organization or possessing a job ID does not override read restrictions or billing entitlement.

## Tests

- User from another account tries artifact ID; former org member; downgrades Pro; URL re-issuance after revocation; old signed URL before/after expiry; started download during TTL; large partial output overflow; two concurrent reservations near account limit; restore Pro on day 89 vs deletion after day 90; GDPR or contractual deletion workflow.
- If bucket public-access, lifecycle settings, actual retention rules or backend authentication cannot be verified, report **unknown** and stop before changing access/retention.

## Sources to re-check

- https://docs.aws.amazon.com/AmazonS3/latest/userguide/using-presigned-url.html
- https://developers.cloudflare.com/r2/api/s3/presigned-urls/
- https://clerk.com/docs/guides/organizations/overview

Vendor and architecture references reviewed 2026-10-10; AWS behavior must not be assumed identical for every S3-compatible provider.
