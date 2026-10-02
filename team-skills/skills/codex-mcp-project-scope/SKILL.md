---
name: codex-mcp-project-scope
description: Configure or troubleshoot Codex CLI MCPs whose visibility or authentication differs by project, shell, or session; distinguish user-wide and project configuration, credential injection, and managed app-server environment.
---

# Codex MCP scope and credentials

Use this Skill when MCPs unexpectedly appear outside a workspace, disappear inside one, or fail authentication even though a shell has the expected credential variable.

## Resolve scope first

Codex user configuration at `~/.codex/config.toml` applies across workspaces. A trusted project's `.codex/config.toml` adds project-scoped settings. The CLI and IDE extension share these configuration layers. Check both before changing anything.

“Local MCP” is ambiguous: configuration can be local to the client or scoped to a project, while the MCP server itself may be a local process or a remote HTTP service. A Linear HTTP endpoint remains remote even when configured only for one project. Local MCP configuration is not by itself an OAuth connection to the Codex account; credentials still authenticate to the corresponding third-party service.

If the intended scope is one project:
- Keep its entries in the trusted project configuration and remove only duplicate entries from user-wide configuration.
- Preserve unrelated global MCPs.
- If a project config is generated, edit its source manifest and regenerate it; do not hand-edit the generated file.
- Compare `/mcp` in a session opened inside the project and another opened outside it.

## Trace credential delivery

Keep credential values in a permission-restricted local secret file or secret manager. Use environment-variable references in MCP config; never put token values in the repository, generated config, command output, or a Skill.

A shell wrapper may source the secret file only when the working directory is within the intended workspace. Match a path boundary (workspace root plus slash) so a sibling with a similar name does not match. Delegate to the executable with `command codex "$@"` to avoid recursive function calls. Check the active shell and confirm the wrapper is loaded before assuming that editing `~/.bashrc` affects the current terminal.

A shell can have a credential that the already-running managed Codex app-server lacks. The daemon retains the environment it started with; loading a secret later into a client shell does not retroactively change that process. Diagnose by comparing the required variable *names* in the shell and daemon environment, never printing values. Also check the actual CLI configuration and MCP error details rather than treating “variable is set in this terminal” as proof the server can read it.

If a restart is needed, first make sure it will not interrupt active Codex work. Load the intended secrets, then use the installed CLI's supported daemon restart command and open a fresh session. In the observed Linux/WSL setup (Codex CLI 0.157.1), `codex app-server daemon restart` from a secrets-loaded shell refreshed the daemon and fixed missing MCP credentials. Recheck the installed CLI help because daemon behavior can change between versions. Do not restart the daemon automatically on every `codex` invocation.

## Verify the result

Check that the intended config layer contains each server once, no unintended global duplicate remains, and no secret value was written to a config file. Open Codex in both target and non-target directories and inspect `/mcp`. Confirm expected servers connect and unrelated global servers remain available.

When new credentials are added or rotated, restart only if the daemon that serves the session has not inherited them. Configuration establishes availability; it does not grant permission to use a connected service for an action.
