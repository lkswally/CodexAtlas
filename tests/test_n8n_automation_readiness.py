import os
import shutil
from pathlib import Path
from uuid import uuid4

os.environ["ATLAS_DISABLE_EVENT_LOGS"] = "1"

from tests._support_paths import ATLAS_ROOT, WEB_ROOT
from tools.n8n_automation_readiness import assess_n8n_automation_readiness
from tools.quality_gate_report import build_quality_gate_report


def _make_temp_project() -> Path:
    base = ATLAS_ROOT / "tests" / "_tmp_n8n_automation_cases"
    base.mkdir(parents=True, exist_ok=True)
    project = base / f"case_{uuid4().hex}"
    project.mkdir(parents=True, exist_ok=False)
    return project


def test_n8n_automation_high_risk_for_real_send_email():
    result = assess_n8n_automation_readiness(
        {
            "project_type": "workflow_automation",
            "nodes": [{"type": "gmail", "name": "Send Email"}],
            "test_payload_available": True,
            "human_approval_required": True,
        },
        root=ATLAS_ROOT,
        project=ATLAS_ROOT,
    )

    assert result["risk_level"] == "high"
    assert "send_email_real" in result["side_effects"]
    assert result["human_approval_required"] is True


def test_n8n_automation_high_risk_for_sheets_or_db_write():
    result = assess_n8n_automation_readiness(
        {
            "project_type": "workflow_automation",
            "nodes": [{"type": "google sheets", "name": "Append Row"}],
            "test_payload_available": True,
        },
        root=ATLAS_ROOT,
        project=ATLAS_ROOT,
    )

    assert result["risk_level"] == "high"
    assert "sheets_or_db_write" in result["side_effects"]


def test_n8n_automation_high_risk_for_public_webhook_without_auth():
    result = assess_n8n_automation_readiness(
        {
            "project_type": "workflow_automation",
            "nodes": [{"type": "webhook", "name": "Webhook Trigger"}],
            "public_webhook": True,
            "test_payload_available": True,
        },
        root=ATLAS_ROOT,
        project=ATLAS_ROOT,
    )

    assert result["risk_level"] == "high"
    assert "public_webhook_without_auth" in result["side_effects"]


def test_n8n_automation_high_risk_for_llm_with_sensitive_data():
    result = assess_n8n_automation_readiness(
        {
            "project_type": "workflow_automation",
            "nodes": [{"type": "openai", "name": "LLM Classification"}],
            "contains_sensitive_data": True,
            "test_payload_available": True,
        },
        root=ATLAS_ROOT,
        project=ATLAS_ROOT,
    )

    assert result["risk_level"] == "high"
    assert "llm_with_sensitive_data" in result["side_effects"]


def test_n8n_automation_requires_test_payload_when_missing():
    result = assess_n8n_automation_readiness(
        {
            "project_type": "workflow_automation",
            "nodes": [{"type": "manual trigger", "name": "Manual Trigger"}],
        },
        root=ATLAS_ROOT,
        project=ATLAS_ROOT,
    )

    assert result["test_payload_required"] is True
    assert result["automation_ready"] is False


def test_n8n_automation_blueprint_without_side_effects_stays_low_or_medium():
    project = _make_temp_project()
    try:
        result = assess_n8n_automation_readiness(
            {
                "project_type": "automation_blueprint",
                "trigger": "manual trigger",
                "expected_output": "A reviewed workflow draft for human approval.",
                "test_payload_available": True,
                "human_approval_required": True,
                "dry_run_available": True,
                "logging_documented": True,
                "error_handling_documented": True,
                "rollback_documented": True,
                "retry_strategy_documented": True,
                "idempotency_documented": True,
            },
            root=ATLAS_ROOT,
            project=project,
        )
    finally:
        shutil.rmtree(project, ignore_errors=True)

    assert result["risk_level"] in {"low", "medium"}
    assert result["blocked_reasons"] == []


def test_quality_gate_report_exposes_n8n_automation_posture():
    result = build_quality_gate_report(ATLAS_ROOT, WEB_ROOT)

    assert isinstance(result["n8n_automation_posture"], dict)
    assert result["n8n_automation_posture"]["advisory_only"] is True
    assert result["n8n_automation_posture"]["risk_level"] in {"low", "medium", "high"}
    assert isinstance(result["n8n_automation_posture"]["side_effects"], list)
    assert isinstance(result["n8n_automation_posture"]["credentials_required"], list)
