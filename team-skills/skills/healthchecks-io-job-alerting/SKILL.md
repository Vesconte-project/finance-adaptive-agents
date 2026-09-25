---
name: healthchecks-io-job-alerting
description: Use when wiring scheduled jobs, backups, restore tests, or deploy events to Healthchecks.io pings, or diagnosing Healthchecks notifications that were missing, unexpected, or never delivered.
---

# Healthchecks.io job alerting

Behaviour learned wiring backups, restore tests, a source-backup job, and a deploy-event channel
to Healthchecks.io. The ping URL is a credential: store it where only the job's identity can read
it (a root-owned environment file, a secret manager, or a masked CI variable — whichever the
workspace uses; ask before touching root-owned paths), never in a repository, log, ticket, or
chat.

**Evidence scope.** One Healthchecks.io account, 2026-09, five checks. Confirm plan limits and
current API behaviour for your account.

## Two different kinds of check

- **Dead man's switch** — the job pings on success; a missed ping past period plus grace alerts.
  Good for scheduled jobs: a job that never runs is itself the alarm. Send a `/start` ping so the
  grace is measured from the real start, then success or `/fail`.
- **Explicit alarm** — pings arrive only when something happens (a failed deploy, a prolonged
  deferral). Configure its period and grace at the largest values the account allows, so that
  an absence of pings never trips it; with a normal period it goes "down" on its own for lack of
  pings.

## Delivery traps (observed; confirm against current docs)

- **HTTP 200 does not mean the ping was accepted.** A rate-limited ping also returns 200. Require
  the response body `OK`; otherwise keep the event in a local outbox and retry. Deliver outbox
  entries in order, under a lock, and quarantine malformed entries instead of retrying them
  forever. The outbox location, format, and retry cadence are workspace decisions — confirm them
  with the user rather than inventing them.
- **Only state transitions notify.** A success ping on an already-green check produces no
  notification; so does a second failure on an already-red check. If people need to know an
  action *completed*, send a success ping on completion and check the event log, which is
  readable from outside the host.
- Signal completion as well as failure. A channel that only reports failures leaves the operator
  unable to tell "done" from "silently stuck".

## Failure bodies

A `/fail` ping can carry a diagnostic body. Build it from a whitelist of safe fields (component,
revision, state, sanitized error code), cap its size, and never include environment dumps,
connection strings, or raw stderr that could contain secrets.

## Ownership

Every alert needs an owned response path. If all checks deliver to one person, record that as an
explicit single point of failure and decide on a second recipient or channel; a detector whose
signal nobody reads is indistinguishable from no detector.
