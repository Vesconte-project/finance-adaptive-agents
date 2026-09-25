# Cross-repository team skills

This vertical proves one property: a team can author a portable Agent Skill once, select it
for multiple relevant repositories with Codex, Claude, or Copilot, and keep every managed
copy current from one Git source.

It also supports a separate transient mode for terminal or software operations. That mode works
inside or outside Git, never materializes Skills in the working directory, and can serve Codex,
Claude, Copilot, Hermes, or another MCP-compatible consumer.

## Reader's map

The everyday consumer lifecycle is:

```text
install CLI once
      ↓
team-skills prepare in a Git repository
      ↓
choose or use the saved AI selector
      ↓
review recommendations and local write boundary
      ↓
confirm local materialization
      ↓
commit only .team-skills config, lock, and local-ignore state
      ↓
run team-skills prepare again when repository work or canonical Skills change
```

The transient lifecycle is:

```text
open an agent in any directory
      ↓
router chooses temporary context by default
      ↓
MCP or CLI sends task plus optional read-only repository evidence
      ↓
model selects only from natively admitted metadata
      ↓
native validation accepts or rejects the IDs
      ↓
agent progressively reads the selected Skill files
      ↓
context disappears with the process; working-directory writes remain zero
```

The contribution lifecycle is separate:

```text
edit an installed Skill or create a local Skill package
      ↓
team-skills validate
      ↓
team-skills propose
      ↓
review the isolated assessment and diff
      ↓
optionally commit, push, and open a draft pull request
      ↓
merge through the canonical repository's normal Git review
      ↓
consumer repositories receive it on their next prepare/sync
```

`prepare` is the normal user command. `setup` changes machine-level onboarding and the default
selector. `list`, `show`, `validate`, and `propose` inspect or contribute Skills. `bootstrap` and
`sync` expose the lower-level repository lifecycle for automation and diagnostics.

`context` is the normal non-persistent command and `mcp` serves the same API over stdio. Intent,
not the presence of `.git`, chooses between `context` and `prepare`; ambiguous requests default to
temporary context.

Application upgrades and catalog refreshes are deliberately different. Use
`pipx upgrade adaptive-agents` to update the CLI application. Use
`team-skills prepare` to fetch canonical knowledge and update the current consumer repository.

## Default source and source contract

The normal team-trial command is:

```sh
team-skills prepare
```

For an unprepared repository, it uses the `adaptive-agents` Git repository at ref `main`,
with catalog path `team-skills`. Product code and team skills share a repository for the
trial but remain separate logical assets: the effective knowledge revision is the latest commit
that changed the catalog subtree, not necessarily the product repository's HEAD.

`team-skills prepare --source <git-repository>` is the normal override for a dedicated
source before repository preparation. The advanced
`team-skills bootstrap --source <git-repository>` form exposes the same initialization step.
They read the dedicated canonical Git source and its catalog from `.` by default. Use
`--catalog-path <relative-path>` when the catalog is below the source root. Config and lock
provenance persist the chosen URL, ref, and catalog path; sync always uses those recorded
coordinates.

The canonical repository has a root `team-skills.json` with `schema_version`, `source_id`,
`organization`, and `team`. Schema version 2 may additionally contain
`organization_default_skill_ids`: active Skill IDs sent to the selected model and added as
auditable organization-default recommendations before native validation during a normal bootstrap
of a repository whose Git remote owner exactly matches `organization`. They are not injected for
other owners or for explicit task-scoped bootstrap. An empty `organization` means the source is
not bound to an owner and cannot declare organization defaults. Each
`skills/<directory>/team-skills.json` has exactly `schema_version`, a stable `id`, and
`state` (`active` or `revoked`). Semantic routing comes only from the standard Agent Skill
`name` and `description` in `SKILL.md`.

The complete materializable package consists of `SKILL.md` and optional UTF-8 files below
`references/` with `.md`, `.txt`, `.json`, `.yaml`, or `.yml` suffixes. The sidecar governs
the package but is not materialized. A deterministic SHA-256 covers every materialized path
and byte; the resource revision is the latest Git commit touching its Skill directory.
For cross-agent portability, the Skill directory must exactly match its standard lowercase
hyphenated `name`; names are limited to 64 characters and descriptions to 1,024 characters.
This narrow canonical subset accepts only `name` and `description` frontmatter; vendor-specific
controls are rejected.

This slice rejects symlinks, executable files, `scripts/`, unsupported files, non-UTF-8 data,
files over 1 MB, Skill packages over 4 MB, and source archives over 20 MB.

## Transient context boundary

`team-skills context --task <text>` accepts any existing working directory. If Git encloses that
directory, it collects the same bounded Git-visible factual evidence used by repository preparation; otherwise
it emits an explicit task-only `terminal` evidence object and does not scan local files. It pins and
validates the canonical snapshot, admits the native resource catalog, exposes only admitted
`id/name/description` metadata to the configured selector, and validates the returned IDs against
the exact exposure receipt. `--skill <id>` skips semantic selection but not native admission or
validation.

