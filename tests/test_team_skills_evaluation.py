from __future__ import annotations

from adaptive_agents.team_skills.evaluation import (
    evaluate_routing,
    routing_evaluation_cases,
    synthetic_routing_catalog,
)
from adaptive_agents.team_skills.selector import SkillSelection, SkillSelectionEntry


class ExpectedSelectionStub:
    def select(self, evidence, skills, *, task=None):
        expected = {
            case.task: case.expected_ids for case in routing_evaluation_cases()
        }[task]
        return SkillSelection(
            tuple(SkillSelectionEntry(skill_id, "Expected by the public fixture.") for skill_id in expected)
        )


class UnstableSelectionStub:
    def __init__(self) -> None:
        self.calls = 0

    def select(self, evidence, skills, *, task=None):
        case_count = len(routing_evaluation_cases())
        iteration = self.calls // case_count
        self.calls += 1
        expected = {
            case.task: case.expected_ids for case in routing_evaluation_cases()
        }[task]
        selected = expected if iteration == 0 else (*expected, "eval.linux.security")
        return SkillSelection(tuple(SkillSelectionEntry(skill_id) for skill_id in selected))


def test_synthetic_catalog_has_200_unique_close_neighbours() -> None:
    catalog = synthetic_routing_catalog()

    assert len(catalog) == 200
    assert len({entry.id for entry in catalog}) == 200
    assert "eval.jira-data-center.api-automation" in {entry.id for entry in catalog}
    assert "eval.jira-data-center.administration" in {entry.id for entry in catalog}
    assert "eval.cloudflare-dns.administration" in {entry.id for entry in catalog}
    assert "eval.cloudflare-waf.administration" in {entry.id for entry in catalog}


def test_routing_evaluation_reports_quality_latency_and_prompt_size() -> None:
    report = evaluate_routing(ExpectedSelectionStub(), selector_name="test-stub").to_data()

    assert report["catalog_size"] == 200
    assert report["selector"] == "test-stub"
    assert report["tool_version"]
    assert report["fixture"] == {"close_neighbour_entries": 200, "neutral_distractor_entries": 0}
    assert report["case_runs"] == len(routing_evaluation_cases())
    assert report["summary"]["precision"] == 1.0
    assert report["summary"]["recall"] == 1.0
    assert report["summary"]["f1"] == 1.0
    assert report["summary"]["exact_match_rate"] == 1.0
    assert report["summary"]["selection_stability_rate"] is None
    assert report["summary"]["max_prompt_bytes"] > 10_000
    assert report["summary"]["max_estimated_prompt_tokens"] > 2_500
    assert all("latency_seconds" in result for result in report["results"])


def test_routing_evaluation_can_run_a_bounded_smoke_test() -> None:
    report = evaluate_routing(ExpectedSelectionStub(), selector_name="test-stub", catalog_size=250, max_cases=2).to_data()

    assert report["catalog_size"] == 250
    assert report["fixture"] == {"close_neighbour_entries": 200, "neutral_distractor_entries": 50}
    assert report["case_runs"] == 2


def test_routing_evaluation_measures_instability_only_across_repetitions() -> None:
    report = evaluate_routing(UnstableSelectionStub(), selector_name="unstable-stub", repeat=2).to_data()

    assert report["summary"]["selection_stability_rate"] == 0.0
