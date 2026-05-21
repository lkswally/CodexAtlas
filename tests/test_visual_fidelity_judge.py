import os
from pathlib import Path

os.environ["ATLAS_DISABLE_EVENT_LOGS"] = "1"

from tests._support_paths import ATLAS_ROOT
from tools.visual_fidelity_judge import assess_visual_fidelity_judge

FIXTURES = ATLAS_ROOT / "tests" / "fixtures" / "visual_fidelity"

def _base_payload():
    return {
        "project_type": "frontend_app",
        "visual_intent_contract_review": {"status": "ready"},
        "brand_profile_review": {"status": "ready"},
        "ui_pre_return_review": {"status": "pass"},
        "design_quality_review": {"status": "ready"},
    }


def test_visual_fidelity_judge_requires_screenshot_backed_evidence():
    project = FIXTURES / "empty"
    result = assess_visual_fidelity_judge(_base_payload(), root=ATLAS_ROOT, project=project)

    assert result["fidelity_state"] == "insufficient_evidence"
    assert result["must_not_claim_visual_pass_without_evidence"] is True
    assert "desktop" in result["missing_viewports"]
    assert "mobile" in result["missing_viewports"]


def test_visual_fidelity_judge_marks_aligned_when_report_and_viewports_are_present():
    project = FIXTURES / "aligned"
    result = assess_visual_fidelity_judge(_base_payload(), root=ATLAS_ROOT, project=project)

    assert result["fidelity_state"] == "aligned"
    assert result["can_support_visual_pass"] is True
    assert result["missing_viewports"] == []
    assert result["missing_compared_layers"] == []


def test_visual_fidelity_judge_detects_drift_from_structured_report():
    project = FIXTURES / "drift"
    result = assess_visual_fidelity_judge(_base_payload(), root=ATLAS_ROOT, project=project)

    assert result["fidelity_state"] == "drift_detected"
    assert result["can_support_visual_pass"] is False
    assert result["drift_signals"]


def test_visual_fidelity_judge_keeps_insufficient_evidence_for_weak_report():
    project = FIXTURES / "weak"
    result = assess_visual_fidelity_judge(_base_payload(), root=ATLAS_ROOT, project=project)

    assert result["fidelity_state"] == "insufficient_evidence"
    assert "brand_profile" in result["missing_compared_layers"]
    assert result["can_support_visual_pass"] is False
