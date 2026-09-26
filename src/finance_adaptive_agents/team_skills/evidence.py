"""Bounded, literal repository facts for model-owned Skill selection."""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any


_EXCLUDED_DIRECTORIES = frozenset({
    ".git",
    ".agents",
    ".claude",
    ".codex",
    ".mypy_cache",
    ".nox",
    ".pytest_cache",
    ".ruff_cache",
    ".tox",
    ".venv",
    "__pycache__",
    "build",
    "dist",
    "node_modules",
    "target",
})
_MANIFEST_NAMES = frozenset({
    "pyproject.toml", "package.json", "package-lock.json", "pnpm-lock.yaml", "yarn.lock",
    "requirements.txt", "Pipfile", "go.mod", "Cargo.toml", "pom.xml", "build.gradle",
    "Dockerfile", "docker-compose.yml", "docker-compose.yaml", "wrangler.toml", "terraform.tf",
})
_MAX_SCANNED_FILES = 10_000
_MAX_FILES = 400
_MAX_MANIFESTS = 100
_MAX_COMPONENTS = 100
_MAX_EXTENSIONS = 50
_COMPONENT_SAMPLE_SIZE = 8
_MAX_HASHED_MANIFEST_BYTES = 1_000_000


@dataclass(frozen=True)
class RepositorySkillsEvidence:
    data: dict[str, Any]
    sha256: str


@dataclass(frozen=True)
class _RepositoryInventory:
    files: tuple[str, ...]
    extensions: dict[str, int]
    other_extension_files: int
    manifests: tuple[str, ...]
    manifest_set_sha256: str | None
    components: dict[str, int]
    observed_files: int
    scan_truncated: bool
    file_source: str


