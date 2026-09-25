# Shared knowledge for coding agents

Write a reusable Agent Skill once in  team-owned Git catalog, then let each engineering
repository install only the Skills a model judges likely to be relevant. Choose Codex,
Claude, or Copilot for that semantic selection step. The source stays
canonical: `team-skills prepare` distributes central improvements and revocations without
manual copying, choosing the lower-level bootstrap or sync path automatically.

The product has two deliberately separate consumption modes: transient task context for any
terminal directory, and persistent repository preparation with local generated copies. Both use one
explicitly selected model CLI, native admission/validation, and the same Git-backed canonical source.

## Start here

You do not need to clone this repository to consume team skills. A new user needs:

- Python 3.11 or later, Git, and `pipx`;
- access to the canonical Git repository; and
- at least one installed and authenticated selector CLI: Codex, Claude, or Copilot.

Install the CLI once:

```sh
pipx install "git+https://github.com/franciscoabadesantos/adaptive-agents.git@main"
```

Then enter any Git repository where you want to work and use the normal entry point:

```sh
cd <your-git-repository>
team-skills prepare
```

On first use, `prepare` shows the available AI CLIs, asks which one should be the default,
installs the onboarding Skill for supported agents, and then continues with the repository.
It presents recommendations and a complete write boundary before changing local state.

The tool never commits, pushes, merges, deploys, or publishes as part of `prepare`. When a plan
is accepted, the repository receives durable config, lock, and local-ignore files under
`.team-skills/`.
Generated Skills under `.agents/skills/`, Claude discovery bridges, runtime data, and source
replicas remain local and reconstructible.

### Which command should I use?

| Goal | Command |
| --- | --- |
| Use team knowledge temporarily here | `team-skills context --task "<work>"` |
| Open one exact Skill temporarily | `team-skills context --skill <id>` |
| First use or normal repository refresh | `team-skills prepare` |
| Prepare for work not yet visible in the repository | `team-skills prepare --task "<work>"` |
| Change or diagnose the default AI selector | `team-skills setup` |
| See or read available Skills | `team-skills list` / `team-skills show <id>` |
| Review a local Skill without publishing | `team-skills validate [<id>]` |
| Contribute a new or improved Skill | `team-skills propose` |
| Work directly with lifecycle internals | `team-skills bootstrap` / `team-skills sync` |
| Expose temporary contexts to an agent | `team-skills mcp` |
| Evaluate selector routing at catalog scale | `team-skills evaluate-routing` |

`prepare` chooses bootstrap for a new repository and sync for an existing one. Most users do
not need to call those advanced commands directly.

### Temporary terminal and software work

Use `context` when knowledge is needed for the current task but should not become repository state:

```sh
cd /any/directory
team-skills context --task "Install and operate X on a Linux server"
```

Inside Git, bounded factual evidence from tracked and non-ignored untracked paths can help selection. Outside Git, the selector gets
an explicit task-only `terminal` context and no invented repository facts. Both paths run native
admission and validation and write nothing to the working directory: no `.team-skills`, `.agents`,
or `.claude` directories are created.

Task-scoped lookups require the requested operation as well as the product or subject to match a
Skill description. An empty result is preferred to a tangential match. After reading a selected
Skill, the agent checks its stated scope and distinguishes Skill-derived guidance from its own
general knowledge.

Agent integrations should prefer the local stdio MCP server:

```sh
team-skills mcp
```

It exposes `team_skills_find`, `team_skills_get`, and `team_skills_read`. A lookup returns a
process-local `context_id`; follow-ups reuse the same pinned catalog and evidence snapshot, while
Skill bodies and references are read progressively. Without MCP, the portable router uses
`team-skills context --json --include-content` as its fallback.

Any MCP host can launch it with the standard server definition:

```json
{
  "command": "team-skills",
  "args": ["mcp"]
}
```

Hermes can place that definition under `mcp_servers`. Setup also installs the router at
`~/.hermes/skills/team-skills-prepare/SKILL.md`. Hermes may author portable Skills and submit them
through the existing `validate`/`propose` workflow; canonical publication still uses normal Git
review.

There are two independent update paths:

```sh
# Update this CLI application and its behavior.
pipx upgrade adaptive-agents

# Fetch canonical Skill changes and refresh the current repository.
team-skills prepare
```

To develop the application itself from a clone:

```sh
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -e ".[dev]"
team-skills --help
```

## Canonical team catalog

For the first team trial, the canonical catalog lives alongside this product's code in the
`team-skills/` subtree:

```text
team-skills/
  team-skills.json
  skills/
```

The root descriptor identifies the source and its team:

```json
{
  "schema_version": 2,
  "source_id": "adaptive-agents",
  "organization": "",
  "team": "engineering"
}
```

An empty `organization` keeps the canonical source unbound to any GitHub repository owner.
In that case, omit `organization_default_skill_ids`; organization-specific forks may set their
own owner and defaults.

