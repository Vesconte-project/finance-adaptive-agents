"""Reproducible scale evaluation for model-owned Skill routing."""

from __future__ import annotations

import statistics
import time
from dataclasses import dataclass

from finance_adaptive_agents import __version__

from .evidence import collect_terminal_context_evidence
from .repository import TeamSkillsError
from .selector import (
    SkillRoutingEntry,
    SkillSelector,
    build_selection_prompt,
    build_selection_request,
)


_SUBJECTS = (
    ("jira-data-center", "Jira Data Center issues, workflows, nodes, and clustered services"),
    ("jira-cloud", "Jira Cloud issues, workflows, projects, and hosted services"),
    ("cloudflare-dns", "Cloudflare DNS zones, records, delegations, and resolvers"),
    ("cloudflare-waf", "Cloudflare WAF rules, managed rulesets, and request filtering"),
    ("kubernetes", "Kubernetes workloads, clusters, namespaces, and controllers"),
    ("helm", "Helm charts, releases, values, and repositories"),
    ("postgresql", "PostgreSQL databases, roles, replication, and SQL services"),
    ("mysql", "MySQL databases, users, replication, and SQL services"),
    ("redis", "Redis data structures, persistence, clusters, and caches"),
    ("kafka", "Apache Kafka topics, brokers, consumers, and streaming services"),
    ("github-actions", "GitHub Actions workflows, runners, jobs, and releases"),
    ("gitlab-ci", "GitLab CI pipelines, runners, jobs, and releases"),
    ("aws-iam", "AWS IAM identities, roles, policies, and permissions"),
    ("azure-entra", "Microsoft Entra identities, applications, roles, and permissions"),
    ("gcp-iam", "Google Cloud IAM principals, roles, policies, and permissions"),
    ("terraform", "Terraform modules, state, providers, and infrastructure plans"),
    ("ansible", "Ansible playbooks, inventories, roles, and managed hosts"),
    ("docker", "Docker images, containers, registries, and runtimes"),
    ("prometheus", "Prometheus metrics, rules, exporters, and alerting"),
    ("grafana", "Grafana dashboards, data sources, alerts, and visualizations"),
    ("elasticsearch", "Elasticsearch indices, mappings, clusters, and searches"),
    ("salesforce", "Salesforce objects, flows, permissions, and platform services"),
    ("servicenow", "ServiceNow records, workflows, catalog items, and platform services"),
    ("dify", "Dify applications, workflows, nodes, tools, and knowledge bases"),
    ("linux", "Linux hosts, services, packages, filesystems, and operating system facilities"),
)

_OPERATIONS = (
    ("api-automation", "automating {subject} through supported APIs and machine interfaces"),
    ("deployment", "deploying and releasing {subject} changes"),
    ("administration", "installing, configuring, upgrading, and administering {subject}"),
    ("security", "reviewing and hardening the security of {subject}"),
    ("incident-response", "diagnosing and responding to incidents involving {subject}"),
    ("backup-restore", "backing up and restoring {subject}"),
    ("migration", "planning and executing migrations involving {subject}"),
    ("observability", "monitoring, tracing, and measuring {subject}"),
)


@dataclass(frozen=True)
class RoutingEvaluationCase:
    id: str
    task: str
    expected_ids: tuple[str, ...]


@dataclass(frozen=True)
class RoutingCaseResult:
    case_id: str
    expected_ids: tuple[str, ...]
    selected_ids: tuple[str, ...]
    latency_seconds: float
    prompt_bytes: int
    estimated_prompt_tokens: int

    def to_data(self) -> dict[str, object]:
        expected = set(self.expected_ids)
        selected = set(self.selected_ids)
        return {
            "case_id": self.case_id,
            "expected_ids": list(self.expected_ids),
            "selected_ids": list(self.selected_ids),
            "true_positives": len(expected & selected),
            "false_positives": len(selected - expected),
            "false_negatives": len(expected - selected),
            "exact_match": expected == selected,
            "latency_seconds": round(self.latency_seconds, 6),
            "prompt_bytes": self.prompt_bytes,
            "estimated_prompt_tokens": self.estimated_prompt_tokens,
        }


@dataclass(frozen=True)
class RoutingEvaluationReport:
    selector_name: str
    catalog_size: int
    repeat: int
    results: tuple[RoutingCaseResult, ...]

    def to_data(self) -> dict[str, object]:
        rows = tuple(result.to_data() for result in self.results)
        selections_by_case: dict[str, set[frozenset[str]]] = {}
        for result in self.results:
            selections_by_case.setdefault(result.case_id, set()).add(
                frozenset(result.selected_ids)
            )
        true_positives = sum(int(row["true_positives"]) for row in rows)
        false_positives = sum(int(row["false_positives"]) for row in rows)
        false_negatives = sum(int(row["false_negatives"]) for row in rows)
        precision_denominator = true_positives + false_positives
        recall_denominator = true_positives + false_negatives
        precision = true_positives / precision_denominator if precision_denominator else 1.0
        recall = true_positives / recall_denominator if recall_denominator else 1.0
        f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
        latencies = [result.latency_seconds for result in self.results]
        close_neighbour_entries = min(self.catalog_size, len(_SUBJECTS) * len(_OPERATIONS))
        return {
            "schema_version": 1,
            "tool_version": __version__,
            "selector": self.selector_name,
            "catalog_size": self.catalog_size,
            "repeat": self.repeat,
            "case_runs": len(rows),
            "fixture": {
                "close_neighbour_entries": close_neighbour_entries,
                "neutral_distractor_entries": self.catalog_size - close_neighbour_entries,
            },
            "prompt_token_estimate": "UTF-8 bytes divided by four, rounded up",
            "summary": {
                "precision": round(precision, 6),
                "recall": round(recall, 6),
                "f1": round(f1, 6),
                "exact_match_rate": round(
                    sum(bool(row["exact_match"]) for row in rows) / len(rows), 6
                ),
                "selection_stability_rate": (
                    round(
                        sum(len(selections) == 1 for selections in selections_by_case.values())
                        / len(selections_by_case),
                        6,
                    )
                    if self.repeat > 1
                    else None
                ),
                "latency_p50_seconds": round(statistics.median(latencies), 6),
                "latency_max_seconds": round(max(latencies), 6),
                "max_prompt_bytes": max(result.prompt_bytes for result in self.results),
                "max_estimated_prompt_tokens": max(
                    result.estimated_prompt_tokens for result in self.results
                ),
            },
            "results": list(rows),
        }