def _git_files(root: Path) -> tuple[tuple[str, ...], bool] | None:
    """Return a bounded Git-aware sample, including non-ignored untracked files."""

    try:
        process = subprocess.Popen(
            [
                "git",
                "-C",
                str(root),
                "ls-files",
                "--cached",
                "--others",
                "--exclude-standard",
                "--deduplicate",
                "-z",
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
        )
    except OSError:
        return None
    if process.stdout is None:  # pragma: no cover - guaranteed by stdout=PIPE
        process.kill()
        return None

    paths: list[str] = []
    buffer = b""
    truncated = False
    try:
        while len(paths) <= _MAX_SCANNED_FILES:
            chunk = process.stdout.read(65_536)
            if not chunk:
                break
            values = (buffer + chunk).split(b"\0")
            buffer = values.pop()
            for value in values:
                if value:
                    paths.append(os.fsdecode(value))
                    if len(paths) > _MAX_SCANNED_FILES:
                        truncated = True
                        break
            if truncated:
                break
    finally:
        process.stdout.close()
        if process.poll() is None:
            process.terminate()
        try:
            returncode = process.wait(timeout=2)
        except subprocess.TimeoutExpired:  # pragma: no cover - defensive guard
            process.kill()
            returncode = process.wait()
    if not truncated and returncode != 0:
        return None
    return tuple(paths[:_MAX_SCANNED_FILES]), truncated


def _filesystem_files(root: Path, is_excluded) -> tuple[tuple[str, ...], bool]:
    """Fallback for non-Git directories, with the same observation budget."""

    paths: list[str] = []
    for current, directories, files in os.walk(root, topdown=True, followlinks=False):
        current_path = Path(current)
        directories[:] = sorted(
            directory
            for directory in directories
            if not (current_path / directory).is_symlink()
            and not is_excluded((current_path / directory).relative_to(root).as_posix())
        )
        for filename in sorted(files):
            path = current_path / filename
            relative = path.relative_to(root).as_posix()
            if is_excluded(relative) or path.is_symlink() or not path.is_file():
                continue
            if len(paths) >= _MAX_SCANNED_FILES:
                return tuple(paths), True
            paths.append(relative)
    return tuple(paths), False


def _repository_inventory(root: Path, excluded_paths: tuple[str, ...]) -> _RepositoryInventory:
    excluded = {Path(path).as_posix().strip("/") for path in excluded_paths}
    first_files: list[str] = []
    manifests: list[str] = []
    manifest_digests: dict[str, str] = {}
    extensions: Counter[str] = Counter()
    component_counts: Counter[str] = Counter()
    component_samples: dict[str, list[str]] = defaultdict(list)

    def is_excluded(relative: str) -> bool:
        return any(part in _EXCLUDED_DIRECTORIES for part in Path(relative).parts) or any(
            relative == item or relative.startswith(item + "/") for item in excluded
        )

    git_files = _git_files(root)
    if git_files is None:
        candidates, scan_truncated = _filesystem_files(root, is_excluded)
        file_source = "filesystem"
    else:
        candidates, scan_truncated = git_files
        file_source = "git"

    observed_files = 0
    for relative in candidates:
        path = root / relative
        if is_excluded(relative) or path.is_symlink() or not path.is_file():
            continue
        observed_files += 1
        extensions[Path(relative).suffix.lower() or "[no extension]"] += 1
        component = relative.split("/", 1)[0] if "/" in relative else "."
        component_counts[component] += 1
        if len(first_files) < _MAX_FILES:
            first_files.append(relative)
        if len(component_samples[component]) < _COMPONENT_SAMPLE_SIZE:
            component_samples[component].append(relative)
        if Path(relative).name in _MANIFEST_NAMES:
            manifests.append(relative)
            try:
                if path.stat().st_size <= _MAX_HASHED_MANIFEST_BYTES:
                    manifest_digests[relative] = hashlib.sha256(path.read_bytes()).hexdigest()
            except OSError:
                pass

    bounded_manifests = tuple(sorted(manifests)[:_MAX_MANIFESTS])
    ranked_components = sorted(
        component_counts,
        key=lambda name: (-component_counts[name], name),
    )[:_MAX_COMPONENTS]
    ranked_extensions = sorted(
        extensions,
        key=lambda name: (-extensions[name], name),
    )
    kept_extensions = ranked_extensions[:_MAX_EXTENSIONS]
    bounded_extensions = {
        extension: extensions[extension] for extension in sorted(kept_extensions)
    }
    other_extension_files = sum(
        extensions[extension] for extension in ranked_extensions[_MAX_EXTENSIONS:]
    )
    selected: list[str] = []
    seen: set[str] = set()

    def add(relative: str) -> None:
        if relative not in seen and len(selected) < _MAX_FILES:
            selected.append(relative)
            seen.add(relative)

    for relative in bounded_manifests:
        add(relative)
    for offset in range(_COMPONENT_SAMPLE_SIZE):
        for component in ranked_components:
            sample = component_samples[component]
            if offset < len(sample):
                add(sample[offset])
    for relative in first_files:
        add(relative)

    manifest_set_digest = hashlib.sha256()
    hashed_manifest_count = 0
    for relative in bounded_manifests:
        digest = manifest_digests.get(relative)
        if digest is None:
            continue
        manifest_set_digest.update(relative.encode("utf-8"))
        manifest_set_digest.update(bytes.fromhex(digest))
        hashed_manifest_count += 1
    bounded_components = {
        component: component_counts[component] for component in ranked_components
    }
    return _RepositoryInventory(
        tuple(selected),
        bounded_extensions,
        other_extension_files,
        bounded_manifests,
        manifest_set_digest.hexdigest() if hashed_manifest_count else None,
        bounded_components,
        observed_files,
        scan_truncated,
        file_source,
    )


def collect_skill_bootstrap_evidence(
    root: Path,
    repository_id: str,
    *,
    excluded_paths: tuple[str, ...] = (".team-skills",),
) -> RepositorySkillsEvidence:
    """Expose bounded literal facts; semantic relevance remains model-owned."""
    inventory = _repository_inventory(root, excluded_paths)
    data: dict[str, Any] = {
        "schema_version": 3,
        "repository": repository_id,
        "files": inventory.files,
        "file_extensions": inventory.extensions,
        "other_extension_files": inventory.other_extension_files,
        "manifests": inventory.manifests,
        "manifest_set_sha256": inventory.manifest_set_sha256,
        "components": inventory.components,
        "observed_files": inventory.observed_files,
        "scan_limit": _MAX_SCANNED_FILES,
        "scan_truncated": inventory.scan_truncated,
        "file_source": inventory.file_source,
    }
    encoded = json.dumps(data, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return RepositorySkillsEvidence(data, hashlib.sha256(encoded).hexdigest())


def collect_terminal_context_evidence() -> RepositorySkillsEvidence:
    """Describe a task-only terminal context without inspecting the current directory."""

    data: dict[str, Any] = {
        "schema_version": 3,
        "context_kind": "terminal",
        "repository": None,
        "files": (),
        "file_extensions": {},
        "other_extension_files": 0,
        "manifests": (),
        "manifest_set_sha256": None,
        "components": {},
        "observed_files": 0,
        "scan_limit": 0,
        "scan_truncated": False,
        "file_source": "none",
    }
    encoded = json.dumps(data, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return RepositorySkillsEvidence(data, hashlib.sha256(encoded).hexdigest())
