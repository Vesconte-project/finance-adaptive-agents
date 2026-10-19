---
name: lets-encrypt-dns01-octodns-renewal
description: Use when issuing or renewing a Let's Encrypt certificate through getssl DNS-01 hooks backed by an authorized OctoDNS repository.
---

# Let's Encrypt DNS-01 renewal through OctoDNS

Use this only for a certificate whose DNS-01 automation is configured with existing,
owner-maintained `getssl` hooks that apply records through OctoDNS. This Skill explains the
operational boundary; it does not grant DNS, repository, CA-account, or private-key access.

## Decide whether you may proceed

Before running a renewal, establish all of the following without printing secret values:

- You have explicit authorization to renew this certificate and apply its temporary DNS
  challenge records.
- You can access the configured `getssl` checkout and its existing local configuration for
  the requested certificate name.
- You can access the OctoDNS checkout named by that configuration, including the correct
  target zone and its supported environment.
- The DNS-provider credentials required by OctoDNS are already available through the
  approved local secret mechanism, and the OctoDNS environment can run a dry-run.
- The installed DNS hooks use an additional strict plan gate: a validator around OctoDNS's
  dry-run, not a standard getssl/OctoDNS guarantee. Its reviewed contract binds every hook
  call to the exact challenge name, TXT value, zone, provider and intended action, rejects
  unrelated or unparseable changes, and guards the same plan/source before apply. Confirm
  that contract in the installed integration; this Skill does not install or substitute it.

If any condition is missing, stop before invoking `getssl`. Report the missing capability
or authorization to the responsible certificate/DNS operator. Do not request, paste, log,
or store credentials in a repository, terminal transcript, ticket, or Skill.

## Safe DNS-01 sequence

1. Confirm the certificate name, all SANs, the correct authoritative DNS zone, and the
   existing `getssl` configuration. A wildcard name uses DNS-01 but does not itself prove
   ownership of a zone or permission to change it. Before invoking renewal, map the possible
   challenges to TXT names/RRsets and confirm the installed gate supports the required actions,
   including shared names; if not, stop as described below.
2. Run the configured renewal through the existing `getssl` entry point. Let its configured
   DNS add hook create `_acme-challenge` TXT data through OctoDNS; do not hand-edit a zone or
   substitute an unrelated DNS provider while that hook is active.
3. Inspect the OctoDNS dry-run **per hook call and challenge**, not once for the whole
   certificate. For the strict single-value gate described here, require exactly one expected
   TXT RRset creation for setup or exactly one expected deletion for cleanup, with no other
   change. Wrong names/values/zones/providers, extra actions or unparseable plans stop the
   operation. Multiple SANs can require several challenge calls; correlate each separately.
   An apex and its wildcard can share `_acme-challenge` and require multiple TXT values at
   once. Adding/removing one value then appears as an RRset update rather than a create/delete.
   **Stop before renewal if this can occur and the installed gate cannot validate the exact
   multivalue change**, preserving other active values. This procedure does not authorise
   updates or an ad-hoc exception: the integration owner must review, test and obtain any
   needed authorisation for that support first. Do not delete the shared RRset to force a
   create, overwrite another challenge, or weaken the gate.
4. A pre-existing exact TXT value can be a creation no-op only when the installed add hook
   explicitly reports that value already present at the intended name/zone and its gate's
   reviewed contract explicitly accepts the corresponding empty plan. Here “hook” means the
   configured executable invoked by getssl to prepare/remove DNS data; no separate in-house
   mutator is presumed. If this evidence or support is absent, stop. Never extend this
   creation-no-op exception to cleanup or treat an unexplained empty plan as success.
5. Wait for the configured authoritative-DNS verification and let the ACME client complete
   issuance. Issuance is not deployment: do not claim an application, cluster, proxy, or
   service has installed or reloaded the new certificate unless that separate action is
   evidenced.
6. Verify the certificate dates, requested names, and certificate/private-key correspondence.
   Verify cleanup through the integration's plan/state evidence and authoritative DNS queries:
   this challenge's TXT value must be gone after completion, without removing values needed
   by other challenges. Record propagation uncertainty instead of claiming immediate absence.

## Artifact handling

Keep the original full-chain certificate and matching private-key files as the source
artifacts. Send a private key only through the approved secure channel. Do not combine the
private key with certificate text in a convenience file, commit either artifact, or place it
in shared storage without explicit approved protection.

## Source of truth and escalation

The executable behavior belongs to the maintained `getssl` DNS hooks and the authorized
OctoDNS repository, not this Skill. If their configuration, plan format, or guardrail
behavior differs from this procedure, stop and have the integration owner review it before
renewing.

## Primary references

Checked 2026-10-20: [Let's Encrypt DNS-01](https://letsencrypt.org/docs/challenge-types/#dns-01-challenge) describes multiple TXT values at a shared name; [getssl](https://github.com/srvrco/getssl) documents configurable DNS hooks; [OctoDNS dry-run workflow](https://octodns.readthedocs.io/en/latest/getting-started.html) separates plan from apply. The strict gate and creation-no-op contract above remain additional integration prerequisites, not guarantees supplied by these projects.
