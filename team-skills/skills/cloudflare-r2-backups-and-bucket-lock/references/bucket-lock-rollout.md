# Bucket Lock rollout, change, and removal

Every rule creation, change, or removal on a bucket holding real data requires the bucket or
account owner's explicit confirmation for that change, recorded with the before/after prefix
listings (see the authorization gate in SKILL.md). The only exception is a probe on a throwaway
prefix where the operator is already authorized to change rules and nothing but probe objects
is stored.

## Before creating a real rule

1. **Prove the semantics you depend on with a disposable prefix** (where you are authorized to
   change rules). Create a short rule over an
   empty throwaway prefix, write a probe object *while the rule is active*, confirm overwrite and
   delete return 409, remove the rule, confirm the delete now succeeds, and confirm absence by
   listing. For age semantics, keep a probe older than the rule duration and check whether it is
   deletable under a newly created rule.
2. **Read every rule back in the dashboard** after creating or removing it — exact prefix
   (including trailing slash) and duration. In one rollout a rule reported as created did not
   exist; every test passed against no rule and produced the right answer for the wrong reason.
3. **Inventory the target prefix completely** and confirm the listing actually succeeded.
   Remove partial uploads, test markers and orphans *before* an indefinite rule; afterwards they
   are permanent.
4. **Choose the duration against the recovery cycle, not by default.** If the rule must outlive
   one full restore-test cycle, compute the worst-case gap between restore tests for *your*
   schedule and add margin (example: "first Sunday of the month" gives gaps of up to 35 days —
   recompute, do not reuse). A retention equal to the gap gives zero overlap between "validated
   by a restore" and "still locked".
5. **State the posture explicitly:** "we can always restore to something recent" (what a rolling
   rule gives) versus "we can restore to any point in the last N months" (which it never gives).

## Validation after activation

- Probe overwrite and delete on a disposable object inside each protected prefix; expect 409.
- The first scheduled backup after activation is the real proof that the rule does not break
  production: verify its object, size, `LastModified`, and checksum read-back.

## Urgent deletion under retention (erasure requests, leaked secret in a dump)

Two paths with different costs:

- **Wait for expiry** — longer retention means a longer wait.
- **Remove the rule, delete, recreate** — only with the owner's recorded confirmation. The
  unprotected window lasts only as long as the operation, but the whole prefix is exposed during
  it. List the prefix immediately before
  removal and immediately after recreation, and compare: only the authorised deletions may
  differ. Without that comparison the window is not just exposed, it is unaudited.

## Recovery tooling

Protected prefixes accumulate loose objects (probes, markers, partial uploads) that can never be
removed, so a listing does not tell you which objects form a complete backup set. Restore
tooling must identify sets from something written with the set — a manifest, or an equivalent
completion record — and ignore objects that no set claims.
