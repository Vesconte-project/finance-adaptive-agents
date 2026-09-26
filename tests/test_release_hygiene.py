from __future__ import annotations

import tomllib
from pathlib import Path

from adaptive_agents import __version__
from adaptive_agents.team_skills.canonical import load_canonical_catalog
from adaptive_agents.team_skills.skill_quality import assessment_prompt
from adaptive_agents.team_skills.skill_validation import load_candidate


ROOT = Path(__file__).resolve().parents[1]


def test_distribution_version_and_product_metadata_are_consistent():
    project = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))["project"]

    assert project["name"] == "adaptive-agents"
    assert project["version"] == __version__ == "0.22.1"
    assert project["readme"] == "README.md"
    assert project["scripts"]["team-skills"] == (
        "adaptive_agents.team_skills.cli:main"
    )


def test_bundled_agent_skills_are_declared_as_wheel_package_data():
    configuration = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))

    assert configuration["tool"]["setuptools"]["package-data"][
        "adaptive_agents.team_skills"
    ] == ["skill_template/*/SKILL.md"]


def test_canonical_skill_catalog_is_safe_and_portable():
    catalog = load_canonical_catalog(
        ROOT / "team-skills",
        "test-source-commit",
        lambda _path: "test-skill-revision",
    )

    assert [(skill.id, skill.name, skill.state) for skill in catalog.skills] == [
        ("agent-operating-agreement", "agent-operating-agreement", "active"),
        ("canonical-team-skill-authoring", "canonical-team-skill-authoring", "active"),
        ("cloudflare-r2-backups-and-bucket-lock", "cloudflare-r2-backups-and-bucket-lock", "active"),
        ("deploy-outcome-visibility", "deploy-outcome-visibility", "active"),
        ("diagnose-host-failures", "diagnose-host-failures", "active"),
        ("dify-workflow-operations", "dify-workflow-operations", "active"),
        ("effective-config-tracing", "effective-config-tracing", "active"),
        ("finance-production-release-channel", "finance-production-release-channel", "active"),
        ("greenfield-host-setup", "greenfield-host-setup", "active"),
        ("guards-that-pass-blindly", "guards-that-pass-blindly", "active"),
        ("healthchecks-io-job-alerting", "healthchecks-io-job-alerting", "active"),
        ("host-mutation-batches", "host-mutation-batches", "active"),
        ("immutable-deploys-single-host", "immutable-deploys-single-host", "active"),
        ("jira-data-center-operations", "jira-data-center-operations", "active"),
        ("lets-encrypt-dns01-octodns-renewal", "lets-encrypt-dns01-octodns-renewal", "active"),
        ("openssh-socket-activation-listeners", "openssh-socket-activation-listeners", "active"),
        ("orchestrator-runtime-ops", "orchestrator-runtime-ops", "active"),
        ("prefect-self-hosted-operations", "prefect-self-hosted-operations", "active"),
        ("privilege-boundaries-ci-runner", "privilege-boundaries-ci-runner", "active"),
        ("stateful-service-migrations", "stateful-service-migrations", "active"),
        (
            "systemd-root-units-and-sandbox-pitfalls",
            "systemd-root-units-and-sandbox-pitfalls",
            "active",
        ),
        (
            "systemd-service-exit-and-oom-semantics",
            "systemd-service-exit-and-oom-semantics",
            "active",
        ),
        ("verify-against-the-host", "verify-against-the-host", "active"),
    ]
    skills = {skill.name: skill for skill in catalog.skills}
    assert catalog.descriptor.organization == "Vesconte-project"
    assert catalog.descriptor.organization_default_skill_ids == (
        "finance-production-release-channel",
    )
    assert catalog.descriptor.organization_only_skill_ids == (
        "finance-production-release-channel",
    )
    assert catalog.by_id()["finance-production-release-channel"].organization_scope == "Vesconte-project"
    finance_candidate = load_candidate(
        ROOT / "team-skills/skills/finance-production-release-channel",
        organization_scope="Vesconte-project",
    )
    finance_assessment = assessment_prompt(finance_candidate)
    assert '"intended_audience":"organization-only for Vesconte-project"' in finance_assessment
    assert "do not require generic applicability outside that organization" in finance_assessment
    renewal = skills["lets-encrypt-dns01-octodns-renewal"]
    assert "Let's Encrypt" in renewal.description
    assert "private key" in renewal.skill_text.lower()
    for skill in catalog.skills:
        assert "CLOUDFLARE_TOKEN" not in skill.skill_text
        assert "/home/user/" not in skill.skill_text
        assert "BEGIN PRIVATE KEY" not in skill.skill_text
    authoring = skills["canonical-team-skill-authoring"]
    assert "progressive references" in authoring.skill_text
    assert "revocation" in authoring.skill_text
    assert "research-and-refresh.md" in authoring.skill_text
    authoring_contract = (
        ROOT
        / "team-skills/skills/canonical-team-skill-authoring/references/evidence-and-lifecycle.md"
    ).read_text(encoding="utf-8")
    assert "schema_version" in authoring_contract
    assert "package digest" in authoring_contract
    dify = skills["dify-workflow-operations"]
    assert "Workspace-dependent" in dify.skill_text
    assert "trace-repair.md" in dify.skill_text
    assert "structured-output-and-effects.md" in dify.skill_text
    assert "unknown outcome" in dify.skill_text
    jira = skills["jira-data-center-operations"]
    assert "unknown outcome" in jira.skill_text
    assert "workflow-transitions.md" in jira.skill_text
