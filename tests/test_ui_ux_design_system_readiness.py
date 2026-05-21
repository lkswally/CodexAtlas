import os

os.environ["ATLAS_DISABLE_EVENT_LOGS"] = "1"

from tests._support_paths import ATLAS_ROOT
from tools.ui_ux_design_system_readiness import assess_ui_ux_design_system_readiness


ROOT = ATLAS_ROOT


def test_ui_ux_design_system_readiness_recommends_react_motion_for_complex_dashboard():
    result = assess_ui_ux_design_system_readiness(
        root=ROOT,
        payload={
            "project_type": "dashboard",
            "product_type": "fintech analytics dashboard",
            "audience": "enterprise operations teams",
            "stack": "react",
            "uses_tailwind": True,
            "needs_complex_hero_motion": False,
            "needs_microinteractions": True,
            "needs_transition_heavy_ui": True,
            "needs_tables": True,
            "needs_dashboard_blocks": True,
        },
    )

    assert result["status"] == "ok"
    assert result["recommended_pattern"] == "summary hero plus prioritized metrics plus task-oriented workflows"
    assert result["frontend_motion_library_posture"] == "recommended_for_react"
    assert result["component_library_posture"]["tailgrids_fit"] == "high"
    assert result["component_library_posture"]["recommended_use"] == "manual_install_with_approval"
    assert "identical cards" in " ".join(result["anti_patterns"])


def test_ui_ux_design_system_readiness_keeps_simple_landing_css_first():
    result = assess_ui_ux_design_system_readiness(
        root=ROOT,
        payload={
            "project_type": "landing_page",
            "product_type": "developer tool saas landing page",
            "audience": "developer teams",
            "stack": "html-tailwind",
        },
    )

    assert result["status"] == "ok"
    assert result["frontend_motion_library_posture"] == "css_sufficient"
    assert result["component_library_posture"]["tailgrids_fit"] == "not_applicable"
    assert result["component_library_posture"]["recommended_use"] == "discard"
    assert "README-looking landing" in result["anti_patterns"]


def test_ui_ux_design_system_readiness_flags_missing_audience():
    result = assess_ui_ux_design_system_readiness(
        root=ROOT,
        payload={
            "project_type": "frontend_app",
            "product_type": "internal operations dashboard",
            "stack": "react",
        },
    )

    assert result["status"] == "needs_input"
    assert "audience" in result["missing_inputs"]


def test_ui_ux_design_system_readiness_uses_contract_inputs_when_payload_is_thin():
    result = assess_ui_ux_design_system_readiness(
        root=ROOT,
        payload={
            "visual_intent_contract": {
                "project_type": "landing_page",
                "audience": "consumer buyers",
            },
            "objective": "ecommerce seasonal launch",
            "stack": "nextjs",
            "needs_scroll_reveal": True,
        },
    )

    assert result["status"] == "ok"
    assert result["recommended_pattern"] == "value hero plus catalog or offer proof plus friction-light CTA progression"
    assert result["frontend_motion_library_posture"] == "recommended_for_react"


def test_ui_ux_design_system_readiness_keeps_tailgrids_as_inspiration_for_custom_identity():
    result = assess_ui_ux_design_system_readiness(
        root=ROOT,
        payload={
            "project_type": "frontend_app",
            "product_type": "creative studio portfolio",
            "audience": "design-conscious clients",
            "stack": "nextjs",
            "uses_tailwind": True,
            "identity_customness": "high",
            "needs_cards": True,
            "needs_landing_sections": True,
        },
    )

    assert result["status"] == "ok"
    assert result["component_library_posture"]["tailgrids_fit"] == "low"
    assert result["component_library_posture"]["recommended_use"] == "inspiration_only"


def test_ui_ux_design_system_readiness_watchlists_tailgrids_without_tailwind():
    result = assess_ui_ux_design_system_readiness(
        root=ROOT,
        payload={
            "project_type": "frontend_app",
            "product_type": "developer tool dashboard",
            "audience": "technical teams",
            "stack": "react",
            "uses_tailwind": False,
            "needs_forms": True,
            "needs_tables": True,
        },
    )

    assert result["status"] == "ok"
    assert result["component_library_posture"]["tailgrids_fit"] == "medium"
    assert result["component_library_posture"]["recommended_use"] == "watchlist"
