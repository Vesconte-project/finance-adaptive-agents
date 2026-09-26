"""Git-backed portable team Skills for coding agents."""

from .repository import TeamSkillsError, find_repository, repository_identity
from .canonical import CanonicalCatalog, CanonicalSkill, SourceDescriptor
from .onboarding import (
    ONBOARDING_SKILL_NAME,
    install_onboarding_skills,
    onboarding_destinations,
    onboarding_readiness,
    onboarding_skill_text,
)
from .preferences import load_selector_preference, preferences_path, save_selector_preference
from .distribution import DistributionPlan, TeamSkillsDistributionService
from .context import TeamSkillsContextService, TransientContextResult, TransientContextSession
from .evidence import (
    RepositorySkillsEvidence,
    collect_skill_bootstrap_evidence,
    collect_terminal_context_evidence,
)
from .evaluation import (
    RoutingEvaluationCase,
    RoutingEvaluationReport,
    evaluate_routing,
    routing_evaluation_cases,
    synthetic_routing_catalog,
)
from .selector import (
    ClaudeSkillSelector,
    CodexSkillSelector,
    CopilotSkillSelector,
    SelectionConversationTurn,
    SelectorResponseError,
    SelectorUnavailable,
    SkillRoutingEntry,
    SkillSelection,
    SkillSelectionEntry,
    SkillSelector,
    build_selection_prompt,
    build_selection_request,
    resolve_selector_name,
    selector_for,
)

__all__ = [
    "ONBOARDING_SKILL_NAME",
    "CanonicalCatalog",
    "CanonicalSkill",
    "ClaudeSkillSelector",
    "CodexSkillSelector",
    "CopilotSkillSelector",
    "DistributionPlan",
    "TeamSkillsError",
    "SkillRoutingEntry",
    "SkillSelection",
    "SkillSelectionEntry",
    "SkillSelector",
    "SelectorResponseError",
    "SelectorUnavailable",
    "SourceDescriptor",
    "TeamSkillsDistributionService",
    "TeamSkillsContextService",
    "TransientContextResult",
    "TransientContextSession",
    "RepositorySkillsEvidence",
    "RoutingEvaluationCase",
    "RoutingEvaluationReport",
    "SelectionConversationTurn",
    "build_selection_prompt",
    "build_selection_request",
    "find_repository",
    "repository_identity",
    "resolve_selector_name",
    "selector_for",
    "collect_skill_bootstrap_evidence",
    "collect_terminal_context_evidence",
    "evaluate_routing",
    "install_onboarding_skills",
    "onboarding_destinations",
    "onboarding_readiness",
    "onboarding_skill_text",
    "load_selector_preference",
    "preferences_path",
    "save_selector_preference",
    "routing_evaluation_cases",
    "synthetic_routing_catalog",
]
