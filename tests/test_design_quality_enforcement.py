import os
from pathlib import Path

os.environ["ATLAS_DISABLE_EVENT_LOGS"] = "1"

from tests._support_paths import ATLAS_ROOT
from tools.design_quality_enforcement import audit_design_quality




def _design_check(check_id, status="pass", evidence=None, recommendation=None):
    payload = {
        "id": check_id,
        "status": status,
        "severity": "medium",
        "evidence": evidence or [f"{check_id}:{status}"],
    }
    if recommendation:
        payload["recommendation"] = recommendation
    return payload


def _brand_review(generic=None, accessibility=None):
    return {
        "status": "ready",
        "requires_profile": True,
        "explicit_profile_present": True,
        "anti_generic_risks": generic or [],
        "accessibility_risks": accessibility or [],
    }


def _payload():
    return {
        "project_type": "frontend_app",
        "design_checks": [
            _design_check("cta_clarity"),
            _design_check("hero_structure"),
            _design_check("spacing_layout_coherence"),
            _design_check("content_density"),
            _design_check("anti_generic_default"),
            _design_check("typography_coherence"),
            _design_check("section_rhythm"),
            _design_check("landing_vs_documentation_balance"),
        ],
        "visual_intent_contract_review": {"status": "ready"},
        "brand_profile_review": _brand_review(),
        "ui_pre_return_review": {"warnings": [], "anti_generic_risks": [], "accessibility_risks": []},
        "source_text": "A differentiated product surface with clear CTA and intentional hierarchy.",
    }


def test_design_quality_enforcement_passes_for_valid_payload():
    result = audit_design_quality(_payload(), root=ATLAS_ROOT)
    assert result["status"] == "pass"
    assert result["ready_for_handoff"] is True
    assert result["blockers"] == []


def test_design_quality_enforcement_blocks_excessive_borders():
    payload = _payload()
    payload["visual_signals"] = {"border_weight_excessive": True}
    result = audit_design_quality(payload, root=ATLAS_ROOT)
    assert result["status"] == "not_ready"
    assert any(item["check"] == "border_weight_excessive" for item in result["blockers"])


def test_design_quality_enforcement_blocks_heavy_shadows():
    payload = _payload()
    payload["visual_signals"] = {"shadow_style_heavy": True}
    result = audit_design_quality(payload, root=ATLAS_ROOT)
    assert result["status"] == "not_ready"
    assert any(item["check"] == "shadow_style_heavy" for item in result["blockers"])


def test_design_quality_enforcement_blocks_weak_hierarchy():
    payload = _payload()
    payload["design_checks"] = [
        _design_check("hero_structure", status="warning", recommendation="Strengthen hero structure."),
        _design_check("spacing_layout_coherence", status="warning", recommendation="Improve spacing rhythm."),
        _design_check("content_density", status="warning", recommendation="Reduce density."),
    ]
    result = audit_design_quality(payload, root=ATLAS_ROOT)
    assert result["status"] == "not_ready"
    assert any(item["check"] == "weak_visual_hierarchy" for item in result["blockers"])


def test_design_quality_enforcement_flags_weak_button_hierarchy():
    payload = _payload()
    payload["design_checks"] = [_design_check("cta_clarity", status="fail", recommendation="Clarify the CTA hierarchy.")]
    result = audit_design_quality(payload, root=ATLAS_ROOT)
    assert any(item["check"] == "weak_button_hierarchy" for item in result["blockers"])


def test_design_quality_enforcement_blocks_brutalism_misapplied():
    payload = _payload()
    payload["visual_signals"] = {"brutalism_misapplied": True}
    result = audit_design_quality(payload, root=ATLAS_ROOT)
    assert result["status"] == "not_ready"
    assert result["required_redesign_level"] in {"visual_system_refactor", "full_redesign"}


def test_design_quality_enforcement_marks_functional_but_amateur_ui_as_not_ready():
    payload = _payload()
    payload["visual_signals"] = {
        "border_weight_excessive": True,
        "shadow_style_heavy": True,
        "amateur_internal_tool_look": True,
    }
    result = audit_design_quality(payload, root=ATLAS_ROOT)
    assert result["status"] == "not_ready"
    assert result["ready_for_handoff"] is False
    assert result["visual_quality_score"] < 80
