"""Execute security-sensitive examples from the distributed text packages."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys

import pytest


SKILLS = Path(__file__).resolve().parents[1] / "team-skills" / "skills"
ENVIRONMENT_EXAMPLES = (
    SKILLS / "verify-against-the-host/references/probes.md",
    SKILLS / "effective-config-tracing/SKILL.md",
)
GIT_EXAMPLES = (
    SKILLS / "verify-against-the-host/SKILL.md",
    SKILLS / "verify-against-the-host/references/probes.md",
)


def environment_program(path: Path) -> str:
    match = re.search(
        r"python3 - \"\$pid\" <<'PY'\n(.*?)\nPY",
        path.read_text(encoding="utf-8"),
        re.DOTALL,
    )
    assert match is not None, f"No environment probe in {path}"
    return match.group(1)


def reviewed_file_program(path: Path) -> str:
    blocks = re.findall(r"```bash\n(.*?)\n```", path.read_text(encoding="utf-8"), re.DOTALL)
    return next(block for block in blocks if 'cat-file -e "$REVIEWED_SHA:$UNIT_FILE"' in block)


@pytest.mark.skipif(not Path("/proc/self/environ").is_file(), reason="Linux procfs example")
@pytest.mark.parametrize("path", ENVIRONMENT_EXAMPLES, ids=lambda path: path.parent.name)
def test_environment_probe_emits_encoded_names_without_values(path: Path):
    synthetic = {
        "ORDINARY_NAME": "FAKE_PRIVATE_VALUE_1\nFAKE_PRIVATE_VALUE_2",
        "NAME\nWITH_CONTROL\tCHARACTERS": "FAKE_PRIVATE_VALUE_3",
        "UNICODE_Á": "FAKE_PRIVATE_VALUE_4=value",
        "EMPTY_VALUE": "",
    }
    child = subprocess.Popen(
        [sys.executable, "-c", "import sys; print('ready', flush=True); sys.stdin.buffer.read(1)"],
        env=synthetic,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        text=True,
    )
    try:
        assert child.stdout is not None
        assert child.stdout.readline().strip() == "ready"
        result = subprocess.run(
            [sys.executable, "-", str(child.pid)],
            input=environment_program(path),
            capture_output=True,
            text=True,
            timeout=10,
        )
        assert result.returncode == 0, result.stderr
        names = [json.loads(line) for line in result.stdout.splitlines()]
        assert set(synthetic) <= set(names) <= set(synthetic) | {"LC_CTYPE"}
        assert len(names) == len(set(names))
        assert "FAKE_PRIVATE_VALUE" not in result.stdout + result.stderr
        assert "\\nWITH_CONTROL\\t" in result.stdout
    finally:
        assert child.stdin is not None
        child.stdin.close()
        child.wait(timeout=10)
        child.stdout.close()


@pytest.mark.parametrize("path", ENVIRONMENT_EXAMPLES, ids=lambda path: path.parent.name)
@pytest.mark.parametrize("pid", ["0", "-1", "../self", "not-a-pid"])
def test_environment_probe_rejects_invalid_pid_without_output(path: Path, pid: str):
    result = subprocess.run(
        [sys.executable, "-", pid],
        input=environment_program(path),
        capture_output=True,
        text=True,
        timeout=10,
    )
    assert result.returncode != 0
    assert result.stdout == ""


@pytest.fixture
def reviewed_file(tmp_path: Path):
    repo = tmp_path / "repository with spaces"
    repo.mkdir()
    environment = dict(os.environ, GIT_CONFIG_NOSYSTEM="1", GIT_CONFIG_GLOBAL=os.devnull)

    def git(*args: str) -> str:
        return subprocess.run(
            ["git", "-C", str(repo), *args],
            check=True,
            capture_output=True,
            text=True,
            env=environment,
        ).stdout.strip()

    git("init", "-q")
    content = b"[Service]\n# Exact bytes, including trailing newlines.\n\n"
    unit = "unit file.service"
    (repo / unit).write_bytes(content)
    git("add", unit)
    git("-c", "user.name=Skill example test", "-c", "user.email=skill@example.invalid", "commit", "-qm", "Fixture")
    installed = tmp_path / "installed unit.service"
    installed.write_bytes(content)
    environment.update(
        REPO=str(repo),
        REVIEWED_SHA=git("rev-parse", "HEAD"),
        UNIT_FILE=unit,
        INSTALLED_UNIT_FILE=str(installed),
    )
    return environment, content


@pytest.mark.parametrize("path", GIT_EXAMPLES, ids=lambda path: str(path.relative_to(SKILLS)))
def test_reviewed_file_probe_hashes_exact_bytes(path: Path, reviewed_file):
    environment, content = reviewed_file
    result = subprocess.run(
        ["bash", "-c", reviewed_file_program(path)],
        env=environment,
        capture_output=True,
        text=True,
        timeout=10,
    )
    assert result.returncode == 0, result.stderr
    digest = hashlib.sha256(content).hexdigest()
    assert [line.split()[0] for line in result.stdout.splitlines()[:2]] == [digest, digest]


@pytest.mark.parametrize("path", GIT_EXAMPLES, ids=lambda path: str(path.relative_to(SKILLS)))
@pytest.mark.parametrize("missing", ["revision", "file"])
def test_reviewed_file_probe_rejects_unavailable_content(path: Path, reviewed_file, missing: str):
    environment, _ = reviewed_file
    if missing == "revision":
        environment["REVIEWED_SHA"] = "0" * 40
    else:
        environment["UNIT_FILE"] = "absent.service"
    result = subprocess.run(
        ["bash", "-c", reviewed_file_program(path)],
        env=environment,
        capture_output=True,
        text=True,
        timeout=10,
    )
    assert result.returncode != 0
    assert result.stdout == ""


def symlink_program() -> str:
    text = (SKILLS / "verify-against-the-host/references/probes.md").read_text()
    match = re.search(r"python3 - \"\$RELEASE\" <<'PY'\n(.*?)\nPY", text, re.DOTALL)
    assert match is not None
    return match.group(1)


def run_symlink_probe(release: Path):
    result = subprocess.run(
        [sys.executable, "-", str(release)],
        input=symlink_program(),
        capture_output=True,
        text=True,
        timeout=10,
    )
    records = [json.loads(line) for line in result.stdout.splitlines()]
    return result, records


def test_symlink_probe_preserves_names_and_does_not_walk_symlink_directories(tmp_path: Path):
    release = tmp_path / "release with spaces"
    release.mkdir()
    external = tmp_path / "external"
    external.mkdir()
    target = external / "artifact"
    target.write_text("synthetic fixture")
    (external / "not-in-inventory").symlink_to(target)
    names = ["link with spaces", "link\\name", "line\nbreak", "tab\tname", "unicode-Á"]
    for name in names:
        (release / name).symlink_to(target)
    (release / "directory link").symlink_to(external, target_is_directory=True)
    nested = release / "nested"
    nested.mkdir()
    (nested / "child link").symlink_to(target)
    result, records = run_symlink_probe(release)
    assert result.returncode == 0, result.stderr
    assert result.stderr == ""
    entries = records[:-1]
    assert {x["path"] for x in entries} == set(names) | {"directory link", "nested/child link"}
    assert all(x["status"] == "resolved" for x in entries)
    assert records[-1] == {"symlinks": 7, "failures": 0}
    assert all(x["target"] in {str(target), str(external)} for x in entries)
    assert "\\nbreak" in result.stdout and "\\tname" in result.stdout


@pytest.mark.parametrize("case", ["missing", "loop"])
def test_symlink_probe_does_not_claim_broken_on_resolution_error(tmp_path: Path, case: str):
    release = tmp_path / "release"
    release.mkdir()
    link = release / "unresolved"
    link.symlink_to(link if case == "loop" else tmp_path / "absent")
    result, records = run_symlink_probe(release)
    assert result.returncode != 0
    assert records[0]["path"] == "unresolved"
    assert records[0]["status"] == "inconclusive"
    assert "target" not in records[0]
    assert records[-1] == {"symlinks": 1, "failures": 1}
    assert "QUEBRADO" not in result.stdout


@pytest.mark.skipif(os.name != "posix" or os.geteuid() == 0, reason="Non-root POSIX permission check")
@pytest.mark.parametrize("case", ["target", "directory"])
def test_symlink_probe_preserves_access_failure(tmp_path: Path, case: str):
    release = tmp_path / "release"
    release.mkdir()
    protected = (tmp_path if case == "target" else release) / "protected"
    protected.mkdir()
    target = protected / "artifact"
    target.write_text("synthetic fixture")
    if case == "target":
        (release / "valid-link").symlink_to(target)
    else:
        (protected / "hidden-link").symlink_to(target)
    protected.chmod(0)
    try:
        result, records = run_symlink_probe(release)
        assert result.returncode != 0
        assert any(x.get("status") == "inconclusive" and x.get("error") == "PermissionError" for x in records)
        assert records[-1]["failures"] >= 1
        assert "QUEBRADO" not in result.stdout
    finally:
        protected.chmod(0o700)
    assert target.is_file()


@pytest.mark.parametrize("case", ["missing", "file"])
def test_symlink_probe_rejects_unavailable_root(tmp_path: Path, case: str):
    release = tmp_path / "unavailable"
    if case == "file":
        release.write_text("not a directory")
    result, records = run_symlink_probe(release)
    assert result.returncode != 0
    assert len(records) == 1 and records[0]["status"] == "inconclusive"


INVENTORY_REFERENCE = SKILLS / "orchestrator-runtime-ops/references/safe-deployment-inventory.md"
GIT_CLONE_STEP = "prefect.deployments.steps.git_clone"


def deployment_inventory_program() -> str:
    blocks = re.findall(r"```python\n(.*?)\n```", INVENTORY_REFERENCE.read_text(), re.DOTALL)
    assert len(blocks) == 1
    return blocks[0]


def run_deployment_inventory(data):
    return subprocess.run(
        [sys.executable, "-c", deployment_inventory_program()],
        input=json.dumps(data), capture_output=True, text=True, timeout=10,
    )


def git_deployment(repository: str, **fields):
    return {"pull_steps": [{GIT_CLONE_STEP: {"repository": repository, **fields}}]}


def test_deployment_inventory_redacts_urls_and_reports_missing_commit():
    marker = "SYNTHETIC_PRIVATE_MARKER"
    result = run_deployment_inventory([
        git_deployment(f"https://user:{marker}@example.invalid/repo.git?token={marker}#{marker}", branch=marker),
        git_deployment("https://example.invalid/repo.git", commit_sha="a" * 40),
        git_deployment("https://example.invalid/repo.git", commit_sha=marker),
    ])
    assert result.returncode == 0, result.stderr
    assert marker not in result.stdout + result.stderr
    assert "example.invalid" not in result.stdout
    records = json.loads(result.stdout)
    rows = records["git_steps"]
    assert records["deployments_examined"] == records["git_steps_examined"] == 3
    assert len({x["repository_id"] for x in rows}) == 1
    assert [x["pinning"] for x in rows] == ["unpinned", "pinned_literal", "unresolved_revision"]
    assert [x["commit_sha"] for x in rows] == [None, "a" * 40, None]


def test_deployment_inventory_supports_scp_without_disclosing_username():
    result = run_deployment_inventory([
        git_deployment("SYNTHETIC_PRIVATE_USER@example.invalid:org/repo.git"),
        git_deployment("ssh://example.invalid/org/repo.git"),
        git_deployment("SYNTHETIC_PRIVATE_USER@example.invalid:/org/repo.git"),
    ])
    assert result.returncode == 0, result.stderr
    rows = json.loads(result.stdout)["git_steps"]
    assert rows[0]["repository_id"] != rows[1]["repository_id"]
    assert rows[1]["repository_id"] == rows[2]["repository_id"]
    assert "SYNTHETIC_PRIVATE_USER" not in result.stdout + result.stderr


@pytest.mark.parametrize("invalid", [
    {}, {"pull_steps": "invalid"},
    {"pull_steps": [{GIT_CLONE_STEP: {"repository": "https://example.invalid/repo.git", "commit_sha": 17}}]},
    {"pull_steps": [{GIT_CLONE_STEP: {"repository": "https://example.invalid/repo%0Asecret.git"}}]},
    {"pull_steps": [{GIT_CLONE_STEP: {"repository": "https://example.invalid:bad/repo.git"}}]},
    {"pull_steps": [{GIT_CLONE_STEP: {"repository": "/local/repo"}}]},
])
def test_deployment_inventory_rejects_entire_invalid_collection_without_partial_output(invalid):
    result = run_deployment_inventory([git_deployment("https://example.invalid/valid.git"), invalid])
    assert result.returncode != 0
    assert result.stdout == ""
    assert "Traceback" not in result.stderr
    assert "example.invalid" not in result.stderr


def test_deployment_inventory_does_not_claim_unknown_steps_are_pinned():
    result = run_deployment_inventory([{"pull_steps": [{"custom.clone": {"secret": "SYNTHETIC_PRIVATE_VALUE"}}]}])
    assert result.returncode == 0
    report = json.loads(result.stdout)
    assert report["git_steps_examined"] == 0 and report["git_steps"] == []
    assert report["other_steps_not_assessed"] is True
    assert "SYNTHETIC_PRIVATE_VALUE" not in result.stdout + result.stderr


def env_names_program() -> str:
    text = (SKILLS / "effective-config-tracing/SKILL.md").read_text()
    match = re.search(r"\| python3 -c '([^']+)'", text)
    assert match is not None
    return match.group(1)


def run_env_names(raw: str):
    return subprocess.run(
        [sys.executable, "-c", env_names_program()], input=raw,
        capture_output=True, text=True, timeout=10,
    )


def test_env_names_filter_emits_only_escaped_names_and_accepts_absent_sources():
    marker = "SYNTHETIC_PRIVATE_VALUE"
    result = run_env_names(json.dumps([
        {}, {"job_variables": None}, {"job_variables": {}},
        {"job_variables": {"env": None}},
        {"name": marker, "job_variables": {"env": {"line\nbreak": marker, "B": {"secret": marker}}}},
        {"job_variables": {"env": {"B": marker}}},
    ]))
    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout) == ["B", "line\nbreak"]
    assert "\\nbreak" in result.stdout
    assert marker not in result.stdout + result.stderr


@pytest.mark.parametrize("invalid", [
    None, {}, "SYNTHETIC_PRIVATE_VALUE", [None], ["SYNTHETIC_PRIVATE_VALUE"],
    [{"job_variables": "SYNTHETIC_PRIVATE_VALUE"}],
    [{"job_variables": []}],
    [{"job_variables": {"env": "SYNTHETIC_PRIVATE_VALUE"}}],
    [{"job_variables": {"env": []}}],
    [{"job_variables": {"env": {"OK": "SYNTHETIC_PRIVATE_VALUE"}}}, {"job_variables": 42}],
])
def test_env_names_filter_rejects_invalid_schema_without_partial_output(invalid):
    result = run_env_names(json.dumps(invalid))
    assert result.returncode != 0
    assert result.stdout == ""
    assert result.stderr == "Resposta invalida; configuracao nao verificada.\n"


def test_env_names_filter_rejects_malformed_json_without_echoing_input():
    result = run_env_names('{"SYNTHETIC_PRIVATE_VALUE":')
    assert result.returncode != 0 and result.stdout == ""
    assert result.stderr == "Resposta invalida; configuracao nao verificada.\n"


def shell_example(path: Path, marker: str) -> str:
    return next(block for block in re.findall(r"```bash\n(.*?)\n```", path.read_text(), re.DOTALL) if marker in block)


def test_unit_source_probe_preserves_inspection_failure():
    program = shell_example(SKILLS / "effective-config-tracing/SKILL.md", "FragmentPath")
    stub = "systemctl() { return 23; }; export -f systemctl\n"
    result = subprocess.run(["bash", "-c", stub + program], capture_output=True, text=True, timeout=10)
    assert result.returncode != 0
    assert result.stdout == ""


def test_schema_probe_does_not_use_existing_file_after_fetch_failure(tmp_path: Path):
    destination = tmp_path / "DESTINO_APROVADO"
    destination.mkdir()
    stale = destination / "spec.json"
    stale.write_text(json.dumps({"components": {"schemas": {"Modelo": {"properties": {}}}}}))
    venv = tmp_path / "VENV/bin"
    venv.mkdir(parents=True)
    executed = tmp_path / "comparison-executed"
    interpreter = venv / "python"
    interpreter.write_text("#!/bin/sh\ntouch comparison-executed\n")
    interpreter.chmod(0o700)
    program = shell_example(SKILLS / "verify-against-the-host/references/probes.md", "SERVIDOR/openapi.json")
    result = subprocess.run(["bash", "-c", "curl() { return 22; }; export -f curl\n" + program], cwd=tmp_path, capture_output=True, text=True, timeout=10)
    assert result.returncode != 0
    assert result.stdout == "" and not executed.exists()
    assert stale.exists()


def test_deployment_inventory_rejects_deep_json_with_fixed_error():
    result = subprocess.run(
        [sys.executable, "-c", deployment_inventory_program()],
        input="[" * 2000 + "0" + "]" * 2000,
        capture_output=True, text=True, timeout=10,
    )
    assert result.returncode != 0 and result.stdout == ""
    assert result.stderr == "Inventário não verificado: entrada ou schema inválido.\n"


def test_unit_source_probe_does_not_expose_continued_environment_value():
    program = shell_example(SKILLS / "effective-config-tracing/SKILL.md", "FragmentPath")
    # The second physical line is still part of Environment, despite looking like
    # another directive. A line-oriented redaction would print the private value.
    unit = "Environment=KEY=start \\\nEnvironmentFile=SYNTHETIC_PRIVATE_VALUE \\\nend\nExecStart=/app SYNTHETIC_PRIVATE_VALUE\n"
    stub = """systemctl() {
if [ "$1" = cat ]; then printf %s "$SYNTHETIC_UNIT";
else printf '%s\\n' 'FragmentPath=/approved/unit.service'; fi;
}; export -f systemctl
"""
    result = subprocess.run(["bash", "-c", stub + program], env=dict(os.environ, SYNTHETIC_UNIT=unit), capture_output=True, text=True, timeout=10)
    assert result.returncode == 0
    assert "FragmentPath=/approved/unit.service" in result.stdout
    assert "SYNTHETIC_PRIVATE_VALUE" not in result.stdout + result.stderr
