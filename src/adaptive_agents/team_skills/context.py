"""Read-only, process-local Team Skills contexts for terminal and agent work."""

from __future__ import annotations

import tempfile
import uuid
from dataclasses import dataclass
from pathlib import Path
from threading import Lock
from typing import Callable

import finance_adaptive_agents.admission_control as native

from .canonical import CanonicalCatalog, CanonicalSkill
from .consumer import ConsumerSource, default_consumer_source, validate_catalog_path, validate_source_url
from .evidence import (
    RepositorySkillsEvidence,
    collect_skill_bootstrap_evidence,
    collect_terminal_context_evidence,
)
from .repository import TeamSkillsError, find_repository, repository_identity
from .routing import (
    admission_context,
    native_catalog,
    read_catalog,
    select_skills,
    validate_selection,
)
from .selector import SelectionConversationTurn, SkillSelection, SkillSelectionEntry, SkillSelector
from .source import GitKnowledgeSource


@dataclass(frozen=True)
class TransientContextResult:
    """One validated selection from a transient context session."""

    context_id: str
    context_kind: str
    source_id: str
    source_commit: str
    repository_id: str | None
    evidence_sha256: str
    selected_skills: tuple[CanonicalSkill, ...]
    rejected_ids: tuple[str, ...]
    selection_reasons: tuple[tuple[str, str | None], ...]
    offline: bool

    def to_data(self, *, include_content: bool = False) -> dict[str, object]:
        skills: list[dict[str, object]] = []
        reasons = dict(self.selection_reasons)
        for skill in self.selected_skills:
            item: dict[str, object] = {
                "id": skill.id,
                "name": skill.name,
                "description": skill.description,
                "revision": skill.revision,
                "files": [path for path, _content in skill.files],
                "reason": reasons.get(skill.id),
            }
            if include_content:
                item["content"] = {
                    path: content.decode("utf-8") for path, content in skill.files
                }
            skills.append(item)
        return {
            "schema_version": 1,
            "context_id": self.context_id,
            "context_kind": self.context_kind,
            "source": {
                "id": self.source_id,
                "commit": self.source_commit,
                "offline": self.offline,
            },
            "repository": self.repository_id,
            "evidence_sha256": self.evidence_sha256,
            "selected_skills": skills,
            "rejected_ids": list(self.rejected_ids),
            "writes": [],
        }


class TransientContextSession:
    """Immutable source/evidence snapshot with process-local conversation history."""

    def __init__(
        self,
        *,
        context_id: str,
        context_kind: str,
        repository_id: str | None,
        evidence: RepositorySkillsEvidence,
        canonical: CanonicalCatalog,
        selector: SkillSelector,
        offline: bool,
    ) -> None:
        self.context_id = context_id
        self.context_kind = context_kind
        self.repository_id = repository_id
        self.evidence = evidence
        self.canonical = canonical
        self.selector = selector
        self.offline = offline
        self._catalog = native_catalog(canonical)
        self._admission_context = admission_context(canonical, repository_id or "@terminal")
        self._snapshot = native.admit(self._admission_context, self._catalog)
        self._conversation: tuple[SelectionConversationTurn, ...] = ()
        self._selected_ids: tuple[str, ...] = ()

    @property
    def selected_ids(self) -> tuple[str, ...]:
        return self._selected_ids

    def _result(self, selection: SkillSelection, receipt: native.ExposureReceipt) -> TransientContextResult:
        selected_ids = tuple(item.id for item in selection.selected)
        validation = validate_selection(
            selected_ids,
            receipt,
            self._admission_context,
            self._catalog,
        )
        accepted = set(validation.final_resource_ids)
        self._selected_ids = tuple(skill.id for skill in self.canonical.skills if skill.id in accepted)
        rejected = tuple(
            decision.resource_id
            for decision in validation.selection_decisions
            if not decision.admitted
        )
        return TransientContextResult(
            self.context_id,
            self.context_kind,
            self.canonical.descriptor.source_id,
            self.canonical.source_commit,
            self.repository_id,
            self.evidence.sha256,
            tuple(skill for skill in self.canonical.skills if skill.id in accepted),
            rejected,
            tuple((item.id, item.reason) for item in selection.selected),
            self.offline,
        )

    def select(
        self,
        task: str,
        *,
        progress: Callable[[str], None] | None = None,
    ) -> TransientContextResult:
        task = task.strip()
        if not task:
            raise TeamSkillsError("task must not be empty")
        if len(task) > 4_000:
            raise TeamSkillsError("task must be at most 4,000 characters")
        selection, receipt = select_skills(
            self.selector,
            self.evidence,
            self._snapshot,
            task=task,
            conversation=self._conversation,
            progress=progress,
        )
        result = self._result(selection, receipt)
        self._conversation = (
            *self._conversation,
            SelectionConversationTurn(task, selection),
        )
        return result

    def select_exact(self, skill_id: str) -> TransientContextResult:
        skill_id = skill_id.strip()
        if not skill_id:
            raise TeamSkillsError("Skill ID must not be empty")
        exposed = tuple(
            resource for resource in self._snapshot.exposable_resources if resource.id == skill_id
        )
        receipt = self._snapshot.record_exposure(exposed)
        selection = SkillSelection((SkillSelectionEntry(skill_id, "Explicitly requested by ID."),))
        return self._result(selection, receipt)

    def read_selected_file(self, skill_id: str, path: str = "SKILL.md") -> str:
        if skill_id not in self._selected_ids:
            raise TeamSkillsError("Skill was not selected and validated in this context")
        skill = self.canonical.by_id().get(skill_id)
        if skill is None:
            raise TeamSkillsError("Skill is not present in this pinned context")
        files = dict(skill.files)
        if path not in files:
            raise TeamSkillsError(f"Skill file is not available: {path}")
        return files[path].decode("utf-8")


