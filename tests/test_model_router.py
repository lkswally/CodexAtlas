import os
from pathlib import Path

os.environ["ATLAS_DISABLE_EVENT_LOGS"] = "1"

from tools.model_router import recommend_model_profile


ATLAS_ROOT = Path(r"C:\Proyectos\Codex-Atlas")


def test_model_router_prefers_cost_saver_for_simple_documentation():
    result = recommend_model_profile(
        root=ATLAS_ROOT,
        task="Update the README with a small status note and save tokens.",
        intent="documentation",
        current_phase="certified",
        risk_level="low",
        complexity="low",
        project_type="internal_tool",
    )
    assert result["recommended_model_profile"] == "cost_saver"
    assert result["cost_sensitivity"] == "high"


def test_model_router_prefers_security_for_high_risk_tasks():
    result = recommend_model_profile(
        root=ATLAS_ROOT,
        task="Review auth credentials and security boundaries before production handoff.",
        intent="security",
        current_phase="audit",
        risk_level="high",
        complexity="high",
        project_type="internal_tool",
    )
    assert result["recommended_model_profile"] == "security"
    assert result["reasoning_required"] == "high"


def test_model_router_prefers_creative_product_for_design_work():
    result = recommend_model_profile(
        root=ATLAS_ROOT,
        task="Define branding, visual direction and landing narrative.",
        intent="branding_ux",
        current_phase="build",
        risk_level="medium",
        complexity="medium",
        project_type="internal_tool",
        recommended_skill="visual-direction-checkpoint",
    )
    assert result["recommended_model_profile"] == "creative_product"
    assert result["task_mode"] == "design"