Repository-only selection without a declared task favors useful recall. Task-scoped selection
instead favors precision: both the requested subject and operation must match the Skill description,
and an empty selection is preferable to a tangential product-name match. Conversation follow-ups
may therefore remove an earlier recommendation when the user narrows or corrects intent. This is
model-owned semantic behavior; native validation still owns eligibility, exposure integrity, and
final ID validation rather than interpreting task prose.

The response is process-local and records no lock. The working directory receives no
`.team-skills`, `.agents`, `.claude`, generated package, bridge, event, or task text. Source refresh
may update the normal user-level canonical replica, which is application storage rather than
working-directory state.

`team-skills mcp` serves this same core over stdio with three tools: `team_skills_find` selects
metadata, `team_skills_read` progressively reads a selected `SKILL.md` or reference, and
`team_skills_get` opens an exact stable ID. A server process keeps at most 32 transient sessions;
reusing `context_id` sends follow-up intent with the prior conversation while preserving the same
catalog and evidence snapshot. Exiting the process discards all sessions.

The portable onboarding Skill is an intent router. It announces a read-only lookup, prefers MCP,
names the selected Skills, and falls back to `context --json --include-content` when MCP is absent.
After loading a Skill, it checks that the requested operation is within the Skill's stated scope.
Tangential Skills are not applied or attributed, and general model guidance must be labelled
separately from loaded Team Skill guidance.
Only explicit requests to install, materialize, keep, bootstrap, refresh, or prepare repository
knowledge enter the persistent path. Skills inform work but never authorize system operations.

## Bootstrap boundary

`team-skills prepare` is the normal persistent repository entry point. It requires either both consumer
state files or neither: without them it performs bootstrap; with them it performs sync against
the locked source. On first interactive use it completes machine onboarding and saves the chosen
default selector. A transient `--task` also forces semantic assessment during the sync path, so a
prepared repository can select knowledge for intended work that is not yet visible in its files.
Source overrides are accepted only before the repository is bootstrapped.

The advanced bootstrap form accepts source, catalog path, ref, selector, and transient task
overrides:

```sh
team-skills bootstrap [--source <git-repository>] [--catalog-path <relative-path>] \
  [--ref <ref>] [--selector <name>] [--task <text>]
```

1. creates or refreshes the persistent local canonical replica and pins a commit;
2. reads and validates an immutable Git archive;
3. projects only factual evidence from the existing repository profiler;
4. maps canonical packages to native `AGENT_SKILL` resources with organization/team scope;
5. calls native `admit()` and gives the selected model CLI only admitted
   `id/name/description` metadata plus
   the factual evidence;
6. records the exact exposure receipt and passes selected IDs through native `validate()`;
7. plans only validated packages for `.agents/skills/<name>/` plus a Claude bridge at
   `.claude/skills/<name>`; and
8. applies the complete plan transactionally after collision and local-modification checks.

Without `--task` or `--yes`, an interactive terminal first offers repository-only recommendation
or a conversational task description. The conversational path builds the catalog, admission
snapshot, and factual repository evidence once. Each continuation uses that same evidence and
includes the earlier user messages and complete earlier model selections, allowing the latest
message to add, correct, or replace intent. Conversation state is process memory only and is
discarded before exit; it is never written to consumer state, the local replica, or the canonical
source. Non-interactive invocations retain repository-only behavior unless `--task` is supplied.

The selector is resolved in this order: explicit `--selector`,
`TEAM_SKILLS_SELECTOR`, saved user preference, then `codex`. There is no automatic provider detection,
cross-provider reconciliation, or deterministic semantic fallback. Selection reasons are
shown in the plan but are deliberately absent from the lock, as is selector identity.

All three providers receive the same semantic instruction and the same factual evidence plus
admitted routing metadata. Each model turn uses a fresh temporary working directory; follow-up
turns replay the bounded in-process conversation against the unchanged evidence snapshot rather
than relying on provider-specific persisted sessions. Codex
uses ephemeral read-only structured execution; Claude uses safe mode with tools, Skills,
custom instructions, sessions, and MCP disabled; Copilot uses programmatic silent mode with
custom instructions, built-in MCP, experimental features, and available tools disabled.
Malformed Copilot text gets at most one serialization-only retry. Provider unavailability is
reported; one provider is never silently substituted for another.

`--task` is optional, transient semantic context for a declared future implementation task and
bypasses the interactive intent menu. It is sent only to the selected model alongside the same
factual evidence and routing metadata. It is not deterministic matching input and is never
recorded in the consumer config or lock. This lets a repository prepare for a capability it does
not yet demonstrate without making a task description part of durable repository state.

