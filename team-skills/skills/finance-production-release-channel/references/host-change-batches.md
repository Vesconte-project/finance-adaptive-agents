# Host change batches ("lotes")

Organization-private. Every fact here is tied to one host's layout as of 2026-09-25; confirm it
against `finance-infra` before acting on it.

## Contract

Every batch is one script in `finance-infra/scripts/` with four modes:

- `stage` — archives the exact commit of `main` into a root-owned tree; refuses a SHA that is not
  the remote tip of `main`.
- `plan` — read-only; performs the full preflight and prints installed, desired, and baseline
  hashes, restarts, expected downtime, and the rollback command.
- `apply` — requires a literal confirmation string, repeats the preflight before its first write,
  and writes a receipt.
- `rollback` — one command back to the recorded baseline.

As designed, agents author and test batches and open PRs, and a human with interactive sudo
merges and runs `stage`/`plan`/`apply`. Confirm this in finance-infra; whatever the current
split, never run a mode that needs privileges you do not demonstrably hold.

## Rules learned the hard way

- **Reserve the number first.** Add the batch to `docs/LOT_REGISTER.json` (validated in CI) before
  opening its PR, and keep its `state` current when it is applied. Two batches were renumbered and
  a third branch reused a taken number within two days.
- **Two batches that install the same file cannot both merge before one is applied.** The first
  one staged will carry the second's content and invalidate the second's baseline. Before
  opening or merging a batch, check `LOT_REGISTER.json` for batches not yet `applied` and the open
  PRs for any that install the same target path.
- **Three-way preflight.** For each installed file: equal to baseline → install; equal to target →
  record a no-op (`APPLIED`, mode `NOOP_ALREADY_INSTALLED`, nothing run); anything else → refuse.
- **Receipts live where the service identities cannot write.** Use a `root:root 0700` directory;
  a directory writable by a service identity lets that identity delete or rename receipts.
- **A failed apply that rolled back must be retryable** with an attempt counter, after validating
  the retained backup against baseline hashes.
- **Keep decision fields separate from file metadata in receipts.** One receipt recorded
  `installation_mode=493` because a loop variable holding the file mode `0o755` overwrote the
  decision. Test receipts for both install and no-op branches.
- **Map credentials by fingerprint before deleting any.** Deleting two deploy keys that looked
  redundant removed the runtime identity's read key; the next deploy failed and the worker could
  not have restarted.
- **A write key granted to a person on a shared key is granted to every service sharing it.** The
  Prefect runtime briefly could push to `main` through a key shared with the human account.

## After applying

Record the batch in the lot register and the master plan's execution log in the same or the next
PR, update the Linear issue if you have access and authorisation (otherwise report what needs
updating), and state what is verified versus reported. A batch is closed only
with its receipt, verification of the final state, and — where the plan says so — one real
observation after apply; synthetic tests alone do not close it.
