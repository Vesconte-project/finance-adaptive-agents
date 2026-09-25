"""Shared admission, exposure, semantic selection, and validation pipeline."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Callable

import adaptive_agents.admission_control as native

from .canonical import CanonicalCatalog, load_canonical_catalog
from .evidence import RepositorySkillsEvidence
from .selector import (
    SelectionConversationTurn,
    SkillRoutingEntry,
    SkillSelection,
    SkillSelector,
)
from .source import GitKnowledgeSource


def native_catalog(catalog: CanonicalCatalog) -> native.ResourceCatalog:
    records = []
    for skill in catalog.skills:
        content = native.build_content(
            skill.id,
            skill.revision,
            native.ResourceKind.AGENT_SKILL,
            skill.name,
            skill.description,
            skill.skill_text,
            native.SkillPayload(("agent-skills",), f"{skill.source_path}/SKILL.md"),
        )
        records.append(
            native.ResourceRecord(
                content,
                native.AdmissionEnvelope(
                    lifecycle=native.Lifecycle(
                        native.LifecycleState.APPROVED
                        if skill.state == "active"
                        else native.LifecycleState.REVOKED
                    ),
                    scope=native.Scope(
                        organization=catalog.descriptor.organization,
                        team=catalog.descriptor.team,
                    ),
                    compatibility=(),
                    dependencies=(),
                    exposure_policy=native.ExposurePolicy.REQUIRE_ADMISSIBLE,
                    selectable=True,
                ),
            )
        )
    return native.ResourceCatalog(catalog.source_commit, tuple(records)).validated()


def admission_context(
    catalog: CanonicalCatalog,
    repository_id: str,
    now: datetime | None = None,
) -> native.AdmissionContext:
    return native.AdmissionContext(
        organization=catalog.descriptor.organization,
        team=catalog.descriptor.team,
        repository=repository_id,
        affected_paths=(),
        effective_at=now or datetime.now(timezone.utc),
        facts={},
    )


def read_catalog(
    source: GitKnowledgeSource,
    commit: str,
    catalog_path: str,
) -> CanonicalCatalog:
    with source.snapshot(commit, catalog_path=catalog_path) as snapshot:
        return load_canonical_catalog(
            snapshot,
            commit,
            lambda path: source.revision_for(commit, path, catalog_path=catalog_path),
        )


def select_skills(
    selector: SkillSelector,
    evidence: RepositorySkillsEvidence,
    snapshot: native.AdmissionSnapshot,
    *,
    task: str | None = None,
    organization_default_skill_ids: tuple[str, ...] = (),
    conversation: tuple[SelectionConversationTurn, ...] = (),
    progress: Callable[[str], None] | None = None,
) -> tuple[SkillSelection, native.ExposureReceipt]:
    exposed = snapshot.exposable_resources
    receipt = snapshot.record_exposure(exposed)
    routing = tuple(
        SkillRoutingEntry(resource.id, resource.title, resource.summary) for resource in exposed
    )
    if progress is not None:
        progress("Calling the configured AI selector with read-only factual evidence")
    selector_arguments: dict[str, object] = {}
    if task is not None:
        selector_arguments["task"] = task
    if organization_default_skill_ids:
        selector_arguments["organization_default_skill_ids"] = organization_default_skill_ids
    if conversation:
        selector_arguments["conversation"] = conversation
    selection = selector.select(evidence, routing, **selector_arguments)
    if progress is not None:
        progress("AI selector completed; validating its proposed Skill IDs")
    return selection, receipt


def validate_selection(
    ids: tuple[str, ...],
    receipt: native.ExposureReceipt,
    context: native.AdmissionContext,
    catalog: native.ResourceCatalog,
) -> native.ValidationResult:
    return native.validate(
        tuple(native.CandidateSelection(resource_id) for resource_id in ids),
        receipt,
        context,
        catalog,
    )