`team-skills prepare` is the normal entry point. On first interactive use it asks for the
default selector and performs machine setup, then bootstraps a new repository or synchronizes an
existing one. `team-skills setup` remains the explicit machine-only command. It installs a single portable
`team-skills-prepare` Skill in the standard user-level Skill directory of Codex, Claude, Copilot,
and Hermes, reports whether their CLIs are available on `PATH`, and refuses to overwrite a different
existing Skill. `--dry-run` diagnoses without writing. `--only` limits onboarding to the agent named
by `--selector`. The CLI does not install or authenticate a coding agent and never silently
substitutes one for another.

The first-run guard is shared by `prepare`, `bootstrap`, `sync`, `validate`, and `propose`, so
starting with an advanced command cannot silently fall back to an unchosen provider. `list` and
`show` remain available without setup because they perform no model selection.

Install the CLI itself once from the approved Git distribution using
`pipx install "git+https://github.com/<organization>/adaptive-agents.git@main"`, then
run `team-skills prepare`. The installed Skill turns a natural-language request into task-scoped
preparation, asks only material clarification questions, and always previews before application. A
Codex plugin may package this conversational entry point as an optional user interface, but the CLI
remains the vendor-neutral installation path.

`team-skills setup --selector <codex|claude|copilot>` saves the person's default semantic selector
in a user-local configuration file, never in repository state. Resolution order is explicit
`--selector`, `TEAM_SKILLS_SELECTOR`, saved user preference, then Codex. This is a local invocation
choice only and is not written to a consumer config or lock.

## Committed and local state

Commit:

- `.team-skills/config.json`: repository identity and canonical Git URL/ref/catalog path;
- `.team-skills/lock.json`: pinned source and selection identities, Git revisions,
  full-package digests, materialized paths, and factual-evidence digest;
- `.team-skills/.gitignore`: exact local state categories.

Keep local:

- `.team-skills/runtime/`;
- `.team-skills/events.jsonl`;
- generated `.agents/skills/<managed-name>/` packages and
  `.claude/skills/<managed-name>` bridges.

The normal Git replica is shared by every consumer of the same canonical source under persistent
user data. On Linux and WSL this is normally
`$XDG_DATA_HOME/team-skills/sources/` or `~/.local/share/team-skills/sources/`. Native Windows
uses `%LOCALAPPDATA%/team-skills/data/sources/`. `TEAM_SKILLS_HOME` may define one explicit
application root, with replicas below its `data/` directory. If setup runs inside the default
canonical clone, that checkout is registered instead of creating a duplicate. The hashed source
directory does not expose its URL, and source URLs containing embedded HTTP credentials are rejected.

The local replica is the durable offline source while `lock.json` continues to pin consumer state
and package digests. Online operations fetch into it first; snapshots and materialization are then
read locally. Offline operations resolve the last successfully fetched ref. Concurrent processes
serialize clone and fetch operations per source. The previous shared bare cache is migrated into
the persistent replica when its provenance is valid.

Version 0.16 and later no longer create `.team-skills/cache/`. When an exact cache created by an
older version is found after the persistent replica is ready, an interactive command offers to remove it
and its obsolete exact `/cache/` ignore rule. Unknown content is never offered for deletion, and
`--yes` deliberately does not authorize legacy cache cleanup.

The installer writes exact managed paths inside a marked block in `.git/info/exclude`. It
never ignores either Skills directory globally and never overwrites an unmanaged physical
package, file, directory, or incorrect bridge. The Claude entry is a relative directory
symlink to the single physical package; no copied fallback is created.

## Sync rules

`team-skills sync` first fetches into the local replica and validates a complete new plan,
then applies it as one filesystem transaction. Central content/reference changes to a selected
Skill update its managed copy and lock. Explicit revocation removes it. Missing locked content without a
revocation is a source-integrity error. New Skills, routing metadata changes, pending model
work, or factual repository evidence changes rerun the explicitly chosen selector. Generated
physical packages and Claude bridges are excluded from factual evidence so their creation or
recovery cannot itself trigger semantic reassessment. Changing only the selector choice also
does not trigger reassessment.

Model nonselection never silently removes an installed Skill; it is reported as possibly no
longer relevant. A locally modified managed copy is never overwritten or removed. If that copy
already matches a newly merged canonical package byte-for-byte, sync records a reconciliation
and updates only its locked provenance instead of rewriting the package. Network
failure falls back to the last local canonical ref and never claims that the remote source is current.
Offline mode can apply already-published updates and revocations present in that replica, restore
managed copies, and prepare local proposal commits without contacting the remote.

## Current limits

This is one Git source, one team scope, and one vendor-neutral Agent Skills target. Codex,
Claude, and Copilot are selector choices; Hermes is currently a consumer rather than a selector.
The bundled catalog is not wheel package data; Git remains its canonical update and revision
mechanism. The product does not publish Skills, merge repository instructions, execute Skill
bundles, authenticate users, rank knowledge, host remote MCP, or manage organization-wide policy. Hosted distribution and additional
materialization formats are intentionally out of scope.
