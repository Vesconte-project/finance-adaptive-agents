"""Independent model processes use their own CLI login, not the caller's runtime home."""
from __future__ import annotations

import os
from pathlib import Path
from typing import Mapping

from .repository import TeamSkillsError

# These are invocation-local preferences, never consumer/catalog configuration.
SELECTOR_HOMES = {
    "codex": ("CODEX_HOME", "TEAM_SKILLS_CODEX_HOME"),
    "claude": ("CLAUDE_CONFIG_DIR", "TEAM_SKILLS_CLAUDE_CONFIG_DIR"),
    "copilot": ("COPILOT_HOME", "TEAM_SKILLS_COPILOT_HOME"),
}
CALLER_CONTEXT = (
    "CODEX_SESSION_ID", "CODEX_THREAD_ID", "CODEX_INTERNAL_ORIGINATOR_OVERRIDE",
    "CLAUDECODE", "CLAUDE_CODE_ENTRYPOINT", "CLAUDE_PROJECT_DIR",
    "COPILOT_CLI", "COPILOT_AGENT_SESSION_ID", "COPILOT_SESSION_CWD",
    "COPILOT_PROJECT_DIR", "COPILOT_HOOK_DEPTH",
)


def model_environment(provider: str, environ: Mapping[str, str] | None = None) -> dict[str, str]:
    """Keep credentials/network settings; detach only caller homes and session context.

    CLI defaults locate the normal per-user login. Dedicated Team Skills home
    overrides select a custom account explicitly, without inspecting or copying
    credentials and without falling back if that home is unavailable.
    """
    if provider not in SELECTOR_HOMES:
        raise TeamSkillsError("unsupported model process provider")
    environment = dict(os.environ if environ is None else environ)
    for native, _override in SELECTOR_HOMES.values():
        environment.pop(native, None)
    for key in CALLER_CONTEXT:
        environment.pop(key, None)
    native, override = SELECTOR_HOMES[provider]
    if override in environment:
        value = environment[override]
        if not value.strip() or "\x00" in value:
            raise TeamSkillsError(f"{override} must name an absolute CLI home")
        path = Path(value).expanduser()
        if not path.is_absolute():
            raise TeamSkillsError(f"{override} must name an absolute CLI home")
        environment[native] = str(path)
    return environment
