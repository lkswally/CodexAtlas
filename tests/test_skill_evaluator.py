import os
from pathlib import Path

os.environ["ATLAS_DISABLE_EVENT_LOGS"] = "1"

from tests._support_paths import ATLAS_ROOT, WEB_ROOT, create_governed_web_fixture
from tools.atlas_dispatcher import dispatch
from tools.skill_evaluator import evaluate_skill_candidate



def test_skill_evaluator_rejects_candidate_that_overlaps_existing_skill():
    result = evaluate_skill_candidate(
        root=ATLAS_ROOT,
        candidate_name="design-system-review-plus",
        problem_statement="Need a reusable design system review skill for landing QA and typography checks.",
        project=WEB_ROOT,
    )
    assert result["status"] == "ok"
    assert result["overlapping_skills"]
    assert result["should_create"] is False
    assert result["recommended_state"] == "rejected"
    assert result["lifecycle_recommendation"] == "reject_candidate"
    assert result["duplication_risk"] == "high"


def test_skill_evaluator_can_detect_cross_project_need_without_overlap():
    result = evaluate_skill_candidate(
        root=ATLAS_ROOT,
        candidate_name="context-window-guidance",
        problem_statement="Need a reusable factory-wide guidance skill for cross-project context refresh and repeatable iteration prompts.",
        project=WEB_ROOT,
    )
    assert result["status"] == "ok"
    assert result["reuse_potential"] in {"medium", "high"}
    assert isinstance(result["need_score"], int)
    assert isinstance(result["should_create"], bool)
    assert result["recommended_state"] in {"candidate", "experimental"}
    assert "lifecycle_recommendation" in result
    assert "why" in result


def test_skill_evaluator_promotes_candidate_to_experimental_when_gap_is_reusable_and_safe():
    result = evaluate_skill_candidate(
        root=ATLAS_ROOT,
        candidate_name="skill-lifecycle-review",
        problem_statement="Need a reusable factory-wide governance workflow skill for cross-project skill lifecycle review, repeatable promotion guidance and catalog hygiene.",
        project=WEB_ROOT,
    )
    assert result["status"] == "ok"
    assert result["recommended_state"] == "experimental"
    assert result["lifecycle_recommendation"] == "promote_to_experimental"
    assert result["requires_human_approval"] is True
    assert result["promotion_blockers"] == []


def test_skill_evaluator_keeps_high_dependency_candidate_in_watchlist_like_state():
    result = evaluate_skill_candidate(
        root=ATLAS_ROOT,
        candidate_name="playwright-visual-runtime-skill",
        problem_statement="Need a reusable MCP Playwright runtime skill with browser automation, install flow, sync logic and external service coordination for cross-project UI checks.",
        project=WEB_ROOT,
    )
    assert result["status"] == "ok"
    assert result["recommended_state"] == "candidate"
    assert result["lifecycle_recommendation"] == "watchlist_only"
    assert result["external_dependency_risk"] == "high"
    assert result["requires_human_approval"] is True


def test_skill_evaluator_requires_decision_council_for_high_risk_skill():
    result = evaluate_skill_candidate(
        root=ATLAS_ROOT,
        candidate_name="autonomous-mcp-runtime-skill",
        problem_statement="Need a reusable autonomous MCP runtime install and sync skill for cross-project agent fleet routing with self-heal behavior.",
        project=WEB_ROOT,
    )
    assert result["status"] == "ok"
    assert result["requires_decision_council"] is True
    assert result["external_dependency_risk"] == "high"
    assert result["complexity"] == "high"


def test_dispatcher_exposes_skill_evaluator(tmp_path):
    project = create_governed_web_fixture(tmp_path / "web-project")
    result = dispatch(
        "skill-evaluator",
        root=ATLAS_ROOT,
        project=project,
        candidate="design-system-review-plus",
        problem="Need a reusable design system review skill for landing QA and typography checks.",
    )
    assert result.ok is True
    assert result.output["result"]["status"] == "ok"
    assert "need_score" in result.output["result"]
    assert "recommended_state" in result.output["result"]
    assert "lifecycle_recommendation" in result.output["result"]
