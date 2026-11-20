from __future__ import annotations

import copy
import json
import subprocess
from pathlib import Path
from types import SimpleNamespace

import pytest

from finance_adaptive_agents.team_skills import authoring as author
from finance_adaptive_agents.team_skills import cli
from finance_adaptive_agents.team_skills.consumer import ConsumerSource
from finance_adaptive_agents.team_skills.repository import TeamSkillsError
from finance_adaptive_agents.team_skills.skill_quality import SkillAssessment


def git(root, *args):
    return subprocess.run(["git", "-C", str(root), *args], check=True,
                          capture_output=True, text=True).stdout.strip()


@pytest.fixture
def catalog(tmp_path, monkeypatch):
    monkeypatch.setenv("TEAM_SKILLS_HOME", str(tmp_path / "machine"))
    root = tmp_path / "project"
    source = tmp_path / "canonical"
    for path in [root, source]:
        path.mkdir()
        git(path, "init", "-q", "-b", "main")
        git(path, "config", "user.name", "Test")
        git(path, "config", "user.email", "test@example.invalid")
    (source / "team-skills.json").write_text(json.dumps({
        "schema_version": 1, "source_id": "test", "organization": "", "team": "engineering",
    }))
    skill = source / "skills" / "dns"
    skill.mkdir(parents=True)
    (skill / "team-skills.json").write_text(json.dumps({"schema_version": 1, "id": "dns", "state": "active"}))
    (skill / "SKILL.md").write_text("---\nname: dns\ndescription: Use for DNS operations.\n---\n\nReview DNS changes.\n")
    git(source, "add", ".")
    git(source, "-c", "commit.gpgsign=false", "commit", "-qm", "Initial catalog")
    return root, source, ConsumerSource("../canonical", "main", ".")


def decision(kind="create", skill_id=None):
    return {"decision": kind, "skill_id": skill_id, "summary": "Reusable verified practice.", "missing_evidence": []}


def package(name="backup-proof", body="Verify the restore in a disposable database before relying on it."):
    return {"files": [{"path": "SKILL.md", "content":
        f"---\nname: {name}\ndescription: Use when proving a logical backup can be restored.\n---\n\n{body}\n"}]}


READY = SkillAssessment("ready", "Suitable for review.", (), (), "Restore a backup.", "Tune query performance.")


def models(monkeypatch, first=None, second=None, assessment=READY):
    requests = []
    responses = iter([first or decision(), second or package()])
    def invoke(provider, request, schema):
        requests.append((provider, copy.deepcopy(request), schema))
        response = next(responses)
        if schema is author.PACKAGE_SCHEMA and set(response) == {"files"}:
            response = dict(response, decision="write", summary="Verified lesson.", missing_evidence=[])
        return response
    monkeypatch.setattr(author, "invoke_author", invoke)
    assessments = []
    def assess(provider, candidate):
        assessments.append((provider, candidate.files))
        return assessment
    monkeypatch.setattr(author, "assess_candidate", assess)
    return requests, assessments


def test_create_preserves_complete_context_and_requires_independent_assessment(catalog, monkeypatch, tmp_path):
    root, source, config = catalog
    primary = tmp_path / "handoff.md"
    primary.write_text("Objective and failed attempts\n" + "evidence " * 1500 + "TAIL-EVIDENCE")
    attachment = tmp_path / "proof.txt"
    attachment.write_text("Verified restore trace, version and limitations.")
    documents = author.read_context((primary, attachment))
    requests, assessments = models(monkeypatch)
    before = git(source, "rev-parse", "HEAD")
    result = author.propose_from_context(root, config, documents, "codex")
    assert result.decision == "create"
    assert result.prepared.kind == "addition"
    assert result.assessment is READY
    for _, request, _ in requests:
        assert request["context_documents"] == documents
        assert request["context_documents"][0]["content"].endswith("TAIL-EVIDENCE")
    assert len(assessments) == 1
    assert assessments[0][1] == (("SKILL.md", package()["files"][0]["content"].encode()),)
    assert git(source, "rev-parse", "HEAD") == before
    assert git(result.prepared.checkout, "rev-parse", "HEAD") == before
    assert (result.prepared.checkout / "skills/backup-proof/team-skills.json").exists()
    assert not (root / ".team-skills").exists()
    assert not (root / ".agents").exists()
    assert not (root / ".claude").exists()
    assert "TAIL-EVIDENCE" not in result.prepared.diff
    assert result.draft_path.exists()
    assert not any("TAIL-EVIDENCE" in p.read_text() for p in result.draft_path.parent.rglob("*") if p.is_file())


