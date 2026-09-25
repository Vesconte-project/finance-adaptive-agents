"""Canonical, text-only Agent Skills loaded from one pinned Git snapshot."""

from __future__ import annotations

import hashlib
import json
import os
import re
import stat
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Callable

from adaptive_agents.team_skills.repository import TeamSkillsError


SKILL_NAME = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
RESOURCE_ID = re.compile(r"^[A-Za-z][A-Za-z0-9_.-]*$")
REFERENCE_SUFFIXES = frozenset({".md", ".txt", ".json", ".yaml", ".yml"})
MAX_FILE_BYTES = 1_000_000
MAX_SKILL_BYTES = 4_000_000
MAX_SKILL_NAME_LENGTH = 64
MAX_SKILL_DESCRIPTION_LENGTH = 1024


@dataclass(frozen=True)
class SourceDescriptor:
    source_id: str
    organization: str
    team: str
    organization_default_skill_ids: tuple[str, ...] = ()
    organization_only_skill_ids: tuple[str, ...] = ()


@dataclass(frozen=True)
class CanonicalSkill:
    id: str
    name: str
    description: str
    state: str
    source_path: str
    revision: str
    digest_sha256: str
    files: tuple[tuple[str, bytes], ...]
    skill_text: str
    organization_scope: str | None = None

    @property
    def materialized_path(self) -> str:
        return f".agents/skills/{self.name}"


@dataclass(frozen=True)
class CanonicalCatalog:
    descriptor: SourceDescriptor
    source_commit: str
    skills: tuple[CanonicalSkill, ...]

    def by_id(self) -> dict[str, CanonicalSkill]:
        return {skill.id: skill for skill in self.skills}


def _json_object(path: Path, *, allowed: frozenset[str]) -> dict[str, object]:
    if path.is_symlink() or not path.is_file():
        raise TeamSkillsError(f"canonical descriptor is missing or unsafe: {path.name}")
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise TeamSkillsError(f"cannot read canonical descriptor {path}: {error}") from error
    if not isinstance(value, dict):
        raise TeamSkillsError(f"canonical descriptor must be a JSON object: {path}")
    unknown = sorted(set(value) - allowed)
    if unknown:
        raise TeamSkillsError(
            f"unsupported field(s) in {path.name}: {', '.join(unknown)}"
        )
    return value


