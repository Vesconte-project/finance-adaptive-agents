# Optional Finance policy examples

Recorded as proposed target policy on 2026-10-10, not verified production configuration.
Apply only after the target owner confirms these requirements; other products must select
their own limits, retention and charging contract.

- A local two-model comparison fixture allowed 250 MB combined output and 5 GB stored per
  account. Its policy treated overflow as an unsuccessful comparison with no unit charge
  and cleanup of partial objects. These values and refund semantics are not storage invariants.
- The proposed premium plan, called Pro, retained successful outputs while entitled subject
  to quotas/deletion duties; after effective paid access ended it blocked results/new URLs,
  retained outputs for 90 days, then deleted. Restoration before deletion required fresh
  authorization. The period was a proposal, not a legal requirement or provider guarantee.
- A boundary exercise could compare restoration just before the selected deadline against
  already deleted objects after it. Use a synthetic clock and disposable objects, not a
  real user's retained data. History retention and backup erasure windows need separate policy.
