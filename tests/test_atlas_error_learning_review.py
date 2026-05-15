from tools.atlas_error_learning_review import review_atlas_error_learning


def _base_payload():
    return {
        "project_type": "frontend_app",
        "design_checks": [
            {"id": "hero_structure", "status": "pass"},
            {"id": "cta_clarity", "status": "pass"},
            {"id": "cta_integrity", "status": "pass"},
            {"id": "landing_vs_documentation_balance", "status": "pass"},
            {"id": "typography_coherence", "status": "pass"},
        ],
        "ui_pre_return_review": {"missing_evidence": []},
        "frontend_auto_audit_review": {"status": "ready"},
        "visual_qa_readiness_posture": {"safe_to_run": False},
        "manual_visual_review_recorded": True,
        "integration_surfaces": [],
        "certify_report": {"result": {"blockers": [], "warnings": []}},
    }


def test_error_learning_passes_clean_payload():
    result = review_atlas_error_learning(_base_payload())
    assert result["status"] == "ready"
    assert result["blockers"] == []


def test_error_learning_blocks_visual_regressions_and_missing_evidence():
    payload = _base_payload()
    payload["hero_overflow"] = True
    payload["ctas_not_working"] = True
    payload["manual_visual_review_recorded"] = False
    payload["ui_pre_return_review"] = {"missing_evidence": ["screenshots"]}
    result = review_atlas_error_learning(payload)
    assert result["status"] == "needs_improvement"
    assert "error_learning_ui_not_ready" in result["warning_codes"]
    assert "error_learning_visual_evidence_missing" in result["warning_codes"]


def test_error_learning_blocks_readme_like_landing():
    payload = _base_payload()
    payload["landing_reads_like_readme"] = True
    result = review_atlas_error_learning(payload)
    assert result["status"] == "needs_improvement"
    assert "error_learning_landing_not_ready" in result["warning_codes"]


def test_error_learning_flags_integration_claims_ahead_of_readiness():
    payload = _base_payload()
    payload["project_type"] = "backend_api"
    payload["integration_surfaces"] = [
        {
            "name": "OpenAI Docs MCP",
            "claim_active": True,
            "declared_state": "ready",
            "actual_state": "watchlist",
            "tests_present": False,
        }
    ]
    result = review_atlas_error_learning(payload)
    assert result["status"] == "needs_improvement"
    assert result["requires_decision_council"] is True
    assert "error_learning_integration_not_ready" in result["warning_codes"]
