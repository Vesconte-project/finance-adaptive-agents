---
name: finance-production-release-channel
description: Organization-private (Vesconte-project). Use when merging to main, deploying, or diagnosing a deploy of a Vesconte-project Finance component to the Finance self-hosted production server (finance-backend, finance-model-registry, finance-data-ops, finance-feature-store, finance-research-orchestrator and its pinned research repositories), or when preparing, applying, or reviewing a host change batch for that server. Not for ordinary feature, test, or docs work in those repositories, and not for same-named repositories outside Vesconte-project.
---

# Finance production release channel

**Organization-private.** Operating knowledge for the Vesconte-project Finance self-hosted
production server; it is of no use anywhere else. An agent working in one application repository
cannot see how its merge reaches production; this Skill closes that gap.

This Skill does not authorise a merge, deploy, host change, or credential change. The
organization's governance rules (Company OS, in `Vesconte-project/company-os` `AGENTS.md`: work
admission, human merge, human Acceptance) apply to every change; if you cannot read them, say so
and do not treat any change as admitted.

## Source of truth and precondition

The source of truth is `Vesconte-project/finance-infra`: `docs/PIPELINE_MASTER_PLAN.md`,
`docs/AUTOMATIC_DEPLOYMENT.md`, and `docs/LOT_REGISTER.json`. If this Skill and those documents
disagree, the documents win and this Skill needs updating.

**If you cannot read those documents from your workspace, treat every path, exit code, timer,
and role below as unverified.** Use the reasoning, do not act on the facts, and say in your
report that they were not confirmed.

## What a merge to `main` does

1. The repository's CI runs on `main`.
2. Only after CI succeeds, a deploy workflow runs on a self-hosted runner, triggered by
   `workflow_run` with the exact CI head SHA, so a direct push cannot bypass CI.
3. The runner only *requests* a release for that SHA. A privileged unit on the host validates
   the request, builds an immutable release, switches the active release, checks readiness,
   writes a receipt, and rolls back on failure.

**A green deploy job means "request accepted", not "running in production."** Reconcile the
per-component result, the receipt, and the active-release pointer before saying a change is
live. A deferred result is accepted work waiting for a window, not a failure.

## Deferral is normal around scheduled work

Components that run scheduled work are activated only when no run is active or due soon. A merge
made before a dense block of scheduled runs can legitimately stay deferred for hours. Do not
"fix" a deferral by restarting services by hand; check the forecast and the result first.

Since the Marco 0 engine (installed 2026-10-30, finance-infra #169–#174) the gate is stricter
and applies to **every** component:

- it refuses to start inside the forbidden windows, with no run active in any pool (nor the
  weekly Atlas service), when work is scheduled within about 45 minutes, or when the attempt
  budget (30 min) would cross the start of a forbidden window;
- a deferred request is retried every few minutes but is installed **only inside the supervised
  window** of the release-windows policy. It expires after 24 h with an alert and is never
  forced. A newer request for the same component supersedes it;
- a merge made shortly before an evening run therefore waits until the next morning. To land
  before a given night, merge after the previous run finishes and early enough for CI plus
  the 45-minute margin before the next one. Read the scheduled runs before choosing the
  moment.

The final outcome of a deferred request (installed later, expired, failed or rolled back)
reaches the release Healthchecks check, not the GitHub run, which stays green once the request
is accepted.

## Capacity admission and retention

Before staging, the engine requires the persistent release/cache filesystem to keep its
reserve plus a per-component staging budget; volatile filesystems such as a tmpfs `/tmp` are
observed but are not subject to the reserve. A missing budget or a changed component contract
refuses with `STAGING_MEASUREMENT_REQUIRED`; capacity refusals say `STAGING_CAPACITY_INSUFFICIENT`.
Budgets live in a root-only operations directory and must be re-measured when a component's
dependency footprint changes materially. Retention keeps the current release, two verified
predecessors and registered recovery references. It runs in `plan` mode (lists candidates,
removes nothing) until a human approves `collect`. Do not delete release directories by hand
outside a reviewed batch that re-validates references at deletion time.

## Closed lists that live in another repository

The release engine's configuration in `finance-infra` holds a **closed list** of the Prefect
deployment names each component publishes (`expected_names`). Adding a deployment to a
component's `prefect.yaml` without adding it there makes activation refuse ("publication is
incomplete"); the automatic rollback then republishes the old deployments but cannot remove the
new one, so it reports "rollback was incomplete" and the component stays on the previous release.
Observed on 2026-10-18 when a weekly-atlas deployment was added to the feature store.

- When a component PR adds or renames a deployment, prepare the matching `finance-infra` change
  in the same piece of work, and merge it **before** the component PR, or the deploy fails.
- After any feature-store or data-ops release, confirm both the release receipt and the Prefect
  state: the deployments carry the new pinned SHA, schedules have the state the current
  operating decision requires (they were on hold in September and are active since the
  resumption), and no unexpected flow runs were created.
- Treat other cross-repository pins the same way: a manifest that fixes a commit or checksum in
  `finance-infra` must change together with the owner repository, and its CI admission only
  passes once the owner commit is on `main`.

## Changing the host itself: batches

Host changes (units, root scripts, identities, state layout) are **batches** ("lotes") with
`stage`/`plan`/`apply`/`rollback` modes, never ad hoc commands. Read
[references/host-change-batches.md](references/host-change-batches.md) before preparing,
reviewing, or recording one.

## Privileges

Do not assume which privileges you or the reader hold. If a step needs sudo, a credential, a
dashboard, or a merge you do not demonstrably have, stop and hand it to whoever holds it, with
the exact command or change prepared.

## Records

Work on this server is coordinated in Linear (project *Release pipeline & host hardening*) and
narrated in Notion (*Server & Release Pipeline — September 2026 Record*). Work done without
updating them has already had to be reconstructed once. Update them only if you have access and
the user has authorised it; otherwise end your report with exactly what needs recording and
where.

## Environment facts (state as of 2026-09-25, updated 2026-10-30 — confirm, do not rely)

Re-check against finance-infra whenever you use one; if any has drifted, fix this section.

- Active release pointer: `/srv/finance/current/<component>`; releases are immutable directories.
- Components: `backend-api` (finance-backend), `model-registry-api` (finance-model-registry),
  `prefect-control-plane`, `data-ops-worker`, `finance-jobs-api` (finance-data-ops),
  `feature-store-worker`, `relationship-map-builder` (finance-feature-store), `research-runtime`
  (finance-research-orchestrator). `finance-ml-lab`, `finance-strategy-lab` and
  `finance-backtest` reach production only through the orchestrator's `runtime-lock.json` and a
  `research-runtime` release. `finance-infra` itself is never deployed by the runner.
- Activation exit codes: `75` deferred (accepted, retried every few minutes), `76` expired
  (a failure). The expiry was six hours until 2026-10-30 and is 24 hours with the Marco 0
  engine; deferred retries install only inside the supervised window.
- Host monitor (since 2026-10-30): disk, stuck runs and worker memory are reported every 15 s
  to three Healthchecks checks, separate from the release check.
- The four Prefect-mapped components are gated on their pool; `prefect-control-plane` waits for
  **both** pools. The pending warning is forecast-relative (Lote 10).
- The runner identity was designed with no sudo, Docker, service secrets, or PAT; host batches
  were applied by a human with interactive sudo.

## Stop conditions

Stop and report if: CI for the exact SHA did not succeed; the change needs sudo, a credential, or
a dashboard you do not hold; the result file, receipt, and active-release pointer disagree; or
the relevant `finance-infra` document contradicts what you observe.
