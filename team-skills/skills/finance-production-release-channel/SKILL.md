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

## Environment facts (state as of 2026-09-25 — confirm, do not rely)

Re-check against finance-infra whenever you use one; if any has drifted, fix this section.

- Active release pointer: `/srv/finance/current/<component>`; releases are immutable directories.
- Components: `backend-api` (finance-backend), `model-registry-api` (finance-model-registry),
  `prefect-control-plane`, `data-ops-worker`, `finance-jobs-api` (finance-data-ops),
  `feature-store-worker`, `relationship-map-builder` (finance-feature-store), `research-runtime`
  (finance-research-orchestrator). `finance-ml-lab`, `finance-strategy-lab` and
  `finance-backtest` reach production only through the orchestrator's `runtime-lock.json` and a
  `research-runtime` release. `finance-infra` itself is never deployed by the runner.
- Activation exit codes: `75` deferred (accepted, retried every few minutes), `76` expired after
  six hours (a failure).
- The four Prefect-mapped components are gated on their pool; `prefect-control-plane` waits for
  **both** pools. The pending warning is forecast-relative (Lote 10).
- The runner identity was designed with no sudo, Docker, service secrets, or PAT; host batches
  were applied by a human with interactive sudo.

## Stop conditions

Stop and report if: CI for the exact SHA did not succeed; the change needs sudo, a credential, or
a dashboard you do not hold; the result file, receipt, and active-release pointer disagree; or
the relevant `finance-infra` document contradicts what you observe.
