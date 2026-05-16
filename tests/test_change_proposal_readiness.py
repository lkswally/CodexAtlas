from tools.change_proposal_readiness import assess_change_proposal_readiness


def test_change_proposal_not_required_for_small_low_risk_change():
    result = assess_change_proposal_readiness(
        {
            "change_size": "small",
            "risk_level": "low",
            "complexity": "low",
        }
    )
    assert result["status"] == "not_required"
    assert result["required"] is False


def test_change_proposal_missing_for_medium_change():
    result = assess_change_proposal_readiness(
        {
            "change_size": "medium",
            "risk_level": "medium",
            "complexity": "medium",
        }
    )
    assert result["status"] == "missing"
    assert "proposal" in result["missing_artifacts"]
    assert "archive" in result["missing_artifacts"]


def test_change_proposal_partial_when_sections_are_missing():
    result = assess_change_proposal_readiness(
        {
            "change_size": "large",
            "risk_level": "high",
            "provided_artifacts": {
                "proposal": [
                    "what_changes",
                    "why",
                    "problem_resolved"
                ],
                "specs": [
                    "functional_requirements",
                    "non_functional_requirements"
                ]
            }
        }
    )
    assert result["status"] == "partial"
    assert result["artifact_statuses"]["proposal"] == "partial"
    assert "out_of_scope" in result["missing_sections"]["proposal"]
    assert result["artifact_statuses"]["design"] == "missing"


def test_change_proposal_ready_when_all_artifacts_are_complete():
    result = assess_change_proposal_readiness(
        {
            "change_size": "medium",
            "risk_level": "medium",
            "provided_artifacts": {
                "proposal": [
                    "what_changes",
                    "why",
                    "problem_resolved",
                    "out_of_scope",
                    "risks",
                    "expected_impact"
                ],
                "specs": [
                    "functional_requirements",
                    "non_functional_requirements",
                    "scenarios",
                    "acceptance_criteria"
                ],
                "design": [
                    "technical_approach",
                    "affected_modules",
                    "tradeoffs",
                    "discarded_alternatives"
                ],
                "tasks": [
                    "task_list",
                    "suggested_order",
                    "validation_per_task",
                    "rollback_if_needed"
                ],
                "verify": [
                    "tests",
                    "governance",
                    "quality_gate",
                    "minimum_evidence",
                    "known_false_positives"
                ],
                "archive": [
                    "final_decision",
                    "commit_reference",
                    "lessons_learned",
                    "next_steps"
                ]
            }
        }
    )
    assert result["status"] == "ready"
    assert result["missing_artifacts"] == []
    assert result["missing_sections"] == {}