class TeamSkillsContextService:
    """Create transient sessions without materializing knowledge in the working directory."""

    def __init__(self, selector: SkillSelector) -> None:
        self.selector = selector
        self._catalog_key: tuple[str, str, str] | None = None
        self._catalog: CanonicalCatalog | None = None
        self._catalog_lock = Lock()

    def _read_catalog_cached(
        self,
        source: GitKnowledgeSource,
        commit: str,
        catalog_path: str,
    ) -> CanonicalCatalog:
        if source.repository is None:
            raise TeamSkillsError("canonical source must be acquired before it can be read")
        key = (str(source.repository.resolve()), catalog_path, commit)
        with self._catalog_lock:
            if self._catalog_key == key and self._catalog is not None:
                return self._catalog
            catalog = read_catalog(source, commit, catalog_path)
            self._catalog_key = key
            self._catalog = catalog
            return catalog

    def start(
        self,
        location: str | Path = ".",
        *,
        source: ConsumerSource | None = None,
        offline: bool = False,
        progress: Callable[[str], None] | None = None,
    ) -> TransientContextSession:
        working_directory = Path(location).expanduser().resolve()
        if not working_directory.is_dir():
            raise TeamSkillsError(f"working directory is not a directory: {working_directory}")
        source = default_consumer_source() if source is None else source
        if source.type != "git":
            raise TeamSkillsError("consumer source type must be git")
        source_url = validate_source_url(source.url)
        ref = source.ref.strip()
        catalog_path = validate_catalog_path(source.catalog_path)
        if not ref or ref.startswith("-"):
            raise TeamSkillsError("source ref must be a non-empty Git ref")

        try:
            repository_root = find_repository(working_directory)
        except TeamSkillsError:
            repository_root = None
        repository_id = repository_identity(repository_root) if repository_root else None
        context_kind = "repository" if repository_root else "terminal"
        if progress is not None:
            progress(
                "Collecting read-only repository evidence"
                if repository_root
                else "Using task-only terminal evidence"
            )
        evidence = (
            collect_skill_bootstrap_evidence(repository_root, repository_id)
            if repository_root and repository_id
            else collect_terminal_context_evidence()
        )

        if progress is not None:
            progress(
                "Reading and validating the local canonical replica"
                if offline
                else "Refreshing and validating the local canonical replica"
            )
        with tempfile.TemporaryDirectory(prefix="team-skills-context-") as temporary:
            git_source = GitKnowledgeSource(
                working_directory,
                runtime_root=Path(temporary) / "runtime",
            )
            commit = git_source.acquire(
                source_url,
                ref,
                catalog_path=catalog_path,
                offline=offline,
            )
            effective_offline = offline or git_source.used_offline_fallback
            canonical = self._read_catalog_cached(git_source, commit, catalog_path)

        if progress is not None:
            progress("Creating an in-memory admitted Skill context")
        return TransientContextSession(
            context_id=uuid.uuid4().hex,
            context_kind=context_kind,
            repository_id=repository_id,
            evidence=evidence,
            canonical=canonical,
            selector=self.selector,
            offline=effective_offline,
        )
