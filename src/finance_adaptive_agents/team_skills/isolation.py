"""Capabilities disabled for metadata selection, authorship and package assessment."""


def codex_isolation_arguments() -> list[str]:
    # read-only is a write policy, not a tool boundary. Explicit feature switches
    # remove local execution, integrations and alternate filesystem/action routes.
    # Unsupported switches fail the invocation instead of weakening isolation.
    disabled = (
        "shell_tool", "unified_exec", "code_mode_host", "multi_agent", "apps",
        "plugins", "remote_plugin", "hooks", "view_image", "image_generation",
        "browser_use", "computer_use", "skill_search",
    )
    arguments = [item for feature in disabled for item in ("--disable", feature)]
    return [*arguments, "--enable", "skip_host_skill_discovery", "-c", 'web_search="disabled"']
