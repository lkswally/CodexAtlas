from tools.frontend_auto_audit_rules import audit_frontend_auto_readiness


def _base_payload():
    return {
        "project_type": "frontend_app",
        "intent_clarifier_contract": {"status": "ready", "missing_questions": [], "weak_answers": []},
        "visual_intent_contract_review": {
            "status": "ready",
            "contract": {"evidence_expectations": ["screenshots planned", "cta proof"]}
        },
        "brand_json_v2_readiness": {
            "status": "ready",
            "missing_sections": [],
            "weak_sections": [],
            "evidence_expectations": ["palette rationale"]
        },
        "brand_profile_review": {"status": "ready"},
        "ui_pre_return_review": {
            "status": "pass",
            "pass_ready": True,
            "blockers": [],
            "missing_evidence": []
        },
        "design_quality_review": {
            "status": "ready",
            "ready_for_handoff": True,
            "detected_risks": []
        },
        "design_checks": [
            {"id": "responsive_baseline", "status": "pass", "evidence": ["viewport_meta=true", "media_queries=true"]}
        ],
    }


def test_frontend_auto_audit_passes_when_local_guardrails_are_ready():
    result = audit_frontend_auto_readiness(_base_payload())
    assert result["status"] == "ready"
    assert result["can_support_pre_return"] is True


def test_frontend_auto_audit_blocks_missing_intent_clarifier():
    payload = _base_payload()
    payload["intent_clarifier_contract"] = {"status": "needs_input", "missing_questions": ["target_audience"], "weak_answers": []}
    result = audit_frontend_auto_readiness(payload)
    assert result["status"] == "needs_improvement"
    assert any(item["check"] == "frontend_auto_audit_missing_intent_clarifier" for item in result["blockers"])


def test_frontend_auto_audit_blocks_missing_brand_json_v2():
    payload = _base_payload()
    payload["brand_json_v2_readiness"] = {"status": "needs_input", "missing_sections": ["mood_vector"], "weak_sections": []}
    result = audit_frontend_auto_readiness(payload)
    assert result["status"] == "needs_improvement"
    assert any(item["check"] == "frontend_auto_audit_missing_brand_json_v2" for item in result["warnings"])


def test_frontend_auto_audit_flags_missing_evidence():
    payload = _base_payload()
    payload["visual_intent_contract_review"]["contract"]["evidence_expectations"] = []
    payload["brand_json_v2_readiness"]["evidence_expectations"] = []
    payload["ui_pre_return_review"]["missing_evidence"] = ["evidence_expectations"]
    result = audit_frontend_auto_readiness(payload)
    assert result["status"] == "needs_improvement"
    assert "evidence_expectations" in result["evidence_gaps"]
