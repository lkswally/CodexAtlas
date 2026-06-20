import pytest

from tools.architecture_state_model import ARCHITECTURE_DOMAINS, build_architecture_state
from tools.intelligent_orchestrator import (
    OrchestratorContractError,
    consolidate_return_envelopes,
    simulate_orchestration,
    validate_return_envelope,
)


def _envelope(agent="Verifier", status="PASS", **overrides):
    result = {
        "agent": agent,
        "status": status,
        "summary": f"{agent} completed its bounded task.",
        "evidence": [f"{agent}:check"],
        "changes": [],
        "risks": [],
        "recommendation": "Proceed with the verified result.",
        "needs_followup": False,
    }
    result.update(overrides)
    return result


def _passing_state():
    return build_architecture_state(
        {
            domain: {
                "status": "PASS",
                "evidence": [f"{domain}:pass"],
                "freshness": {"is_stale": False},
                "confidence": 0.9,
            }
            for domain in ARCHITECTURE_DOMAINS
        }
    )


def test_simple_task_uses_one_agent_and_cheap_model():
    report = simulate_orchestration("Update README wording for clarity")

    assert report["status"] == "READY"
    assert report["decision_gate"]["split_task"] is False
    assert len(report["agent_assignments"]) == 1
    assert report["agent_assignments"][0]["agent"] == "Documentation Specialist"
    assert report["model_routing"]["selected_model_class"] == "cheap_fast"


def test_complex_architecture_task_splits_to_three_roles():
    report = simulate_orchestration(
        "Design a complex architecture redesign across multiple modules"
    )

    assert report["decision_gate"]["split_task"] is True
    assert [item["agent"] for item in report["agent_assignments"]] == [
        "Planner",
        "Executor",
        "Verifier",
    ]
    assert report["model_routing"]["selected_model_class"] == "premium_reasoning"


def test_high_risk_task_requires_approval_and_verifier():
    report = simulate_orchestration(
        "Review critical production security architecture before release"
    )

    roles = [item["agent"] for item in report["agent_assignments"]]
    assert report["decision_gate"]["requires_human_approval"] is True
    assert "Verifier" in roles
    assert report["model_routing"]["selected_model_class"] == "premium_reasoning"


def test_complex_code_can_use_code_specialist_class():
    report = simulate_orchestration(
        "Implement a complex cross-module code refactor with bounded tests"
    )

    assert report["model_routing"]["selected_model_class"] == "code_specialist"


def test_verification_task_uses_verifier_model_class():
    report = simulate_orchestration("Verify the current test evidence and audit report")

    assert report["model_routing"]["selected_model_class"] == "verifier"


def test_agent_context_is_minimal_and_role_relevant():
    files = [
        "README.md",
        "docs/design.md",
        "tools/runtime.py",
        "tests/test_runtime.py",
        "config/runtime.json",
        "policies/security.md",
        "docs/extra.md",
    ]
    report = simulate_orchestration(
        "Verify the implementation and review its test evidence",
        relevant_files=files,
        architecture_state=_passing_state(),
    )
    context = report["agent_assignments"][0]["context"]

    assert len(context["relevant_files"]) <= 4
    assert "tests/test_runtime.py" in context["relevant_files"]
    assert set(context) == {"relevant_files", "architecture_domains", "constraints"}
    assert len(context["architecture_domains"]) <= 4


def test_return_envelope_contract_accepts_evidenced_pass():
    assert validate_return_envelope(_envelope()) is True


def test_return_envelope_rejects_pass_without_evidence():
    with pytest.raises(OrchestratorContractError, match="require evidence"):
        validate_return_envelope(_envelope(evidence=[]))


def test_return_envelope_rejects_extra_fields():
    with pytest.raises(OrchestratorContractError, match="exact field contract"):
        validate_return_envelope({**_envelope(), "extra": True})


def test_consolidation_preserves_worst_status_and_deduplicates():
    result = consolidate_return_envelopes(
        [
            _envelope("Executor", evidence=["tests:pass"], changes=["tools/a.py"]),
            _envelope(
                "Verifier",
                status="WARN",
                evidence=["tests:pass", "diff:clean"],
                risks=["manual_review"],
                needs_followup=True,
            ),
        ]
    )

    assert result["agent"] == "Orchestrator"
    assert result["status"] == "WARN"
    assert result["evidence"] == ["tests:pass", "diff:clean"]
    assert result["needs_followup"] is True


def test_simulator_consolidates_supplied_results_without_execution():
    report = simulate_orchestration(
        "Update README wording for clarity", agent_results=[_envelope("Documentation Specialist")]
    )

    assert report["consolidated_result"]["status"] == "PASS"
    assert report["verification_plan"]["failure_registry_review_required"] is False
    assert report["runtime_execution"] is False


def test_failed_result_requests_failure_registry_review():
    report = simulate_orchestration(
        "Update README wording for clarity",
        agent_results=[_envelope("Documentation Specialist", status="FAIL")],
    )

    assert report["verification_plan"] == {
        "review_evidence": True,
        "review_risks": True,
        "review_tests_and_checks": True,
        "review_changes": True,
        "review_docs_consistency": True,
        "failure_registry_review_required": True,
    }


def test_dangerous_command_blocks_plan_before_assignment():
    report = simulate_orchestration(
        "Clean generated files from the workspace",
        proposed_commands=["rm -rf /"],
    )

    assert report["status"] == "BLOCKED"
    assert report["agent_assignments"] == []
    assert report["command_assessments"][0]["status"] == "DENY"
    assert report["decision_gate"]["safe_to_proceed"] is False


def test_unknown_command_requires_approval_but_is_not_assumed_dangerous():
    report = simulate_orchestration(
        "Run a bounded custom repository check",
        proposed_commands=["custom-check --read-only"],
    )

    assert report["status"] == "READY"
    assert report["command_assessments"][0]["status"] == "UNKNOWN"
    assert report["decision_gate"]["requires_human_approval"] is True


def test_failed_security_state_blocks_orchestration():
    state = _passing_state()
    state["domains"]["security"]["status"] = "FAIL"
    state["overall_status"] = "FAIL"

    report = simulate_orchestration(
        "Update README wording for clarity", architecture_state=state
    )

    assert report["status"] == "BLOCKED"
    assert "architecture_domain_failed:security" in report["decision_gate"]["blockers"]


def test_vague_task_asks_exactly_one_question_and_stops():
    report = simulate_orchestration("help")

    assert report["status"] == "NEEDS_CLARIFICATION"
    assert report["clarification"]["question_count"] == 1
    assert report["agent_assignments"] == []
    assert report["loop_control"]["max_decision_rounds"] == 1


def test_loop_control_never_allows_more_than_three_agents():
    report = simulate_orchestration(
        "Review critical production security architecture across multiple modules"
    )

    assert report["loop_control"]["max_agents"] == 3
    assert report["loop_control"]["planned_agents"] <= 3
    assert report["loop_control"]["agents_may_converse"] is False
