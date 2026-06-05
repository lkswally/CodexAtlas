from pathlib import Path
from unittest.mock import patch

from tests._support_paths import ATLAS_ROOT
from tools.frontend_visual_execution_guard import assess_frontend_visual_execution_guard


def _base_payload():
    return {
        "project_type": "landing_page",
        "visual_intent_contract": {
            "audience": "founders",
            "problem_or_promise": "clear product landing",
            "mood_or_vibe": "premium",
            "originality_level": "distinctive",
            "hero_direction": "focused product proof",
            "typography_intent": "modern readable",
            "color_strategy": "brand-led palette",
        },
        "design_references": ["reference-a"],
        "responsive_checkpoints": ["mobile", "desktop"],
        "provided_evidence": ["browser_qa", "screenshot_desktop", "screenshot_mobile"],
        "design_quality_review": {"ready_for_handoff": True, "status": "ok"},
    }


def test_landing_with_build_ok_but_without_visual_qa_needs_visual_review():
    payload = _base_payload()
    payload["provided_evidence"] = ["build_ok"]

    result = assess_frontend_visual_execution_guard(payload, root=ATLAS_ROOT)

    assert result["state"] == "needs_visual_review"
    assert result["browser_qa_present"] is False
    assert "missing_browser_or_screenshot_qa" in result["blocked_reasons"]


def test_motion_promised_without_validation_blocks_motion_handoff():
    payload = _base_payload()
    payload["source_text"] = "Hero has scroll-scrub video animation."

    result = assess_frontend_visual_execution_guard(payload, root=ATLAS_ROOT)

    assert result["state"] == "blocked_motion_unverified"
    assert result["motion_requirements_detected"] is True
    assert result["motion_validated"] is False


def test_mobile_first_absent_needs_visual_review():
    payload = _base_payload()
    payload["responsive_checkpoints"] = []
    payload["provided_evidence"] = ["browser_qa", "screenshot_desktop", "screenshot_mobile"]

    result = assess_frontend_visual_execution_guard(payload, root=ATLAS_ROOT)

    assert result["state"] == "needs_visual_review"
    assert "missing_mobile_first_checkpoints" in result["blocked_reasons"]


def test_generic_pattern_without_references_blocks_template_risk():
    payload = _base_payload()
    payload.pop("design_references")
    payload["source_text"] = "Generic SaaS template with dark hero, repeated cards and pill buttons."

    result = assess_frontend_visual_execution_guard(payload, root=ATLAS_ROOT)

    assert result["state"] == "blocked_generic_template_risk"
    assert result["generic_template_risk"] == "high"


def test_browser_qa_brief_and_mobile_checkpoints_are_ready():
    payload = _base_payload()
    payload["provided_evidence"].append("motion_validated")

    result = assess_frontend_visual_execution_guard(payload, root=ATLAS_ROOT)

    assert result["state"] == "ready"
    assert result["visual_brief_present"] is True
    assert result["browser_qa_present"] is True
    assert result["mobile_first_plan_present"] is True


def test_visual_ready_claim_without_browser_evidence_blocks_missing_evidence():
    payload = _base_payload()
    payload["provided_evidence"] = ["responsive_check"]
    payload["claims_visual_ready"] = True

    result = assess_frontend_visual_execution_guard(payload, root=ATLAS_ROOT)

    assert result["state"] == "blocked_missing_visual_evidence"


def test_governance_rules_require_expected_fields():
    from tools.atlas_governance_check import _load_frontend_visual_execution_guard_rules
    from tools.atlas_governance_check import _validate_frontend_visual_execution_guard_rules

    findings = []
    invalid_rules = _load_frontend_visual_execution_guard_rules(ATLAS_ROOT)
    invalid_rules["blocked_states"] = ["blocked_motion_unverified"]

    with patch(
        "tools.atlas_governance_check._load_frontend_visual_execution_guard_rules",
        return_value=invalid_rules,
    ):
        _validate_frontend_visual_execution_guard_rules(ATLAS_ROOT, findings)

    assert any(
        finding.startswith("frontend_visual_execution_guard_rules_missing_blocked_states:")
        for finding in findings
    )
