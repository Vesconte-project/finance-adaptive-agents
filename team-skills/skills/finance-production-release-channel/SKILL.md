---
name: finance-production-release-channel
description: Use when merging to main, deploying, or diagnosing a deploy of Finance production components (finance-backend, finance-model-registry, finance-data-ops, finance-feature-store, finance-research-orchestrator and its pinned research repositories), or when preparing, applying, or reviewing a host change batch for the Finance production server.
---

# Finance production release channel

Company-specific operating knowledge for the Finance self-hosted production server. An agent
working in one application repository cannot see how its merge reaches production; this Skill
closes that gap. The **source of truth is `Vesconte-project/finance-infra`**
(`docs/PIPELINE_MASTER_PLAN.md`, `docs/AUTOMATIC_DEPLOYMENT.md`, `docs/LOT_REGISTER.json`).
If this Skill and those documents disagree, the documents win and this Skill needs updating.

**State as of 2026-09-25.** This Skill does not authorise a merge, deploy, host change, or
credential change. Company OS governance (work admission, human merge, human Acceptance) still
applies to every change.

## What a merge to `main` does

1. The repository's named CI workflow runs on `main`.
2. Only after CI succeeds, the repository's deploy workflow runs on the self-hosted runner
   (triggered by `workflow_run`, using the exact CI head SHA; a direct push cannot bypass CI).
3. The runner — an isolated identity with no sudo, Docker, service secrets, or PAT — only writes
   an exact-SHA request per component. A root unit validates it and runs the release engine,
   which builds an immutable release, switches `/srv/finance/current/<component>`, checks
   readiness, and writes a receipt; it rolls back on failure.

**A green deploy job means "request accepted", not "running in production."** Read the
per-component result, the receipt, and the `current` symlink. Exit code 75 means *deferred*
(accepted, will retry); 76 means *expired* (a failure).

Components: `backend-api` (finance-backend), `model-registry-api` (finance-model-registry),
`prefect-control-plane`, `data-ops-worker`, `finance-jobs-api` (finance-data-ops),
`feature-store-worker`, `relationship-map-builder` (finance-feature-store), `research-runtime`
(finance-research-orchestrator). `finance-ml-lab`, `finance-strategy-lab` and `finance-backtest`
reach production only through the orchestrator's `runtime-lock.json` and a `research-runtime`
release. `finance-infra` itself is never deployed by the runner.

## Deferral is normal around scheduled work

Activations of the four Prefect-mapped components are deferred while Prefect work is running or
due within the safety margin, retried every few minutes, and expire after six hours. The
control-plane component waits for **both** pools. A merge made in the evening can legitimately
stay deferred for hours; the warning is forecast-relative (Lote 10). Do not "fix" a deferral by
restarting services by hand.

## Changing the host itself: batches

Host changes (units, root scripts, identities, state layout) are **batches** ("lotes"), never ad
hoc commands. Read [references/host-change-batches.md](references/host-change-batches.md) before
preparing, reviewing, or recording one.

## Records to keep current

Work on this server is coordinated in Linear (project *Release pipeline & host hardening*) and
narrated in Notion (*Server & Release Pipeline — September 2026 Record*). Work done without
updating them has already had to be reconstructed once; when a change lands, update the
matching issue in the same session.

## Stop conditions

Stop and report if: CI for the exact SHA did not succeed; the change needs sudo, a credential, or
a dashboard you do not hold; the result file, receipt, and symlink disagree; or the relevant
`finance-infra` document contradicts what you observe.
