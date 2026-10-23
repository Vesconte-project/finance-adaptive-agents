# Experience-driven proposals

`team-skills propose --context-file <path>` lets the principal coding agent contribute
verified experience without writing a Skill itself. Ask the user before preparing a
contribution; normal task authorization does not automatically authorize publication.

## Supply evidence

Write a private UTF-8 handoff with the original objective, relevant environment and
versions, constraints, symptoms, attempted approaches and their results, established
causes, the final solution and its rationale, tests/traces, references, limitations
and remaining uncertainty. Include enough original evidence for independent judgment.
Remove secrets and unrelated confidential data before invoking the tool. The chosen
model provider receives these documents; the author has no access to the original
conversation or arbitrary paths mentioned in it.

```sh
team-skills propose --repo /path/to/project \
  --context-file /private/experience.md \
  --context-attachment /private/verification.txt \
  --context-attachment /private/relevant-diff.txt
```

Attachments are repeatable, explicit regular UTF-8 files. Symlinks, binary and empty
inputs are rejected. All input text is passed in full, with a combined limit of
2,000,000 bytes. Serialized author requests (including metadata and a selected baseline)
are limited to 8,000,000 UTF-8 bytes. Exceeding a limit fails explicitly before that
model call; the tool never silently truncates or summarizes evidence. A provider can
have a smaller effective token limit and may reject the request. In that case preserve
the evidence and report the failure; no alternate provider is silently substituted.

## Independent stages

1. Fetch and pin the catalog, apply native admission, and expose only eligible metadata.
2. Start a fresh author using the explicit `--selector`, environment setting, saved
   preference or Codex fallback. Supported providers are Codex, Claude and Copilot.
3. Decide create, update, no change, or request missing evidence. An update target must
   pass exact-resource validation before its complete package is disclosed.
4. Author the complete candidate from the same full handoff and, for an update, the
   exact baseline. After reading it, the author can still conclude no change or ask for
   evidence. Canonical authoring guidance is included when its known ID is admitted.
5. Check generated paths, package shape, identity and native candidate safety. No model
   output executes commands or writes directly into a repository.
6. Assess the candidate in a separate fresh evaluator call, using only that package.
   READY with no required changes permits preparation of a local canonical diff.

The author receives context over stdin in a fresh temporary working directory, with
provider execution/integration capabilities disabled. Codex uses explicit feature
switches in addition to its read-only sandbox; a sandbox write policy alone is not
a tool boundary. Internal tool interfaces may still be advertised by a CLI. The
local canary check verified that its execution route could not read an external
synthetic file; this is scoped evidence, not a claim that every interface was exercised. Every supplied document is included in both author stages.
The principal agent gets a short decision and path; it need not ingest the full
candidate or repeat the handoff in its chat. Model decisions about relevance remain
separate from native eligibility, exposure, integrity and lifecycle checks.

## Local state and source

This mode does not run first-time setup, install repository Skills, or create consumer
config/lock. A prepared consumer uses its existing source; overrides are rejected.
An unprepared repo uses the standard catalog. For another authorized source:

```sh
team-skills propose --context-file /private/experience.md \
  --source <git-url> --catalog-path team-skills --ref main
```

Generated packages and reviews are retained privately under the user-data directory's
`authoring-drafts/` folder, including when the assessment requests revision. The raw
handoff is not copied into application state, a lock or the canonical proposal.
Use the printed candidate/review files as explicit evidence for a revised attempt.
READY proposals use the normal canonical replica's proposal worktree and action menu.
If the catalog changes while authorship runs, preparation stops and preserves the draft.

`--offline` uses the already-fetched Git replica; it does not make a cloud model work
offline. Reports identify offline source freshness. Provider or package errors stop
without preparing a publishable checkout; evidence requests exit with code 2 and
no-change exits with code 0. A review requiring revision also exits with code 2.

## Publication

The safe action remains keeping the proposal local. Commit, push and draft-PR creation
are explicit later choices; merge follows normal human Git review. New Skills become
available to fresh online consumer lookups after publication to their tracked ref.
An already-pinned MCP context does not refresh until a new context is started.
