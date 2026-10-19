---
name: codex-mcp-project-scope
description: Configure or troubleshoot Codex CLI MCPs whose visibility or authentication differs by project, shell, or session; distinguish user-wide and project configuration, credential injection, and managed app-server environment.
---

# Codex MCP scope and credentials

Use this Skill when MCPs unexpectedly appear outside a workspace, disappear inside one, or fail authentication even though a shell has the expected credential variable.

## Resolve scope first

Establish the installed client/version, effective `CODEX_HOME` (default `~/.codex`), working directory, and project trust before choosing a file to inspect. The user config normally lives at `$CODEX_HOME/config.toml`; `~/.codex/config.toml` is the default, not a guaranteed active path. Inspect only configuration relevant to the task and authorized scope; do not dump credentials or unrelated personal settings.

Check which layers this installed client supports: invocation overrides and profiles, trusted project `.codex/config.toml` files, user defaults, and any managed/system settings or enforced requirements. Project discovery may include ancestor directories. A project file being present does not establish that it is loaded. The CLI and IDE extension support shared configuration, but may use different processes, invocations or environments. Confirm the effective MCP source rather than assuming two files are the complete configuration.

“Local MCP” is ambiguous: configuration can be local to the client or scoped to a project, while the MCP server itself may be a local process or a remote HTTP service. A Linear HTTP endpoint remains remote even when configured only for one project. Local MCP configuration is not by itself an OAuth connection to the Codex account; credentials still authenticate to the corresponding third-party service.

If the intended scope is one project:
- Keep its entries in an applicable trusted project layer. Remove a user-wide duplicate only after confirming the intended scope, its other consumers, and authorization to change that configuration. A duplicate name does not by itself establish which definition wins.
- Preserve unrelated global MCPs.
- If a project config is generated, edit its source manifest and regenerate it; do not hand-edit the generated file.
- Compare `/mcp` in a session opened inside the project and another opened outside it.

## Trace credential delivery

Keep credential values in a permission-restricted local secret file or secret manager. Use environment-variable references in MCP config; never put token values in the repository, generated config, command output, or a Skill.

A shell wrapper may source the secret file only when the working directory is within the intended workspace. Match a path boundary (workspace root plus slash) so a sibling with a similar name does not match. Delegate to the executable with `command codex "$@"` to avoid recursive function calls. Check the active shell and confirm the wrapper is loaded before assuming that editing `~/.bashrc` affects the current terminal.

First establish which process and execution environment launch the affected MCP: the current CLI, a managed local app-server, or a remote executor. A managed daemon is a diagnostic branch only when it actually serves the session. For the relevant MCP transport, confirm the supported credential fields and injection mechanism; STDIO environment forwarding and HTTP bearer-token lookup need not use the same configuration.

If an already-running process lacks a newly loaded shell credential, changing that shell does not itself change the other process's environment. With authorized access, compare only required variable names and MCP error details. Parse NUL-delimited process environments before extracting names and escape control characters; line-splitting raw environment data can reveal fragments of multiline values. Names in an initial environment still do not prove effective credential consumption.

Restart only if evidence identifies stale credentials in the serving process and existing authorization covers the disruption. Check active work and discover the actual lifecycle command through installed help and the service manager or launcher in use. Do not assume a managed service inherits the restarting shell's environment. If there is no such daemon, investigate the actual client or MCP launch path instead. Never restart automatically on every invocation.

**Historical report, not a reproduction:** the original Linux/WSL account associates Codex CLI 0.157.1 and `codex app-server daemon restart` from a secrets-loaded shell with recovery of missing credentials. The package contains no supporting receipt, so this is a bounded troubleshooting hypothesis, not proof of that version's behavior or a universal remedy. On 2026-10-19, local help from CLI 0.163.0 listed that subcommand; only help was inspected, with no daemon restart or authentication test.

## Verify the result

Check that the intended config layer contains each server once, no unintended global duplicate remains, and no secret value was written to a config file. Open Codex in both target and non-target directories and inspect `/mcp`. Confirm expected servers connect and unrelated global servers remain available.

When new credentials are added or rotated, restart only if the daemon that serves the session has not inherited them. Configuration establishes availability; it does not grant permission to use a connected service for an action.

## Sources

[Configuration basics](https://developers.openai.com/codex/config-basic/),
[state/config locations](https://developers.openai.com/codex/config-advanced/#config-and-state-locations),
and [MCP configuration](https://developers.openai.com/codex/mcp/) were checked on
2026-10-19. Recheck the installed version and target environment before acting;
the documentation does not establish local trust, effective access or credentials.
