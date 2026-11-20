"""Real child processes exercise every model entry point under different callers."""
from __future__ import annotations

import json
from importlib.util import find_spec
import os
from pathlib import Path

import pytest

from finance_adaptive_agents.team_skills import selector, skill_quality

# Authorship exists on the 0.23 proposal branch, not yet on main.
HAS_AUTHORING = find_spec("finance_adaptive_agents.team_skills.authoring") is not None
if HAS_AUTHORING:
    from finance_adaptive_agents.team_skills import authoring
from finance_adaptive_agents.team_skills.evidence import RepositorySkillsEvidence
from finance_adaptive_agents.team_skills.process_environment import (
    CALLER_CONTEXT, SELECTOR_HOMES, model_environment,
)
from finance_adaptive_agents.team_skills.repository import TeamSkillsError


HOSTS = {
    'terminal': {},
    'codex': {'CODEX_HOME': '/caller/custom-codex', 'CODEX_SESSION_ID': 'caller'},
    'claude': {'CLAUDE_CONFIG_DIR': '/caller/custom-claude', 'CLAUDECODE': '1'},
    'copilot': {'COPILOT_HOME': '/caller/custom-copilot', 'COPILOT_AGENT_SESSION_ID': 'caller'},
    't3': {'CODEX_HOME': '/caller/shadow', 'CODEX_THREAD_ID': 'caller'},
}


@pytest.mark.parametrize('provider', SELECTOR_HOMES)
@pytest.mark.parametrize('host', HOSTS)
def test_default_cli_identity_does_not_depend_on_caller_and_parent_is_untouched(provider, host):
    parent = {'HOME': '/user', 'PATH': '/bin', 'OPENAI_API_KEY': 'synthetic-key',
              'HTTPS_PROXY': 'synthetic-proxy', **HOSTS[host]}
    before = dict(parent)
    result = model_environment(provider, parent)
    assert parent == before
    assert not set(result) & {native for native, _ in SELECTOR_HOMES.values()}
    assert not set(result) & set(CALLER_CONTEXT)
    assert result['HOME'] == '/user'
    assert result['OPENAI_API_KEY'] == 'synthetic-key'
    assert result['HTTPS_PROXY'] == 'synthetic-proxy'


@pytest.mark.parametrize('provider', SELECTOR_HOMES)
def test_explicit_custom_home_is_preserved_even_when_missing_and_never_falls_back(provider, tmp_path):
    native, override = SELECTOR_HOMES[provider]
    missing = tmp_path/'not-created'
    result = model_environment(provider, {native: '/caller/home', override: str(missing)})
    assert result[native] == str(missing)
    assert not missing.exists()


@pytest.mark.parametrize('provider', SELECTOR_HOMES)
@pytest.mark.parametrize('invalid', ['', ' ', 'relative/home', 'bad\x00path'])
def test_invalid_explicit_home_fails_without_including_value(provider, invalid):
    _, override = SELECTOR_HOMES[provider]
    with pytest.raises(TeamSkillsError, match=override) as error:
        model_environment(provider, {override: invalid})
    assert str(error.value) == f'{override} must name an absolute CLI home'


def test_unknown_provider_is_rejected():
    with pytest.raises(TeamSkillsError):
        model_environment('unknown', {})


@pytest.mark.parametrize('provider', SELECTOR_HOMES)
@pytest.mark.parametrize('host', HOSTS)
@pytest.mark.parametrize('role', ['selection', 'assessment'] + (['authoring'] if HAS_AUTHORING else []))
@pytest.mark.parametrize('custom_home', [False, True])
def test_all_entry_points_launch_detached_processes(provider, host, role, custom_home, tmp_path, monkeypatch):
    for native, override in SELECTOR_HOMES.values():
        monkeypatch.delenv(native, raising=False)
        monkeypatch.delenv(override, raising=False)
    for key in CALLER_CONTEXT:
        monkeypatch.delenv(key, raising=False)
    for key, value in HOSTS[host].items():
        monkeypatch.setenv(key, value)
    expected_environment = {'OPENAI_API_KEY': 'synthetic-only'}
    if custom_home:
        native, override = SELECTOR_HOMES[provider]
        home = str(tmp_path/'explicit-login')
        monkeypatch.setenv(override, home)
        expected_environment[native] = home
    capture = tmp_path/'capture.json'
    monkeypatch.setenv('TEST_CAPTURE', str(capture))
    monkeypatch.setenv('OPENAI_API_KEY', 'synthetic-only')
    if role == 'assessment':
        payload = {'decision': 'ready', 'summary': 'Suitable.', 'required_changes': [],
                   'findings': [], 'in_scope_exercise': 'Review DNS.',
                   'out_of_scope_exercise': 'Tune SQL.'}
    else:
        payload = {'schema_version': 1, 'selected': []}
    executable = tmp_path/provider
    # Capture only known synthetic values; never dump the real process environment.
    executable.write_text(
        '#!/usr/bin/env python3\n'
        'import os, sys, json\nfrom pathlib import Path\n'
        f'keys = {tuple(CALLER_CONTEXT) + tuple(native for native, _ in SELECTOR_HOMES.values()) + ("OPENAI_API_KEY",)!r}\n'
        "Path(os.environ['TEST_CAPTURE']).write_text(json.dumps({k: os.environ[k] for k in keys if k in os.environ}))\n"
        f'payload = {json.dumps(payload)!r}\n'
        "if '--output-last-message' in sys.argv:\n"
        " Path(sys.argv[sys.argv.index('--output-last-message')+1]).write_text(payload)\n"
        + ("else: print(json.dumps({'structured_output': json.loads(payload)}))\n"
           if provider == 'claude' else 'else: print(payload)\n')
    )
    executable.chmod(0o755)
    monkeypatch.setenv('PATH', str(tmp_path)+os.pathsep+os.environ['PATH'])
    before = dict(os.environ)
    if role == 'selection':
        types = {'codex': selector.CodexSkillSelector, 'claude': selector.ClaudeSkillSelector,
                 'copilot': selector.CopilotSkillSelector}
        assert types[provider](str(executable)).select(RepositorySkillsEvidence({}, '0'*64), ()).selected == ()
    elif role == 'authoring':
        assert authoring.invoke_author(provider, {}, {}) == payload
    else:
        monkeypatch.setattr(skill_quality, 'assessment_prompt', lambda candidate: '{}')
        assert getattr(skill_quality, 'assess_with_'+provider)(object(), str(executable)).decision == 'ready'
    assert dict(os.environ) == before
    observed = json.loads(capture.read_text())
    assert observed == expected_environment