Each Skill uses the standard `name` and `description` frontmatter in `SKILL.md`. Its small
sidecar contains only stable identity and lifecycle:

```json
{
  "schema_version": 1,
  "id": "dns-operations",
  "state": "active"
}
```

Review changes to this repository through normal Git pull requests. Skills must be safe,
UTF-8 text packages: `SKILL.md` plus optional text references. Symlinks, executable files,
`scripts/`, and binary bundles are rejected.

## How repository preparation works

The normal command in an engineering repository is always:

```sh
team-skills prepare
```

On first use, `prepare` detects that machine setup has not been completed, shows which selector
CLIs are available, asks for the default selector, and installs the portable onboarding Skill.
It then bootstraps a new repository or synchronizes an already prepared repository automatically.
The same first-run guard applies when an experienced user starts with `bootstrap`, `sync`,
`validate`, or `propose`; read-only `list` and `show` do not require selector setup.

In an interactive terminal, first-time repository preparation offers to recommend Skills from the
repository as it exists or to start a short conversation about work you intend to add. Conversation turns
reuse the same catalog and factual repository-evidence snapshot. Earlier requests and the
selector's earlier recommendations remain in memory for the duration of that command, so a
clarification can add, correct, or replace intent without rescanning the repository. The
conversation is discarded on exit and is never written to the repository, lock, configuration,
or the persistent local canonical replica.

By default, the tool fetches the `main` branch of `adaptive-agents` and reads only its
`team-skills/` catalog. Product code and team skills share Git hosting for this trial,
but remain separate logical assets with independent source paths, revisions, and lifecycle.

To use a different dedicated canonical Git repository whose catalog is at the repository root,
override the source:

```sh
team-skills prepare --source <git-repository>
```

For a catalog in a subdirectory, provide that path explicitly:

```sh
team-skills prepare \
  --source <git-repository> \
  --catalog-path team-skills
```

An explicit source defaults to the external-root behavior (`.`). The chosen URL, ref, and
catalog path are recorded so later syncs never silently migrate to a different default.

Bootstrap profiles factual repository evidence, gives that evidence and admitted Skill
`id/name/description` metadata to the chosen model selector, and presents a plan. Selectors
are explicit; there is no auto-detection or semantic fallback:

```sh
team-skills prepare --selector claude
TEAM_SKILLS_SELECTOR=copilot team-skills prepare
```

The CLI prints each phase, including when it starts and finishes the isolated AI selection.
Before an interactive approval it repeats the exact local write boundary; approval never commits,
pushes, deploys, or changes application source files.

When more than one validated Skill is recommended during an interactive bootstrap, the CLI first
offers numbered choices. Keep all recommendations or select a subset (for example, only Dify and
not Jira); only that subset is then written to the lock and shown in the final approval form.
`--yes` is explicit automation consent for the complete validated recommendation set.

`team-skills propose` provides one contribution flow for improving an installed Skill or
adding a new one. For a new Skill it detects existing local drafts and unmanaged portable Skill
packages before offering to create a blank draft. A selected candidate must pass package checks
and an isolated semantic assessment before the CLI prepares a branch and worktree from the latest
local canonical baseline
and offers explicit local commit, push, or draft-PR actions.

A canonical source may opt into schema version 2 and declare
`organization_default_skill_ids`. During a normal bootstrap, those active Skill IDs are presented
and enforced as auditable defaults only when the repository's Git remote owner exactly matches the
descriptor's `organization`. They are never cross-organization defaults and are not injected for an
explicit `--task`, which remains a separate semantic request.

An empty `organization` disables these defaults and requires `organization_default_skill_ids`
to be empty.

The command-line flag takes precedence over `TEAM_SKILLS_SELECTOR`; otherwise Codex is
used. The selector is an invocation choice, not repository state, and is not written to the
config or lock. After reviewing the plan, answer `y`
(or use `--yes` in automation). Then commit only the distribution state:

```sh
git add .team-skills/config.json .team-skills/lock.json .team-skills/.gitignore
git commit -m "Bootstrap shared team skills"
```

Declining the bootstrap plan leaves no `.team-skills/` state or generated Skill package in
the consumer repository. Source acquisition may create or refresh the persistent local canonical replica.

To prepare a repository for work it does not yet contain, choose "Tell me what you want to do"
in the interactive preparation form. `--task` provides the same direct, non-conversational path for
scripts and one-line invocations. Task and conversation text are never written to the config,
lock, generated Skill package, or local replica:

```sh
team-skills prepare --task "Implement Jira issue automation for this service"
```

The first interactive `prepare` installs the portable routing Skill at the user-level
locations for Codex, Claude, Copilot, and Hermes. Use the explicit machine command only to inspect or
change that setup later:

```sh
team-skills setup --dry-run
team-skills setup
```

After that, in any repository, a request such as “prepare this repository to implement Jira
automation; ask if a material detail is missing” invokes the local onboarding Skill. It shows a
plan and never applies, commits, or pushes without confirmation.

