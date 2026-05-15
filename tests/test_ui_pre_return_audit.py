import os
from pathlib import Path

os.environ["ATLAS_DISABLE_EVENT_LOGS"] = "1"

from tests._support_paths import ATLAS_ROOT
from tools.ui_pre_return_audit import audit_ui_pre_return




def _design_check(check_id, status="pass", recommendation=None, evidence=None):
    payload = {
        "id": check_id,
        "status": status,
        "severity": "medium",
        "evidence": evidence or [f"{check_id}:{status}"],
    }
    if recommendation:
        payload["recommendation"] = recommendation
    return payload


def _visual_review(status="ready", missing=None, weak=None):
    return {
        "status": status,
        "requires_contract": True,
        "missing_fields": missing or [],
        "weak_fields": weak or [],
        "contract": {
            "project_type": "frontend_app",
            "visual_density": "medium",
            "motion_intensity": "low",
            "evidence_expectations": ["hero clarity proof", "cta proof"],
        },
    }


def _brand_review(status="ready", explicit=True, missing=None, weak=None, invalid=None, generic=None, derivative=None, accessibility=None):
    return {
        "status": status,
        "requires_profile": True,
        "explicit_profile_present": explicit,
        "profile_source": "explicit_brand_profile",
        "missing_fields": missing or [],
        "weak_fields": weak or [],
        "invalid_fields": invalid or [],
        "anti_generic_risks": generic or [],
        "derivative_risks": derivative or [],
        "accessibility_risks": accessibility or [],
        "profile": {
            "visual_density": "medium",
            "motion_principles": ["subtle section transitions"],
            "color_strategy": {"primary": "#141414"},
            "evidence_expectations": ["brand rationale", "palette proof"],
        },
    }


def _valid_payload():
    return {
        "project_type": "frontend_app",
        "visual_intent_contract_review": _visual_review(),
        "brand_profile_review": _brand_review(),
        "design_checks": [
            _design_check("cta_clarity"),
            _design_check("above_the_fold_clarity"),
            _design_check("typography_coherence"),
            _design_check("responsive_baseline"),
            _design_check("contrast_accessibility"),
            _design_check("hero_structure"),
            _design_check("spacing_layout_coherence"),
            _design_check("content_density"),
            _design_check("anti_generic_default"),
            _design_check("landing_vs_documentation_balance"),
            _design_check("section_rhythm"),
        ],
        "public_readiness": "needs_improvement",
        "landing_score": 92,
        "source_text": "Atlas frontend landing with clear CTA and differentiated system-first identity.",
    }


def test_ui_pre_return_audit_skips_backend_projects():
    result = audit_ui_pre_return({"project_type": "backend_service"}, root=ATLAS_ROOT)
    assert result["status"] == "skipped"
    assert result["checks"] == []


def test_ui_pre_return_audit_passes_for_valid_payload():
    result = audit_ui_pre_return(_valid_payload(), root=ATLAS_ROOT)
    assert result["status"] == "pass"
    assert result["pass_ready"] is True
    assert result["warnings"] == []
    assert result["blockers"] == []
    assert result["design_quality_review"]["status"] == "pass"


def test_ui_pre_return_audit_flags_missing_visual_intent_contract():
    payload = _valid_payload()
    payload["visual_intent_contract_review"] = {}
    result = audit_ui_pre_return(payload, root=ATLAS_ROOT)
    assert result["status"] == "not_ready"
    assert "ui_pre_return_missing_visual_intent" in result["warnings"]


def test_ui_pre_return_audit_flags_missing_brand_profile():
    payload = _valid_payload()
    payload["brand_profile_review"] = _brand_review(status="needs_input", explicit=False, missing=["brand_name"])
    result = audit_ui_pre_return(payload, root=ATLAS_ROOT)
    assert "ui_pre_return_missing_brand_profile" in result["warnings"]
    assert "brand_profile_missing_or_inferred" in result["brand_alignment_risks"]


def test_ui_pre_return_audit_flags_weak_cta_and_above_fold():
    payload = _valid_payload()
    payload["design_checks"] = [
        _design_check("cta_clarity", status="fail", recommendation="Strengthen the CTA."),
        _design_check("above_the_fold_clarity", status="warning", recommendation="Clarify the hero."),
        _design_check("typography_coherence"),
        _design_check("responsive_baseline"),
        _design_check("contrast_accessibility"),
    ]
    result = audit_ui_pre_return(payload, root=ATLAS_ROOT)
    assert "ui_pre_return_cta_weak" in result["warnings"]
    assert result["blockers"]


def test_ui_pre_return_audit_flags_typography_and_layout_genericity():
    payload = _valid_payload()
    payload["design_checks"] = [
        _design_check("cta_clarity"),
        _design_check("above_the_fold_clarity"),
        _design_check("typography_coherence", status="warning", recommendation="Use more intentional type."),
        _design_check("responsive_baseline"),
        _design_check("contrast_accessibility"),
        _design_check("hero_structure", status="warning", recommendation="Strengthen hero pacing."),
        _design_check("spacing_layout_coherence", status="warning", recommendation="Improve hierarchy."),
        _design_check("content_density"),
        _design_check("anti_generic_default", status="warning", recommendation="Avoid generic defaults."),
        _design_check("landing_vs_documentation_balance"),
        _design_check("section_rhythm"),
    ]
    result = audit_ui_pre_return(payload, root=ATLAS_ROOT)
    assert "ui_pre_return_generic_risk" in result["warnings"]
    assert "layout_hierarchy_weak" in result["anti_generic_risks"]


def test_ui_pre_return_audit_flags_weak_color_strategy_and_derivative_risk():
    payload = _valid_payload()
    payload["brand_profile_review"] = _brand_review(
        status="needs_input",
        generic=["generic_color_strategy"],
        derivative=["too_close_to_reference_brand"],
        accessibility=["missing_contrast_notes"],
    )
    result = audit_ui_pre_return(payload, root=ATLAS_ROOT)
    assert "ui_pre_return_brand_mismatch" in result["warnings"]
    assert "ui_pre_return_generic_risk" in result["warnings"]
    assert result["requires_decision_council"] is True


def test_ui_pre_return_audit_flags_missing_evidence_and_unknown_responsive_state():
    payload = _valid_payload()
    payload["visual_intent_contract_review"]["contract"]["evidence_expectations"] = []
    payload["brand_profile_review"]["profile"]["evidence_expectations"] = []
    payload["design_checks"] = [
        _design_check("cta_clarity"),
        _design_check("above_the_fold_clarity"),
        _design_check("typography_coherence"),
        _design_check("responsive_baseline", status="skipped"),
        _design_check("contrast_accessibility", status="warning", recommendation="Improve contrast."),
    ]
    result = audit_ui_pre_return(payload, root=ATLAS_ROOT)
    assert "ui_pre_return_missing_evidence" in result["warnings"]
    assert "ui_pre_return_responsive_unknown" in result["warnings"]
    assert "ui_pre_return_accessibility_weak" in result["warnings"]
