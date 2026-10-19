# Optional Finance design context

These are recorded target-policy discussions of 2026-10-10 and 2026-10-18/19, not
verified deployments or a catalog-wide contract. Reconfirm them with the target owner
before implementation. The originating discussion artifacts are not included here.

The proposed Finance model used Clerk identity, FastAPI authorization and PostgreSQL
projections; personal and organization accounts owned jobs, artifacts and subscriptions.
It proposed admins managing members/billing and contracted capabilities, members using
features and reading organization results, and custom roles without permissions until
mapped. Cancellation was restricted to the still-authorized submitter or an authorized
organization admin. Former paid accounts could retain only non-sensitive basic history;
results/downloads required current entitlement. These choices are optional product policy,
not consequences of using Clerk.

A later platform-admin design separated expiring database-backed grants from runtime
write authority, with a dedicated operator path for issuance, renewals and revocations.
It contemplated temporary operator login activation and session cleanup. This is design
history, **not an executable bootstrap procedure**. No operator prerequisites, root trust
boundary or deployed privileges have been verified by this package. Such operations need
a separately requested and authorized runbook, including credential handling, interrupted
operation reconciliation and rollback/revocation checks.

The same design reported user creation on first authenticated API access and possible
privileges left over from removed features. Treat these as source-specific questions:
verify actual provisioning paths and inherited rights. Do not prohibit SQL provisioning,
require a first client login, or revoke privileges in another workspace from this account.
A grant idempotency key and reconciliation after an uncertain commit remain useful design
considerations when an independently authorized privileged workflow is being designed.
