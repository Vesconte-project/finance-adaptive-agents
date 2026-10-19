# Optional Finance settlement and capacity fixture

Recorded target discussion of 2026-10-10; not proof of deployment or a verified current
agreement. Use only for maintaining that design after confirming it, or for an explicitly
selected synthetic exercise. Other products must supply their own contract.

The proposal ran two models per comparison and charged one included unit only after both
outputs were valid and durable. Definitive partial failure/cancellation released the unit;
provider compute cost was recorded separately. Successful results remained billable despite
browser-delivery failure.

Local fixtures were 20 comparisons per monthly billing period, 2 concurrent jobs, 250 MB
aggregate output, 5 GB stored per account and 10 distinct effective cancellations per rolling
hour. Reaching the cancellation threshold blocked new submissions, not cancellation or reads.
For example, 4.8 GB stored plus a 250 MB reservation exceeds the selected 5 GB ceiling
(using a consistent unit definition); this is a fixture, not a portable capacity default.

An optional degraded-billing simulation used confirmed failure over 15 minutes to limit
concurrency to one job/account, then blocked new paid jobs after 60 minutes since verified
commercial sync. Accepted work could finish, still within usage/storage and previously
verified unexpired rights. Explicitly select thresholds and use synthetic time; a different
product's actual risk policy may choose different behavior. No outage or stale grant implies
a free upgrade.