def _text(value: object, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise TeamSkillsError(f"canonical {field} must be a non-empty string")
    return value.strip()


def _parse_source(root: Path) -> SourceDescriptor:
    data = _json_object(
        root / "team-skills.json",
        allowed=frozenset(
            {
                "schema_version",
                "source_id",
                "organization",
                "team",
                "organization_default_skill_ids",
                "organization_only_skill_ids",
            }
        ),
    )
    schema_version = data.get("schema_version")
    if schema_version not in {1, 2}:
        raise TeamSkillsError("canonical source schema_version must be 1 or 2")
    raw_defaults = data.get("organization_default_skill_ids", [])
    if schema_version == 1 and "organization_default_skill_ids" in data:
        raise TeamSkillsError("organization_default_skill_ids requires canonical source schema_version 2")
    if schema_version == 1 and "organization_only_skill_ids" in data:
        raise TeamSkillsError("organization_only_skill_ids requires canonical source schema_version 2")
    if not isinstance(raw_defaults, list) or any(
        not isinstance(skill_id, str) or not RESOURCE_ID.fullmatch(skill_id) for skill_id in raw_defaults
    ):
        raise TeamSkillsError("organization_default_skill_ids must be an array of valid Skill IDs")
    defaults = tuple(raw_defaults)
    if len(defaults) != len(set(defaults)):
        raise TeamSkillsError("organization_default_skill_ids must not contain duplicates")
    organization = data.get("organization")
    if not isinstance(organization, str):
        raise TeamSkillsError("canonical organization must be a string")
    organization = organization.strip()
    raw_private = data.get("organization_only_skill_ids", [])
    if not isinstance(raw_private, list) or any(
        not isinstance(skill_id, str) or not RESOURCE_ID.fullmatch(skill_id) for skill_id in raw_private
    ):
        raise TeamSkillsError("organization_only_skill_ids must be an array of valid Skill IDs")
    organization_only = tuple(raw_private)
    if len(organization_only) != len(set(organization_only)):
        raise TeamSkillsError("organization_only_skill_ids must not contain duplicates")
    if not organization and (defaults or organization_only):
        raise TeamSkillsError(
            "organization defaults and organization-only Skills require a non-empty organization"
        )
    return SourceDescriptor(
        _text(data.get("source_id"), "source_id"),
        organization,
        _text(data.get("team"), "team"),
        defaults,
        organization_only,
    )


def _frontmatter_values(lines: list[str]) -> dict[str, str]:
    values: dict[str, str] = {}
    index = 0
    while index < len(lines):
        line = lines[index]
        if not line.strip():
            index += 1
            continue
        if line[:1].isspace() or ":" not in line:
            raise TeamSkillsError("SKILL.md frontmatter must use top-level key: value fields")
        field, raw = line.split(":", 1)
        field = field.strip()
        raw = raw.strip()
        if not field or field in values:
            raise TeamSkillsError(f"SKILL.md has invalid or duplicate {field or '<empty>'} frontmatter")
        if raw in {">", ">-", ">+", "|", "|-", "|+"}:
            block: list[str] = []
            index += 1
            while index < len(lines) and (not lines[index].strip() or lines[index][:1].isspace()):
                block.append(lines[index].strip())
                index += 1
            values[field] = ("\n" if raw.startswith("|") else " ").join(block).strip()
            continue
        values[field] = raw.strip('"\'')
        index += 1
    return values


def _parse_skill_text(text: str) -> tuple[str, str]:
    lines = text.splitlines()
    if not lines or lines[0] != "---":
        raise TeamSkillsError("SKILL.md must start with a --- frontmatter delimiter")
    try:
        closing = lines.index("---", 1)
    except ValueError as error:
        raise TeamSkillsError("SKILL.md frontmatter must end with a --- delimiter") from error
    frontmatter = lines[1:closing]
    values = _frontmatter_values(frontmatter)
    unsupported = sorted(set(values) - {"name", "description"})
    if unsupported:
        raise TeamSkillsError(
            f"unsupported canonical Skill frontmatter field(s): {', '.join(unsupported)}"
        )
    name = values.get("name")
    description = values.get("description")
    if name is None or not SKILL_NAME.fullmatch(name):
        raise TeamSkillsError("SKILL.md name must be a lowercase hyphenated Skill name")
    if len(name) > MAX_SKILL_NAME_LENGTH:
        raise TeamSkillsError(
            f"SKILL.md name must be at most {MAX_SKILL_NAME_LENGTH} characters"
        )
    if description is None or not description.strip():
        raise TeamSkillsError("SKILL.md description must be non-empty")
    normalized_description = " ".join(description.split())
    if len(normalized_description) > MAX_SKILL_DESCRIPTION_LENGTH:
        raise TeamSkillsError(
            f"SKILL.md description must be at most {MAX_SKILL_DESCRIPTION_LENGTH} characters"
        )
    if not "\n".join(lines[closing + 1 :]).strip():
        raise TeamSkillsError("SKILL.md body must be non-empty")
    return name, normalized_description


def package_digest(files: tuple[tuple[str, bytes], ...]) -> str:
    """Hash exact materializable paths and bytes in stable path order."""

    digest = hashlib.sha256()
    for relative, content in sorted(files):
        encoded_path = relative.encode("utf-8")
        digest.update(len(encoded_path).to_bytes(4, "big"))
        digest.update(encoded_path)
        digest.update(len(content).to_bytes(8, "big"))
        digest.update(content)
    return digest.hexdigest()


def directory_digest(path: Path) -> str:
    if path.is_symlink() or not path.is_dir():
        raise TeamSkillsError(f"managed Agent Skill path is not a safe directory: {path}")
    files: list[tuple[str, bytes]] = []
    for candidate in sorted(path.rglob("*")):
        relative = candidate.relative_to(path).as_posix()
        if candidate.is_symlink() or not (candidate.is_dir() or candidate.is_file()):
            raise TeamSkillsError(f"managed Agent Skill contains unsafe entry: {relative}")
        if candidate.is_file():
            files.append((relative, candidate.read_bytes()))
    return package_digest(tuple(files))


def _skill_files(directory: Path) -> tuple[tuple[str, bytes], ...]:
    materializable: list[tuple[str, bytes]] = []
    total = 0
    for path in sorted(directory.rglob("*")):
        relative = path.relative_to(directory)
        label = relative.as_posix()
        if path.is_symlink():
            raise TeamSkillsError(f"canonical Skill contains symlink: {label}")
        mode = path.stat(follow_symlinks=False).st_mode
        if path.is_dir():
            if "scripts" in relative.parts:
                raise TeamSkillsError("canonical Skills may not contain scripts/")
            continue
        if not stat.S_ISREG(mode):
            raise TeamSkillsError(f"canonical Skill contains non-regular file: {label}")
        if mode & 0o111:
            raise TeamSkillsError(f"canonical Skill contains executable file: {label}")
        allowed = label in {"SKILL.md", "team-skills.json"} or (
            relative.parts[0] == "references" and path.suffix.lower() in REFERENCE_SUFFIXES
        )
        if not allowed:
            raise TeamSkillsError(f"unsupported canonical Skill file: {label}")
        data = path.read_bytes()
        if len(data) > MAX_FILE_BYTES:
            raise TeamSkillsError(f"canonical Skill file is too large: {label}")
        try:
            data.decode("utf-8")
        except UnicodeDecodeError as error:
            raise TeamSkillsError(f"canonical Skill file must be UTF-8 text: {label}") from error
        total += len(data)
        if total > MAX_SKILL_BYTES:
            raise TeamSkillsError(f"canonical Skill package is too large: {directory.name}")
        if label != "team-skills.json":
            materializable.append((label, data))
    names = {name for name, _data in materializable}
    if "SKILL.md" not in names:
        raise TeamSkillsError(f"canonical Skill is missing SKILL.md: {directory.name}")
    return tuple(materializable)


def load_canonical_catalog(
    root: Path,
    source_commit: str,
    revision_for: Callable[[str], str],
) -> CanonicalCatalog:
    descriptor = _parse_source(root)
    skills_root = root / "skills"
    if not skills_root.exists():
        return CanonicalCatalog(descriptor, source_commit, ())
    if skills_root.is_symlink() or not skills_root.is_dir():
        raise TeamSkillsError("canonical source must contain a safe skills/ directory")
    stray = [
        path.name
        for path in skills_root.iterdir()
        if path.name != ".gitkeep" and (path.is_symlink() or not path.is_dir())
    ]
    if stray:
        raise TeamSkillsError(f"canonical skills/ contains unsafe entry: {sorted(stray)[0]}")
    parsed: list[CanonicalSkill] = []
    for directory in sorted(
        (path for path in skills_root.iterdir() if path.name != ".gitkeep"),
        key=lambda item: item.name,
    ):
        sidecar = _json_object(
            directory / "team-skills.json",
            allowed=frozenset({"schema_version", "id", "state"}),
        )
        if sidecar.get("schema_version") != 1:
            raise TeamSkillsError(f"canonical Skill {directory.name} schema_version must be 1")
        resource_id = _text(sidecar.get("id"), f"Skill {directory.name} id")
        if not RESOURCE_ID.fullmatch(resource_id):
            raise TeamSkillsError(f"canonical Skill has invalid stable ID: {resource_id}")
        state = _text(sidecar.get("state"), f"Skill {resource_id} state")
        if state not in {"active", "revoked"}:
            raise TeamSkillsError(f"canonical Skill {resource_id} state must be active or revoked")
        files = _skill_files(directory)
        skill_bytes = dict(files)["SKILL.md"]
        skill_text = skill_bytes.decode("utf-8")
        name, description = _parse_skill_text(skill_text)
        if name != directory.name:
            raise TeamSkillsError(
                f"canonical Skill directory {directory.name!r} must match Skill name {name!r}"
            )
        source_path = PurePosixPath("skills", directory.name).as_posix()
        parsed.append(
            CanonicalSkill(
                resource_id,
                name,
                description,
                state,
                source_path,
                revision_for(source_path),
                package_digest(files),
                files,
                skill_text,
                descriptor.organization
                if resource_id in descriptor.organization_only_skill_ids
                else None,
            )
        )
    ids = [skill.id for skill in parsed]
    names = [skill.name for skill in parsed]
    if len(ids) != len(set(ids)):
        raise TeamSkillsError("canonical Skill IDs must be unique")
    if len(names) != len(set(names)):
        raise TeamSkillsError("canonical Skill names must be unique")
    defaults = set(descriptor.organization_default_skill_ids)
    unknown_defaults = defaults - set(ids)
    if unknown_defaults:
        raise TeamSkillsError(
            f"organization default Skill is missing from catalog: {sorted(unknown_defaults)[0]}"
        )
    revoked_defaults = {
        skill.id for skill in parsed if skill.id in defaults and skill.state != "active"
    }
    if revoked_defaults:
        raise TeamSkillsError(
            f"organization default Skill must be active: {sorted(revoked_defaults)[0]}"
        )
    unknown_private = set(descriptor.organization_only_skill_ids) - set(ids)
    if unknown_private:
        raise TeamSkillsError(
            f"organization-only Skill is missing from catalog: {sorted(unknown_private)[0]}"
        )
    revoked_private = {
        skill.id
        for skill in parsed
        if skill.id in descriptor.organization_only_skill_ids and skill.state != "active"
    }
    if revoked_private:
        raise TeamSkillsError(
            f"organization-only Skill must be active: {sorted(revoked_private)[0]}"
        )
    return CanonicalCatalog(descriptor, source_commit, tuple(parsed))
