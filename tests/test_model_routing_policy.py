import copy
from unittest.mock import patch

import pytest

from tests._support_paths import ATLAS_ROOT
from tools.atlas_governance_check import _load_model_routing_rules, _validate_model_routing_rules
from tools.model_routing_policy import ModelRoutingPolicyError, select_model_class


def test_documentation_routes_to_cheap_fast():
    result = select_model_class("documentation", "low")

    assert result["selected_model_class"] == "cheap_fast"
    assert result["requires_human_approval"] is False
    assert result["auto_switch_allowed"] is False


@pytest.mark.parametrize("task_type", ["summarization", "formatting"])
def test_low_risk_lightweight_tasks_route_to_cheap_fast(task_type):
    result = select_model_class(task_type, "low")

    assert result["selected_model_class"] == "cheap_fast"


@pytest.mark.parametrize("task_type", ["code_small_change", "test_generation"])
def test_bounded_code_tasks_route_to_balanced(task_type):
    result = select_model_class(task_type, "medium")

    assert result["selected_model_class"] == "balanced"


@pytest.mark.parametrize(
    "task_type",
    ["architecture_decision", "security_review", "outcome_evaluation"],
)
def test_high_reasoning_tasks_route_to_premium_reasoning(task_type):
    result = select_model_class(task_type, "medium")

    assert result["selected_model_class"] == "premium_reasoning"


@pytest.mark.parametrize("task_type", ["production_operation", "external_side_effect"])
def test_side_effect_tasks_require_human(task_type):
    result = select_model_class(task_type, "medium")

    assert result["selected_model_class"] == "human_required"
    assert result["requires_human_approval"] is True


def test_secrets_or_credentials_are_blocked():
    result = select_model_class("secrets_or_credentials", "low")

    assert result["selected_model_class"] == "blocked"
    assert result["requires_human_approval"] is True


def test_high_risk_never_routes_to_cheap_fast():
    result = select_model_class("documentation", "high")

    assert result["selected_model_class"] == "balanced"
    assert "High-risk work must never use cheap_fast." in result["reason"]


def test_blocked_risk_always_blocks():
    result = select_model_class("documentation", "blocked")

    assert result["selected_model_class"] == "blocked"
    assert result["requires_human_approval"] is True


def test_output_contract_is_exact():
    result = select_model_class("test_execution_analysis", "medium")

    assert set(result.keys()) == {
        "task_type",
        "risk_level",
        "selected_model_class",
        "reason",
        "requires_human_approval",
        "auto_switch_allowed",
    }


def test_cost_and_criticality_do_not_enable_auto_switch():
    result = select_model_class(
        "code_refactor",
        "high",
        cost_sensitivity="high",
        criticality="high",
    )

    assert result["selected_model_class"] == "balanced"
    assert result["auto_switch_allowed"] is False
    assert "V1 does not auto-switch" in result["reason"]


def test_unknown_task_type_fails_controlled():
    with pytest.raises(ModelRoutingPolicyError):
        select_model_class("unknown", "low")


def test_unknown_risk_level_fails_controlled():
    with pytest.raises(ModelRoutingPolicyError):
        select_model_class("documentation", "unknown")


def test_governance_accepts_model_routing_policy_v1():
    findings = []

    _validate_model_routing_rules(ATLAS_ROOT, findings)

    assert findings == []


def test_governance_rejects_v1_auto_switch():
    rules = copy.deepcopy(_load_model_routing_rules(ATLAS_ROOT))
    rules["auto_switch_allowed"] = True
    findings = []

    with patch("tools.atlas_governance_check._load_model_routing_rules", return_value=rules):
        _validate_model_routing_rules(ATLAS_ROOT, findings)

    assert "model_routing_v1_auto_switch_must_be_false" in findings
