---
name: organization-resource-authorization
description: Use when implementing Clerk Organization membership, roles and tenant-scoped FastAPI authorization for jobs, results, billing and resources; distinguish account entitlements from membership or ownership.
---

# Organization membership is not a paid entitlement

**Scope:** personal and organizational accounts with Clerk identity, FastAPI resource authorization and optional Stripe billing. These are **target product policies** from architecture discussion on 2026-10-10, not a statement that any repo has deployed them.

## Authority and account model

- Clerk Organizations owns invitations, organizational membership and platform roles. Maintain a minimal local, indexed projection in PostgreSQL for performant joins and policy evaluation; consume webhooks idempotently and reconcile drift.
- Internal `users` map `(clerk_issuer, clerk_subject)` to a stable internal ID. Internal `accounts` may be `personal` or `organization`; subscriptions, quotas, jobs and artifacts belong to an `account_id`. Do not create a Clerk Organization for every B2C personal account.
- FastAPI validates current membership/role and evaluates every action against account, resource owner, feature grant and quota. For urgent access removals, design a fresh-check/invalidation path; webhook projection lag must not yield indefinite access.

## Default role policy

- `org:admin`: may manage members and billing, and may use contracted capabilities.
- `org:member`: may use contracted features and read authorized organization results, subject to quotas/resource policy; cannot administer billing by default.
- Any custom role starts **without** product permissions until explicitly mapped in the application's policy.
- Neither role grants Pro: account-level commercial entitlement does. A user may be admin in an unpaid organization.

## Research job policy

- Organizational jobs belong to the organization. Members with `research:read` may read its authorized jobs/results and artifacts; personal jobs stay private to their account. A job's submitting user is retained for audit.
- Job cancellation: the submitter (while still authorized in the account) **or** a currently authorized `org:admin` may request it. Mere `research:read` is not cancellation authority.
- A removed member must no longer receive new job events, artifact URLs or other account data. Treat reconnects and pagination as new resource authorization checks.
- No cross-account access even with a valid opaque job/artifact ID. For sensitive jobs, a separately designed private/team-sharing ACL may narrow reading beyond basic organization membership; do not promise it exists without code evidence.
- Former Pro accounts can see only a **safe basic history** (non-sensitive name/date/status) when otherwise authorized; results and downloads remain subject to current entitlement and retention policy.

## Checks before merge

Test roles and memberships against all GET/POST/export/SSE/download routes, not just frontend menus. Include wrong active organization, guessed ID, admin downgrades, member removal during active SSE, accounts switching personal->org, Stripe plan removal and access to an old result. Prefer query scoping by `account_id` plus resource ID to prevent data leakage.

If current Clerk/webhook semantics or the deployed role mapping are unknown, inspect docs and code before asserting the above is implemented. Do not change live organization membership or billing without authorization.

## Sources to re-check

- https://clerk.com/docs/guides/organizations/overview
- https://clerk.com/docs/guides/organizations/roles-and-permissions
- https://clerk.com/docs/webhooks/overview

Provider references last reviewed 2026-10-10.
