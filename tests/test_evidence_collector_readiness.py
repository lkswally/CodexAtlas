from tools.evidence_collector_readiness import review_evidence_collector_readiness


def test_frontend_evidence_is_partial_without_screenshots():
    result = review_evidence_collector_readiness(
        {
            "project_type": "frontend_app",
            "provided_evidence": [
                "responsive_check",
                "tap_target_check",
                "font_loading_check",
                "link_cta_check",
                "seo_basics",
                "accessibility_basics",
                "build_test_result",
                "known_false_positives",
            ],
        }
    )
    assert result["readiness_state"] == "evidence_partial"
    assert "screenshot_desktop" in result["missing_evidence"]
    assert result["can_claim_ready"] is False
    assert result["can_claim_pass_with_caution"] is True


def test_backend_evidence_can_be_ready():
    result = review_evidence_collector_readiness(
        {
            "project_type": "backend_service",
            "provided_evidence": [
                "tests",
                "endpoint_contract",
                "error_handling",
                "migration_schema_check",
                "relevant_logs",
                "no_secrets",
            ],
        }
    )
    assert result["readiness_state"] == "evidence_ready"
    assert result["can_claim_ready"] is True


def test_research_requires_sources_and_inference_label():
    result = review_evidence_collector_readiness(
        {
            "task_type": "research_benchmark",
            "provided_evidence": [
                "sources",
                "query_date",
                "selection_criteria",
            ],
        }
    )
    assert result["readiness_state"] == "evidence_partial"
    assert "inference_vs_data" in result["blocking_gaps"]


def test_high_risk_decision_missing_decision_council_is_not_ready():
    result = review_evidence_collector_readiness(
        {
            "task_type": "high_risk_decision",
            "provided_evidence": [
                "alternatives_compared",
                "tradeoffs",
                "risks",
            ],
        }
    )
    assert result["readiness_state"] == "evidence_partial"
    assert "decision_council" in result["blocking_gaps"]
    assert result["can_claim_ready"] is False


def test_skill_governance_change_requires_governance_and_tests():
    result = review_evidence_collector_readiness(
        {
            "task_type": "skill_governance_change",
            "provided_evidence": [
                "policy",
                "config",
                "behavior",
                "tests",
                "governance_check",
                "lifecycle_state",
            ],
        }
    )
    assert result["readiness_state"] == "evidence_ready"
    assert result["can_claim_ready"] is True
