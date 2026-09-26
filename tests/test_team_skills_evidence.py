from __future__ import annotations

from pathlib import Path
import subprocess

import finance_adaptive_agents.team_skills.evidence as evidence_module
from finance_adaptive_agents.team_skills.evidence import collect_skill_bootstrap_evidence


def test_repository_evidence_prunes_excluded_trees_and_bounds_deterministically(
    tmp_path: Path,
) -> None:
    for directory in ("node_modules", ".git", ".team-skills", "generated"):
        target = tmp_path / directory
        target.mkdir()
        (target / "ignored.py").write_text("ignored = True\n", encoding="utf-8")

    source = tmp_path / "src"
    source.mkdir()
    for index in reversed(range(401)):
        (source / f"module-{index:03}.py").write_text("value = 1\n", encoding="utf-8")

    evidence = collect_skill_bootstrap_evidence(
        tmp_path,
        "company/example",
        excluded_paths=(".team-skills", "generated"),
    )

    assert len(evidence.data["files"]) == 400
    assert evidence.data["files"][0] == "src/module-000.py"
    assert evidence.data["files"][-1] == "src/module-399.py"
    assert evidence.data["file_extensions"] == {".py": 401}
    assert evidence.data["components"] == {"src": 401}
    assert evidence.data["observed_files"] == 401
    assert not any("ignored.py" in path for path in evidence.data["files"])


def test_repository_evidence_represents_late_components_and_manifest_changes(
    tmp_path: Path,
) -> None:
    early = tmp_path / "a-large-component"
    early.mkdir()
    for index in range(500):
        (early / f"module-{index:03}.py").write_text("value = 1\n", encoding="utf-8")

    late = tmp_path / "z-service"
    late.mkdir()
    manifest = late / "package.json"
    manifest.write_text('{"name":"service","dependencies":{}}\n', encoding="utf-8")
    (late / "worker.ts").write_text("export const value = 1;\n", encoding="utf-8")

    before = collect_skill_bootstrap_evidence(tmp_path, "company/example")
    manifest.write_text('{"name":"service","dependencies":{"x":"1"}}\n', encoding="utf-8")
    after = collect_skill_bootstrap_evidence(tmp_path, "company/example")

    assert len(before.data["files"]) == 400
    assert "z-service/package.json" in before.data["files"]
    assert "z-service/worker.ts" in before.data["files"]
    assert before.data["manifests"] == ("z-service/package.json",)
    assert before.data["components"] == {"a-large-component": 500, "z-service": 2}
    assert before.data["observed_files"] == 502
    assert before.data["manifest_set_sha256"] != after.data["manifest_set_sha256"]
    assert before.sha256 != after.sha256


def test_repository_evidence_respects_git_ignored_files(tmp_path: Path) -> None:
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    (tmp_path / ".gitignore").write_text("build/\n.pytest_cache/\n", encoding="utf-8")
    source = tmp_path / "src"
    source.mkdir()
    (source / "tracked.py").write_text("value = 1\n", encoding="utf-8")
    (tmp_path / "notes.txt").write_text("planned work\n", encoding="utf-8")
    build = tmp_path / "build"
    build.mkdir()
    (build / "artifact.py").write_text("generated = True\n", encoding="utf-8")
    cache = tmp_path / ".pytest_cache"
    cache.mkdir()
    (cache / "nodeids").write_text("[]\n", encoding="utf-8")
    subprocess.run(
        ["git", "add", ".gitignore", "src/tracked.py"],
        cwd=tmp_path,
        check=True,
    )

    evidence = collect_skill_bootstrap_evidence(tmp_path, "company/example")

    assert evidence.data["file_source"] == "git"
    assert ".gitignore" in evidence.data["files"]
    assert "src/tracked.py" in evidence.data["files"]
    assert "notes.txt" in evidence.data["files"]
    assert not any(path.startswith("build/") for path in evidence.data["files"])
    assert not any(path.startswith(".pytest_cache/") for path in evidence.data["files"])


def test_repository_evidence_has_a_hard_observation_budget(
    tmp_path: Path,
    monkeypatch,
) -> None:
    monkeypatch.setattr(evidence_module, "_MAX_SCANNED_FILES", 5)
    for index in range(8):
        (tmp_path / f"file-{index}.txt").write_text("value\n", encoding="utf-8")

    evidence = collect_skill_bootstrap_evidence(tmp_path, "company/example")

    assert evidence.data["observed_files"] == 5
    assert evidence.data["scan_limit"] == 5
    assert evidence.data["scan_truncated"] is True
    assert len(evidence.data["files"]) == 5


def test_repository_evidence_bounds_extension_cardinality(
    tmp_path: Path,
    monkeypatch,
) -> None:
    monkeypatch.setattr(evidence_module, "_MAX_EXTENSIONS", 2)
    for suffix in ("a", "b", "c"):
        (tmp_path / f"file.{suffix}").write_text("value\n", encoding="utf-8")

    evidence = collect_skill_bootstrap_evidence(tmp_path, "company/example")

    assert evidence.data["file_extensions"] == {".a": 1, ".b": 1}
    assert evidence.data["other_extension_files"] == 1