def synthetic_routing_catalog(size: int = 200) -> tuple[SkillRoutingEntry, ...]:
    """Build 200 close neighbours plus neutral scale distractors, without packages."""

    if size < 200 or size > 2_000:
        raise TeamSkillsError("routing evaluation catalog size must be between 200 and 2,000")
    skills = [
        SkillRoutingEntry(
            f"eval.{subject_id}.{operation_id}",
            f"{subject_id}-{operation_id}",
            "Use when " + template.format(subject=subject_description) + ".",
        )
        for subject_id, subject_description in _SUBJECTS
        for operation_id, template in _OPERATIONS
    ]
    for index in range(size - len(skills)):
        family = index % 25
        variant = index // 25
        skills.append(
            SkillRoutingEntry(
                f"eval.synthetic-platform-{family:02d}.workflow-{variant:02d}",
                f"synthetic-platform-{family:02d}-workflow-{variant:02d}",
                "Use for lifecycle workflow "
                f"{variant:02d} on synthetic enterprise platform {family:02d}; "
                "this is a scale-only distractor.",
            )
        )
    return tuple(skills)


def routing_evaluation_cases() -> tuple[RoutingEvaluationCase, ...]:
    return (
        RoutingEvaluationCase(
            "jira-issue-api-not-server-admin",
            "Use the Jira Data Center REST API to create issues and transition their workflows.",
            ("eval.jira-data-center.api-automation",),
        ),
        RoutingEvaluationCase(
            "jira-cluster-administration",
            "Upgrade and administer the nodes of our Jira Data Center cluster.",
            ("eval.jira-data-center.administration",),
        ),
        RoutingEvaluationCase(
            "cloudflare-dns-change",
            "Configure and administer Cloudflare DNS records and zone delegations.",
            ("eval.cloudflare-dns.administration",),
        ),
        RoutingEvaluationCase(
            "cloudflare-waf-incident",
            "Diagnose a production incident where a Cloudflare WAF rule blocks valid requests.",
            ("eval.cloudflare-waf.incident-response",),
        ),
        RoutingEvaluationCase(
            "postgres-restore",
            "Restore a PostgreSQL database from its verified backup.",
            ("eval.postgresql.backup-restore",),
        ),
        RoutingEvaluationCase(
            "cross-database-migration",
            "Plan and execute a migration from MySQL to PostgreSQL.",
            ("eval.mysql.migration", "eval.postgresql.migration"),
        ),
        RoutingEvaluationCase(
            "kubernetes-deploy-and-observe",
            "Deploy a Kubernetes workload and add monitoring for that workload.",
            ("eval.kubernetes.deployment", "eval.kubernetes.observability"),
        ),
        RoutingEvaluationCase(
            "aws-permission-review",
            "Review and harden AWS IAM role permissions.",
            ("eval.aws-iam.security",),
        ),
        RoutingEvaluationCase(
            "dify-api-workflow",
            "Automate creation of Dify workflows through the supported API.",
            ("eval.dify.api-automation",),
        ),
        RoutingEvaluationCase(
            "negative-construction-task",
            "Design a masonry wall and calculate how many bricks are required.",
            (),
        ),
    )


def evaluate_routing(
    selector: SkillSelector,
    *,
    selector_name: str,
    catalog_size: int = 200,
    repeat: int = 1,
    max_cases: int | None = None,
) -> RoutingEvaluationReport:
    if repeat < 1 or repeat > 10:
        raise TeamSkillsError("routing evaluation repeat must be between 1 and 10")
    if max_cases is not None and (max_cases < 1 or max_cases > len(routing_evaluation_cases())):
        raise TeamSkillsError("routing evaluation max cases is outside the available case range")
    skills = synthetic_routing_catalog(catalog_size)
    evidence = collect_terminal_context_evidence()
    cases = routing_evaluation_cases()[:max_cases]
    results: list[RoutingCaseResult] = []
    for _iteration in range(repeat):
        for case in cases:
            request = build_selection_request(evidence, skills, task=case.task)
            prompt_bytes = len(build_selection_prompt(request).encode("utf-8"))
            started = time.perf_counter()
            selection = selector.select(evidence, skills, task=case.task)
            elapsed = time.perf_counter() - started
            results.append(
                RoutingCaseResult(
                    case.id,
                    case.expected_ids,
                    tuple(item.id for item in selection.selected),
                    elapsed,
                    prompt_bytes,
                    (prompt_bytes + 3) // 4,
                )
            )
    return RoutingEvaluationReport(selector_name, catalog_size, repeat, tuple(results))