def test_update_can_target_online_skill_without_installing_it(catalog, monkeypatch):
    root, _, config = catalog
    requests, _ = models(monkeypatch, decision("update", "dns"), package("dns"))
    result = author.propose_from_context(root, config, ({"label": "handoff", "content": "DNS lesson"},), "claude")
    assert result.prepared.kind == "update"
    assert requests[1][1]["baseline"]["id"] == "dns"
    assert "Review DNS changes." in requests[1][1]["baseline"]["files"]["SKILL.md"]
    assert json.loads((result.prepared.checkout / "skills/dns/team-skills.json").read_text())["id"] == "dns"
    assert not (root / ".team-skills").exists()


@pytest.mark.parametrize("kind,missing", [("no_change", []), ("needs_evidence", ["Provide the observed failure and verification."])])
def test_no_candidate_when_author_declines_or_requests_evidence(catalog, monkeypatch, kind, missing):
    root, _, config = catalog
    first = dict(decision(kind), missing_evidence=missing)
    requests, assessments = models(monkeypatch, first)
    monkeypatch.setattr(author, "prepare_authored", lambda *a, **k: pytest.fail("must not prepare a checkout"))
    result = author.propose_from_context(root, config, ({"label": "handoff", "content": "lesson"},), "codex")
    assert result.decision == kind and result.missing_evidence == tuple(missing)
    assert len(requests) == 1 and not assessments
    assert not (root / ".team-skills").exists()


@pytest.mark.parametrize("skill_id", ["unknown", "revoked", "private"])
def test_native_admission_rejects_unknown_revoked_and_wrong_organization(catalog, monkeypatch, skill_id):
    root, source, config = catalog
    if skill_id != "unknown":
        skill = source / "skills" / skill_id
        skill.mkdir()
        (skill / "team-skills.json").write_text(json.dumps({
            "schema_version": 1, "id": skill_id, "state": "revoked" if skill_id == "revoked" else "active",
        }))
        (skill / "SKILL.md").write_text(f"---\nname: {skill_id}\ndescription: Scoped operations.\n---\n\nReview changes.\n")
        if skill_id == "private":
            (source / "team-skills.json").write_text(json.dumps({
                "schema_version": 2, "source_id": "test", "organization": "Other-company",
                "team": "engineering", "organization_only_skill_ids": ["private"],
            }))
        git(source, "add", ".")
        git(source, "-c", "commit.gpgsign=false", "commit", "-qm", "Add scoped resource")
    requests, assessments = models(monkeypatch, decision("update", skill_id))
    with pytest.raises(TeamSkillsError, match="inadmissible"):
        author.propose_from_context(root, config, ({"label": "handoff", "content": "lesson"},), "codex")
    assert skill_id not in [item["id"] for item in requests[0][1]["available_skills"]]
    assert len(requests) == 1 and not assessments


@pytest.mark.parametrize("path", ["../escape.md", "/tmp/escape.md", "references/../../escape.md", "scripts/a.md", "references/a.py", "team-skills.json", "proposal.json", "references/./a.md", "references/a\x00.md"])
def test_untrusted_generated_paths_never_reach_evaluator_or_checkout(catalog, monkeypatch, path):
    root, _, config = catalog
    second = package()
    second["files"].append({"path": path, "content": "bad"})
    _, assessments = models(monkeypatch, second=second)
    with pytest.raises(TeamSkillsError, match="unsafe|invalid portable"):
        author.propose_from_context(root, config, ({"label": "handoff", "content": "lesson"},), "codex")
    assert not assessments


