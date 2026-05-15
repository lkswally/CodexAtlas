import os
from pathlib import Path

os.environ["ATLAS_DISABLE_EVENT_LOGS"] = "1"

from tools.model_cost_control_readiness import assess_model_cost_control


ATLAS_ROOT = Path(r"C:\Proyectos\Codex-Atlas")


def test_model_cost_control_prefers_mini_for_small_docs_task():
    result = assess_model_cost_control(
        root=ATLAS_ROOT,
        task="Update the README with a small status note.",
        task_type="documentation",
        risk_level="low",
        complexity="low",
    )
    assert result["recommended_model_tier"] == "mini"
    assert result["status"] == "ok"


def test_model_cost_control_prefers_strong_for_high_risk_architecture():
    result = assess_model_cost_control(
        root=ATLAS_ROOT,
        task="Plan the architecture boundary changes and security-sensitive contracts for Atlas.",
        task_type="architecture",
        risk_level="high",
        complexity="high",
        estimated_context_chars=4200,
    )
    assert result["recommended_model_tier"] == "strong"
    assert result["split_task_recommended"] is True
    assert result["requires_user_confirmation"] is True


def test_model_cost_control_prefers_medium_for_bounded_code_execution():
    result = assess_model_cost_control(
        root=ATLAS_ROOT,
        task="Implement a focused Python command and update the related tests.",
        task_type="code_execution",
        risk_level="medium",
        complexity="medium",
    )
    assert result["recommended_model_tier"] == "medium"


def test_model_cost_control_asks_for_context_reduction_on_large_context():
    result = assess_model_cost_control(
        root=ATLAS_ROOT,
        task="Review this task.",
        task_type="audit_review",
        risk_level="medium",
        complexity="medium",
        estimated_context_chars=5000,
    )
    assert "summarize" in result["context_reduction_strategy"]
    assert result["split_task_recommended"] is True


def test_model_cost_control_requires_confirmation_when_task_type_is_ambiguous():
    result = assess_model_cost_control(
        root=ATLAS_ROOT,
        task="Work on Atlas and improve what matters most.",
        risk_level="medium",
        complexity="medium",
    )
    assert result["requires_user_confirmation"] is True
    assert "ambiguous_task_type" in result["risks"]
