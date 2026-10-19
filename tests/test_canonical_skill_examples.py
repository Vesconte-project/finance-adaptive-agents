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