@pytest.mark.parametrize("second", [package("dns"), {"files": []}, {"files": package()["files"] * 2}, package(body="Authorization: Bearer secret")])
def test_invalid_conflicting_or_unsafe_candidate_stops_before_assessment(catalog, monkeypatch, second):
    root, _, config = catalog
    _, assessments = models(monkeypatch, second=second)
    with pytest.raises(TeamSkillsError):
        author.propose_from_context(root, config, ({"label": "handoff", "content": "lesson"},), "codex")
    assert not assessments


def test_failed_independent_review_does_not_prepare_checkout(catalog, monkeypatch):
    root, _, config = catalog
    review = SkillAssessment("needs_revision", "Too broad.", ("Narrow the trigger.",), (), "Example", "Other")
    models(monkeypatch, assessment=review)
    monkeypatch.setattr(author, "prepare_authored", lambda *a, **k: pytest.fail("must not prepare a checkout"))
    result = author.propose_from_context(root, config, ({"label": "handoff", "content": "lesson"},), "codex")
    assert result.decision == "needs_revision" and result.prepared is None
    assert result.draft_path.exists()


def test_catalog_change_during_authoring_requires_fresh_proposal(catalog, monkeypatch):
    root, source, config = catalog
    models(monkeypatch)
    def assess(provider, candidate):
        (source / "skills/dns/SKILL.md").write_text((source / "skills/dns/SKILL.md").read_text() + "New evidence.\n")
        git(source, "add", ".")
        git(source, "-c", "commit.gpgsign=false", "commit", "-qm", "Concurrent update")
        return READY
    monkeypatch.setattr(author, "assess_candidate", assess)
    with pytest.raises(TeamSkillsError, match="changed during authorship"):
        author.propose_from_context(root, config, ({"label": "handoff", "content": "lesson"},), "codex")


def test_context_inputs_fail_explicitly_without_truncation(tmp_path, monkeypatch):
    path = tmp_path / "context.md"
    path.write_text("z" * 11)
    monkeypatch.setattr(author, "MAX_CONTEXT_BYTES", 10)
    with pytest.raises(TeamSkillsError, match="nothing was truncated or sent"):
        author.read_context((path,))
    path.write_bytes(b"\xff")
    with pytest.raises(TeamSkillsError, match="UTF-8"):
        author.read_context((path,))
    path.write_text("")
    with pytest.raises(TeamSkillsError, match="empty"):
        author.read_context((path,))
    path.unlink()
    path.symlink_to(tmp_path / "other")
    with pytest.raises(TeamSkillsError, match="symlinks"):
        author.read_context((path,))


@pytest.mark.parametrize("provider", ["codex", "claude", "copilot"])
def test_isolated_provider_receives_full_prompt_on_stdin_and_errors_do_not_echo_it(monkeypatch, provider):
    calls = []
    def run(command, **kwargs):
        calls.append((command, kwargs))
        if command[0] == "git":
            return SimpleNamespace(returncode=0)
        return SimpleNamespace(returncode=1, stdout="PRIVATE HANDOFF", stderr="PRIVATE HANDOFF")
    monkeypatch.setattr(author.subprocess, "run", run)
    with pytest.raises(TeamSkillsError) as error:
        author.invoke_author(provider, {"evidence": "PRIVATE HANDOFF"}, author.DECISION_SCHEMA)
    command, kwargs = calls[-1]
    assert "PRIVATE HANDOFF" in kwargs["input"]
    assert "PRIVATE HANDOFF" not in " ".join(command)
    assert "PRIVATE HANDOFF" not in str(error.value)
    assert kwargs["cwd"] != Path.cwd()


def test_cli_context_authorship_never_runs_machine_setup(catalog, tmp_path, monkeypatch, capsys):
    root, _, _ = catalog
    handoff = tmp_path / "handoff.md"
    handoff.write_text("Complete context")
    monkeypatch.setattr(cli, "_ensure_first_run_setup", lambda *a: pytest.fail("must not install onboarding"))
    received = []
    def propose(*args, **kwargs):
        received.append(args)
        return author.AuthoringResult("no_change", "No transferable learning.", (), "abc", False)
    monkeypatch.setattr(cli, "propose_from_context", propose)
    assert cli.main(["propose", "--repo", str(root), "--context-file", str(handoff), "--source", "../canonical"]) == 0
    assert received[0][1].url == "../canonical"
    assert "No transferable learning." in capsys.readouterr().out
    assert not (root / ".team-skills").exists()


