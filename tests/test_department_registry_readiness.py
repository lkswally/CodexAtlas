import os
from pathlib import Path

os.environ["ATLAS_DISABLE_EVENT_LOGS"] = "1"

from tests._support_paths import ATLAS_ROOT, WEB_ROOT
from tools.department_registry_readiness import assess_department_registry_readiness


def test_department_registry_recommends_web_growth_and_governance_for_frontend_surface():
    result = assess_department_registry_readiness(
        {
            "project_type": "frontend_app",
            "objective": "Polish the landing, improve CTA clarity and tighten brand trust.",
            "target_audience": "Founders validating AI workflows.",
            "visual_fidelity_posture": {
                "fidelity_state": "drift_detected",
                "drift_signals": ["CTA hierarchy drift"],
            },
            "copywriting_conversion_posture": {
                "copy_readiness_state": "needs_improvement",
                "warnings": ["Hero is still vague."],
            },
            "brand_strategy_posture": {
                "brand_readiness_state": "needs_improvement",
                "warnings": ["Palette still feels generic."],
            },
        },
        root=ATLAS_ROOT,
        project=WEB_ROOT,
    )

    posture = result["department_registry_posture"]
    assert result["status"] == "ok"
    assert posture["registry_state"] == "ready"
    assert posture["auto_activate"] is False
    assert "web_ux" in posture["recommended_departments"]
    assert "growth_marketing" in posture["recommended_departments"]
    assert "qa_governance" in posture["recommended_departments"]


def test_department_registry_recommends_automation_for_n8n_like_work():
    result = assess_department_registry_readiness(
        {
            "project_type": "internal_tool",
            "objective": "Design an n8n workflow to review leads and send a draft report.",
            "n8n_automation_posture": {
                "risk_level": "high",
                "side_effects": ["send_email_real", "sheets_or_db_write"],
                "source_files": ["docs/workflow.json"],
            },
        },
        root=ATLAS_ROOT,
        project=ATLAS_ROOT,
    )

    posture = result["department_registry_posture"]
    assert "automation_n8n" in posture["recommended_departments"]
    assert "engineering" in posture["recommended_departments"]
    assert "qa_governance" in posture["recommended_departments"]


def test_department_registry_prefers_engineering_for_backend_code_work():
    result = assess_department_registry_readiness(
        {
            "project_type": "backend_service",
            "objective": "Refactor runtime compatibility checks and tighten build validation.",
            "repo_graph_posture": {
                "repo_graph_recommended": True,
            },
        },
        root=ATLAS_ROOT,
        project=ATLAS_ROOT,
    )

    posture = result["department_registry_posture"]
    assert "engineering" in posture["recommended_departments"]
    assert "web_ux" not in posture["recommended_departments"]
    assert "growth_marketing" not in posture["recommended_departments"]


def test_department_registry_keeps_operations_finance_in_watchlist():
    result = assess_department_registry_readiness(
        {
            "project_type": "ai_agent_system",
            "objective": "Review model fallback cost and provider watchlist posture.",
            "model_cost_control_posture": {
                "recommended_model_tier": "mini",
                "fallback_posture": {
                    "fallback_mode": "manual_only",
                    "auto_switch_enabled": False,
                },
            },
        },
        root=ATLAS_ROOT,
        project=ATLAS_ROOT,
    )

    posture = result["department_registry_posture"]
    assert "operations_finance" in posture["watchlist_departments"]
    assert "operations_finance" not in posture["recommended_departments"]


def test_department_registry_exposes_manual_governed_mode():
    result = assess_department_registry_readiness(
        {
            "project_type": "atlas-factory-core",
            "objective": "Audit Atlas operating departments.",
        },
        root=ATLAS_ROOT,
        project=ATLAS_ROOT,
    )

    posture = result["department_registry_posture"]
    assert posture["activation_mode"] == "manual_governed"
    assert posture["advisory_only"] is True
    assert posture["auto_activate"] is False