### New-machine setup

The CLI is the shared foundation: it is independent of Codex, Claude, Copilot, and Hermes. Install Python
3.11+, Git, and the coding agents a person will use, then install the canonical
distribution once:

```sh
pipx install "git+https://github.com/<organization>/<team-knowledge-repository>.git@main"
team-skills prepare
```

The first interactive `prepare` performs machine setup and continues directly into repository
preparation. `setup` remains available to inspect or change that machine configuration. It installs
the same portable onboarding Skill for all four agents and reports whether their
CLIs are currently available on `PATH`; it does not install, authenticate, configure, or silently
substitute any coding agent. A person needs Git access to the private source and must sign in to the
selector they choose. By default it prepares all four consumers, including ones installed later. Use
`team-skills setup --selector claude --only` to limit onboarding to one agent. A Codex
plugin can later package the same conversational onboarding, but it is optional: the CLI
remains the cross-agent installation path.

Set the user-level default semantic selector during setup; it is stored in the person's local
configuration, never in a repository or lock:

```sh
team-skills setup --selector claude
```

For one command only, `--selector` wins; `TEAM_SKILLS_SELECTOR` wins next, then the saved user
preference, with Codex as the final fallback.

Validated Skills are materialized once at `.agents/skills/<name>/`, the vendor-neutral Agent
Skills location used directly by Codex and Copilot. Claude receives a relative directory
symlink at `.claude/skills/<name>` pointing to that same package. Generated packages, Claude
bridges remain local. Bootstrap adds only the exact managed paths to `.git/info/exclude`; it does
not hide other Agent Skills. A normal Git clone of each canonical source is shared across repositories
under persistent user data (normally `~/.local/share/team-skills/sources/` on Linux/WSL), never
inside the pipx installation or a consumer repository. When setup runs inside the default canonical
clone, that checkout is registered and reused. `TEAM_SKILLS_HOME` can place replicas and user
configuration under an explicit root, and `team-skills setup` prints the effective paths.

When the canonical team repository changes, the same entry point refreshes the repository:

```sh
team-skills prepare
git add .team-skills/lock.json
git commit -m "Sync shared team skills"
```

The plan automatically updates already-selected Skills and removes explicitly revoked ones.
New Skills or changed repository evidence trigger a fresh selection using the selector chosen
for that invocation. A previously selected Skill the model no longer selects is reported but
retained for human review. If a locally edited candidate already matches its newly merged
canonical package, sync reconciles the lock without rewriting the local package. Changing only
`--selector` does not itself trigger reassessment.

If the configured selector is unavailable during sync, safe deterministic updates and revocations can still be
applied while semantic additions are deferred. If the Git remote is unavailable, the command automatically
uses the most recently fetched local canonical ref and says that remote freshness was not checked.
`team-skills sync --offline` selects that behavior explicitly. Offline proposal preparation and local
commits are supported; push, pull-request creation, and cloud-dependent model selection still
require connectivity.

`bootstrap` and `sync` remain explicit advanced commands for scripts and diagnostics. `prepare`
selects between them from the presence of the complete committed consumer config and lock.

Unrelated product-code commits do not advance the effective team-skills revision or churn
consumer locks. Commits under `team-skills/` do. See
[Cross-repository team skills](docs/CROSS_REPOSITORY_TEAM_SKILLS.md) for the exact
formats, safety rules, and sync behavior.

## Architecture boundary

The explicitly chosen model owns semantic relevance. The product supplies bounded factual
repository evidence and Skill routing metadata; it contains no keyword fallback or deterministic
semantic selector.
The existing native admission layer independently enforces exposure and final exact-resource
validation before any canonical Skill is materialized.

Deferred architecture options and their measurement gates are recorded in
[Team Skills follow-up decisions](docs/TEAM_SKILLS_FOLLOW_UP.md).

### Maintainer scale evaluation

The checked-in catalog does not need 200 real Skills before selector scale can be measured.
Maintainers can run a read-only evaluation against 200 deterministic routing entries with close
neighbours such as Jira Data Center versus Jira Cloud, Cloudflare DNS versus WAF, and PostgreSQL
versus MySQL:

```sh
# Two-case smoke test: two model calls, no repository writes.
team-skills evaluate-routing --selector codex --max-cases 2

# Complete public fixture and machine-readable report: ten model calls.
team-skills evaluate-routing --selector codex --json
```

The report identifies the selector and tool version and includes precision, recall, F1, exact-match
rate, per-call and aggregate latency, prompt bytes, and an approximate token estimate. `--catalog-size` can add neutral distractors up
to 2,000 entries, and `--repeat` measures stability. This fixture evaluates the routing boundary,
not the quality of a later engineering task or the full package-loading path; those remain separate
measurements. Each run invokes the explicitly selected provider and can therefore consume paid
model capacity.