def test_context_mode_rejects_legacy_identity_options_before_any_model_call(catalog, tmp_path, monkeypatch):
    root, _, _ = catalog
    handoff = tmp_path / "handoff.md"
    handoff.write_text("Complete context")
    monkeypatch.setattr(cli, "propose_from_context", lambda *a, **k: pytest.fail("must not invoke author"))
    assert cli.main(["propose", "--repo", str(root), "--context-file", str(handoff), "--new"]) == 2


@pytest.mark.parametrize("provider", ["codex", "claude", "copilot"])
def test_provider_success_decodes_structured_response_without_echoing_context(monkeypatch, provider):
    response = decision("no_change")
    def run(command, **kwargs):
        if command[0] == "git":
            return SimpleNamespace(returncode=0)
        if provider == "codex":
            Path(command[command.index("--output-last-message") + 1]).write_text(json.dumps(response))
        stdout = json.dumps({"structured_output": response} if provider == "claude" else response)
        return SimpleNamespace(returncode=0, stdout=stdout, stderr="")
    monkeypatch.setattr(author.subprocess, "run", run)
    assert author.invoke_author(provider, {"evidence": "full context"}, author.DECISION_SCHEMA) == response


@pytest.mark.parametrize("kind,missing", [("no_change", []), ("needs_evidence", ["Need the actual trace."])])
def test_author_can_revise_decision_after_reading_existing_baseline(catalog, monkeypatch, kind, missing):
    root, _, config = catalog
    requests, assessments = models(monkeypatch, decision("update", "dns"), {
        "decision": kind, "summary": "After inspecting baseline.", "missing_evidence": missing, "files": [],
    })
    result = author.propose_from_context(root, config, ({"label": "handoff", "content": "lesson"},), "codex")
    assert result.decision == kind and result.missing_evidence == tuple(missing)
    assert requests[1][1]["baseline"]["id"] == "dns"
    assert not assessments


def test_reused_proposal_must_preserve_reviewed_active_lifecycle(catalog, monkeypatch):
    root, _, config = catalog
    documents = ({"label": "handoff", "content": "lesson"},)
    models(monkeypatch)
    result = author.propose_from_context(root, config, documents, "codex")
    sidecar = result.prepared.checkout / "skills/backup-proof/team-skills.json"
    value = json.loads(sidecar.read_text())
    value["state"] = "revoked"
    sidecar.write_text(json.dumps(value))
    models(monkeypatch)
    with pytest.raises(TeamSkillsError, match="does not match the validated candidate"):
        author.propose_from_context(root, config, documents, "codex")
    assert json.loads(sidecar.read_text())["state"] == "revoked"


def test_repeated_identical_proposal_can_reuse_only_its_exact_reviewed_checkout(catalog, monkeypatch):
    root, _, config = catalog
    documents = ({"label": "handoff", "content": "lesson"},)
    models(monkeypatch)
    first = author.propose_from_context(root, config, documents, "codex")
    models(monkeypatch)
    second = author.propose_from_context(root, config, documents, "codex")
    assert second.prepared.checkout == first.prepared.checkout
    assert second.prepared.reused


def test_unavailable_assessment_preserves_native_valid_draft_without_publishing(catalog, monkeypatch):
    root, _, config = catalog
    models(monkeypatch)
    def unavailable(*args):
        raise TeamSkillsError("provider unavailable")
    monkeypatch.setattr(author, "assess_candidate", unavailable)
    monkeypatch.setattr(author, "prepare_authored", lambda *a, **k: pytest.fail("must not prepare"))
    with pytest.raises(TeamSkillsError, match="assessment did not complete; draft preserved"):
        author.propose_from_context(root, config, ({"label": "handoff", "content": "lesson"},), "codex")
    reports = list((root.parent / "machine/data/authoring-drafts").rglob("assessment.json"))
    assert len(reports) == 1
    assert json.loads(reports[0].read_text())["status"] == "incomplete"
    assert (reports[0].parent / "candidate/SKILL.md").exists()
    assert not (root / ".team-skills").exists()
