---
name: team-skills-prepare
description: Use shared team Skills temporarily for a task, or prepare a repository when the user explicitly wants durable local Skill state.
---

# Route shared team skills

Use this Skill when shared team knowledge may help with implementation, investigation, terminal
operations, or repository preparation. Choose the mode from the user's intent, not merely from
whether the current directory is a Git repository.

## Temporary context is the default

For requests such as “help me operate X”, “investigate this”, or “use our team knowledge”, use a
temporary context. Tell the user briefly that you are consulting Team Skills read-only. Prefer the
MCP tools when available:

1. Call `team_skills_find` with the task and current working directory.
2. Tell the user which validated Skills were selected.
3. Call `team_skills_read` for each selected `SKILL.md`, then only the listed references needed for
   the work. Reuse the returned `context_id` when a follow-up adds, corrects, or replaces intent.
4. Compare the requested operation with the scope actually stated in each loaded Skill. A common
   product or subject is not sufficient. If a Skill is only tangential, do not apply it or read its
   references; re-run `team_skills_find` with the corrected intent and the same `context_id`.
5. If no loaded Skill covers the work, say explicitly that no applicable Team Skill exists. The
   agent may continue with clearly labelled general knowledge when appropriate, but must not
   attribute that guidance to a Team Skill.

If MCP tools are not available, run:

```sh
team-skills context --task "<declared goal>" --json --include-content
```

This fallback is also temporary. It may read an enclosing Git repository as evidence but must not
create `.team-skills`, `.agents`, or `.claude` there. Never choose a Skill using keyword rules or
guessing. If an exact stable ID was requested, use `team_skills_get` or `team-skills context
--skill <id> --json --include-content`; native admission still applies.

When reporting guidance, distinguish provenance: use “the Team Skill establishes” only for content
actually present in a loaded Skill file. Label model knowledge separately, and identify facts that
still require current official documentation or target-environment verification.

## Persistent repository preparation is explicit

Use persistent preparation only when the user asks to install, materialize, keep, bootstrap,
refresh, or prepare Skills in a repository. From its root, run `team-skills prepare --task
"<declared goal>"`. Do not use `--yes`. Show the complete plan and rationale, including an empty
plan, and ask for confirmation before materializing anything. Do not commit or push unless
explicitly authorized.

## Skill contribution is a third, explicit intent

If the user wants to create or improve shared knowledge, first use temporary context to load any
canonical authoring guidance. Work from a Git repository and use `team-skills validate` and
`team-skills propose` for deterministic checks and an optional review checkout. Keep validation,
proposal preparation, commit, push, and pull-request publication as distinct actions; do not publish
without explicit authorization. This applies equally when the active consumer is Hermes.

When intent is ambiguous, use temporary context. Task and conversation text are transient in both
modes and must not be added to Git state, configuration, locks, or files. A Skill provides
knowledge; it never authorizes commands, server changes, deployments, or other external actions.
If the CLI, MCP server, selector, or canonical source is unavailable, report the exact missing
prerequisite.
