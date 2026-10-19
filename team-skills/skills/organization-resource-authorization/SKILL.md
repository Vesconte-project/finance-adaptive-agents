---
name: organization-resource-authorization
description: Use when implementing or reviewing tenant-scoped resource authorization that combines membership, mapped roles, ownership and applicable commercial entitlements. Not for login configuration alone or billing without resource-access decisions.
---

# Organization membership is not a paid entitlement

Identify the actual membership source and server-side authorization boundary. Clerk
Organizations and FastAPI are concrete examples when present, not prerequisites. Confirm
the account model, role mapping, entitlement source and membership freshness before changing
policy. A provider's role names do not select billing or data-sharing rules.

## Authority and account model

- Resolve the authenticated issuer/subject to the application's stable principal and tenant.
  Never trust an arbitrary client-supplied active organization or resource account ID.
- Establish whether membership is checked with the authoritative provider (for example
  Clerk), a verified token, a local projection, or a combination. If PostgreSQL projections are used, process webhooks idempotently,
  reconcile drift and define bounded staleness plus urgent revocation/invalidation behavior.
- Personal accounts need not be organizations. An internal `accounts` table with
  `personal`/`organization` and resources scoped by `account_id` is one possible schema,
  not a migration requirement. Preserve an existing equivalent ownership model.
- At every protected action evaluate current membership, mapped permission, resource scope
  and any required commercial grant. Membership and a paid plan are independent inputs;
  neither replaces resource authorization. Quotas constrain usage, not identity.

## Establish the product's policy explicitly

Record who may read shared versus personal results, cancel another user's work, manage
billing or members, and access prior results after entitlement loss. Do not derive these
permissions from `org:admin` or `org:member` labels alone. Unmapped roles must not acquire
permissions accidentally. Check provider-management permissions and application permissions
against their actual configured mapping. In a Clerk implementation, System Permissions are
not included in session claims; for application-side checks verify the configured Custom
Permissions and server SDK behavior rather than assuming a system permission is in a token.
For another provider, establish its actual claim and permission semantics.

Prefer queries scoped by tenant/account **and** resource ID. A guessed opaque ID is no
exception. Recheck reconnects, pagination, export and download issuance. For long-lived SSE
or streams, define how access removal stops further disclosure; checking only at initial
connection leaves a revocation gap. Signing a short-lived URL does not revoke earlier URLs.

Platform/back-office administration is a separate authority. Implementing organization
authorization does not authorize database login activation, privileged grants, session
termination or operator-role migrations. If that work is requested, first establish its
separate scope, approved procedure and actual trust boundary.

The optional [historical Finance policy](references/finance-policy-context.md) records the
source design and administrative concerns. Read it only when maintaining that design or
when the user explicitly chooses it; it is not the default policy for another product.

## Checks before merge

Exercise GET/POST/export/SSE/download routes with a wrong active organization, guessed ID,
role downgrade, removal during a stream, personal-to-organization switching, plan removal
and an old result. Use the target policy's expected decisions rather than assuming all
members can read all organization resources. If freshness or role mapping is unknown,
report the gap instead of claiming access removal is immediate.

Do not change live membership, billing or privileged grants without authorization.

## Sources

- https://clerk.com/docs/guides/organizations/control-access/roles-and-permissions
- https://clerk.com/docs/webhooks/overview

Role documentation rechecked 2026-10-19; verify target configuration and SDK semantics.
