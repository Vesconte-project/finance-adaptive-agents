---
name: private-research-artifact-access
description: Use when implementing authorization, private S3-compatible downloads, storage reservations, retention and deletion for paid research results or artifacts.
---

# Artifact possession must not bypass account authorization

Establish the actual backend, principal/account model, artifact types, feature grants,
charging rules and retention requirements. FastAPI and a plan named Pro are examples,
not prerequisites. Do not infer retention or billing policy from the storage provider.

## Download boundary

1. Before each URL issuance, authenticate and resolve the principal/account; check current
   resource authorization, membership where relevant, feature access, artifact status and
   retention deadline. A valid artifact ID is not authority.
2. Keep protected objects private. Use account/job-scoped opaque keys and a single-object
   `GET` pre-signed URL, with an expiry selected for sensitivity, file size and client retry
   needs. A **60-second TTL** is an illustrative starting point requiring target selection,
   not an automatic requirement. Do not persist signed URLs in records, analytics, public
   caches or logs.
3. Revocation prevents new issuance. An already issued bearer URL may remain usable until
   expiry, and an already started download may finish. For per-request verification, consider
   authenticated streaming/proxying and its cost; design termination of ongoing transfers
   separately if required.
4. Verify the actual S3-compatible provider's credential, signature and expiry semantics.
   AWS behavior is not a guarantee for every provider. URL validity does not prove entitlement.

## Storage and retention

- Where storage quotas apply, reserve capacity transactionally at admission, settle to
  measured bytes and release unused reservations. Reconcile failed-job partial objects and
  orphaned multipart uploads under an authorized cleanup policy.
- Obtain explicit decisions for retention while entitled, retention after downgrade,
  restoration before deletion, and metadata/history retention. No period or tier is implied.
  Exceeding a storage ceiling does not by itself define whether work is billable: apply the
  confirmed charging and settlement policy.
- Any remaining basic history must be reviewed for disclosure: even a job label may contain
  private information. Exclude prompts, findings, private names and signed URLs unless the
  applicable authorization and retention policy permits them.
- Map deletion across objects, metadata, cached renders, multipart uploads and backup recovery
  windows. Record legal/contractual constraints; do not silently translate a product retention
  period into irreversible bucket locks or promise instant erasure from backups.

For the originating Finance design only, optional [policy examples](references/finance-policy-examples.md)
record numerical fixtures and proposed paid retention. Use them only if explicitly selected
or confirmed in that product's requirements.

## Events and checks

Read/list/status/SSE/download endpoints authorize account and resource on each request or
reconnect; long-lived streams need a revocation policy. Never globally broadcast private
keys or account data. Joining an organization does not override a restricted artifact ACL.

Exercise cross-account IDs, former members, entitlement loss, URL re-issuance, existing URL
expiry and a transfer begun before expiry, simultaneous reservations near capacity,
oversized partial output, restoration before deletion and an authorized deletion workflow.
Use local fixtures or an explicitly authorized isolated environment. Unknown public-access,
retention or lifecycle settings remain unknown; stop before changing them without evidence
and authorization.

## Sources

- https://docs.aws.amazon.com/AmazonS3/latest/userguide/using-presigned-url.html
- https://developers.cloudflare.com/r2/api/s3/presigned-urls/

Provider URL semantics rechecked 2026-10-19; deployment behavior still needs verification.
