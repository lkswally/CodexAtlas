import os
from pathlib import Path

os.environ["ATLAS_DISABLE_EVENT_LOGS"] = "1"

from tools.model_router import recommend_model_profile


ATLAS_ROOT = Path(r"C:\Proyectos\Codex-Atlas")
SWITCH_SUPPORT_UNVERIFIED = {
    "status": "ok",
    "current_global_model": "gpt-5.4",
    "current_project_model": None,
    "codex_cli_available": False,
    "codex_cli_error": "Access is denied",
    "can_auto_switch": False,
    "auto_switch_method": "config",
    "evidence": ["global_config_model=gpt-5.4", "project_scoped_config_missing", "codex_cli_error=Access is denied"],
}


def test_model_router_prefers_gpt_5_4_for_complex_planning():
    result = recommend_model_profile(
        root=ATLAS_ROOT,
        task="Plan the architecture and next strategic phases for Atlas.",
        intent="planning",
        current_phase="planning",
        risk_level="medium",
        complexity="high",
        project_type="internal_tool",
        switch_support=SWITCH_SUPPORT_UNVERIFIED,
    )
    assert result["recommended_model"] == "GPT-5.4"
    assert result["fallback_model"] == "GPT-5.2"
    assert result["recommended_model_profile"] == "deep_reasoning"


def test_model_router_prefers_codex_model_for_general_code_execution():
    result = recommend_model_profile(
        root=ATLAS_ROOT,
        task="Implement a focused Python command and edit the related files.",
        intent="code_execution",
        current_phase="build",
        risk_level="medium",
        complexity="medium",
        project_type="internal_tool",
        switch_support=SWITCH_SUPPORT_UNVERIFIED,
    )
    assert result["recommended_model"] in {"GPT-5.2-Codex", "GPT-5.3-Codex"}
    assert result["recommended_model_profile"] == "code_execution"


def test_model_router_prefers_codex_max_for_delicate_large_change():
    result = recommend_model_profile(
        root=ATLAS_ROOT,
        task="Refactor a risky multi-file code path with delicate contract changes.",
        intent="code_execution",
        current_phase="build",
        risk_level="high",
        complexity="high",
        project_type="internal_tool",
        switch_support=SWITCH_SUPPORT_UNVERIFIED,
    )
    assert result["recommended_model"] == "GPT-5.1-Codex-Max"
    assert result["fallback_model"] == "GPT-5.2-Codex"


def test_model_router_prefers_mini_for_simple_documentation():
    result = recommend_model_profile(
        root=ATLAS_ROOT,
        task="Update the README with a small status note.",
        intent="documentation",
        current_phase="certified",
        risk_level="low",
        complexity="low",
        project_type="internal_tool",
        switch_support=SWITCH_SUPPORT_UNVERIFIED,
    )
    assert result["recommended_model"] in {"GPT-5.4-Mini", "GPT-5.1-Codex-Mini"}
    assert result["cost_sensitivity"] in {"medium", "high"}


def test_model_router_prefers_codex_mini_for_low_risk_token_saving():
    result = recommend_model_profile(
        root=ATLAS_ROOT,
        task="Do a small lightweight edit and save tokens.",
        intent="documentation",
        current_phase="build",
        risk_level="low",
        complexity="low",
        project_type="internal_tool",
        switch_support=SWITCH_SUPPORT_UNVERIFIED,
    )
    assert result["recommended_model"] == "GPT-5.1-Codex-Mini"
    assert result["cost_sensitivity"] == "high"


def test_model_router_marks_ambiguous_case_for_confirmation():
    result = recommend_model_profile(
        root=ATLAS_ROOT,
        task="Work on Atlas and improve what matters most.",
        intent=None,
        current_phase=None,
        risk_level="medium",
        complexity="medium",
        project_type="internal_tool",
        switch_support=SWITCH_SUPPORT_UNVERIFIED,
    )
    assert result["requires_user_confirmation"] is True
    assert result["confidence"] == "low"
    assert result["question_for_user"]


def test_model_router_does_not_allow_auto_switch_when_unverified():
    result = recommend_model_profile(
        root=ATLAS_ROOT,
        task="Plan the next strategic phase for Atlas.",
        intent="planning",
        current_phase="planning",
        risk_level="medium",
        complexity="high",
        project_type="internal_tool",
        switch_support=SWITCH_SUPPORT_UNVERIFIED,
    )
    assert result["can_auto_switch"] is False
    assert result["auto_switch_method"] == "config"
    assert result["requires_user_confirmation"] is True


def test_model_router_requires_question_when_information_is_missing():
    result = recommend_model_profile(
        root=ATLAS_ROOT,
        task="",
        intent=None,
        current_phase=None,
        risk_level="medium",
        complexity="medium",
        project_type="internal_tool",
        switch_support=SWITCH_SUPPORT_UNVERIFIED,
    )
    assert result["missing_information"]
    assert result["question_for_user"]
