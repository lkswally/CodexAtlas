import os
from pathlib import Path

os.environ["ATLAS_DISABLE_EVENT_LOGS"] = "1"

from tools.atlas_dispatcher import dispatch
from tools.skill_evaluator import evaluate_skill_candidate


ATLAS_ROOT = Path(r"C:\Proyectos\Codex-Atlas")
WEB_ROOT = Path(r"C:\Proyectos\CodexAtlas-Web")


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


def test_dispatcher_exposes_skill_evaluator():
    result = dispatch(
        "skill-evaluator",
        root=ATLAS_ROOT,
        project=WEB_ROOT,
        candidate="design-system-review-plus",
        problem="Need a reusable design system review skill for landing QA and typography checks.",
    )
    assert result.ok is True
    assert result.output["result"]["status"] == "ok"
    assert "need_score" in result.output["result"]
