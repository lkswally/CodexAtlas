import os

os.environ["ATLAS_DISABLE_EVENT_LOGS"] = "1"

from tests._support_paths import ATLAS_ROOT, WEB_ROOT
from tools.n8n_api_connector_readiness import assess_n8n_api_connector_readiness
from tools.quality_gate_report import build_quality_gate_report


def test_n8n_api_connector_not_configured_without_base_url():
    result = assess_n8n_api_connector_readiness({}, root=ATLAS_ROOT, project=ATLAS_ROOT)

    posture = result["n8n_api_connector_posture"]
    assert posture["connection_mode"] == "not_configured"
    assert posture["api_key_required"] is True
    assert posture["api_key_read"] is False


def test_n8n_api_connector_read_only_config_allows_list_and_get():
    result = assess_n8n_api_connector_readiness(
        {
            "n8n_base_url": "https://n8n.example.internal",
            "requested_operation": "list_workflows",
        },
        root=ATLAS_ROOT,
        project=ATLAS_ROOT,
    )

    posture = result["n8n_api_connector_posture"]
    assert posture["connection_mode"] == "read_only_ready"
    assert "list_workflows" in posture["allowed_operations"]
    assert "get_workflow" in posture["allowed_operations"]


def test_n8n_api_connector_keeps_allow_write_false_by_default():
    result = assess_n8n_api_connector_readiness(
        {"n8n_base_url": "https://n8n.example.internal"},
        root=ATLAS_ROOT,
        project=ATLAS_ROOT,
    )

    assert result["n8n_api_connector_posture"]["allow_write"] is False


def test_n8n_api_connector_keeps_allow_execute_false_even_if_requested():
    result = assess_n8n_api_connector_readiness(
        {
            "n8n_base_url": "https://n8n.example.internal",
            "allow_execute": True,
            "requested_operation": "execute_workflow",
        },
        root=ATLAS_ROOT,
        project=ATLAS_ROOT,
    )

    posture = result["n8n_api_connector_posture"]
    assert posture["allow_execute"] is False
    assert posture["connection_mode"] == "blocked"
    assert "allow_execute_must_remain_false" in posture["blocked_reasons"]


def test_n8n_api_connector_blocks_sandbox_write_without_sandbox_tag():
    result = assess_n8n_api_connector_readiness(
        {
            "n8n_base_url": "https://n8n.example.internal",
            "requested_operation": "create_workflow",
            "allow_write": True,
            "explicit_human_approval": True,
            "workflow_active": False,
        },
        root=ATLAS_ROOT,
        project=ATLAS_ROOT,
    )

    posture = result["n8n_api_connector_posture"]
    assert posture["connection_mode"] == "blocked"
    assert "sandbox_tag_required_for_write" in posture["blocked_reasons"]


def test_n8n_api_connector_blocks_production_write_targets():
    result = assess_n8n_api_connector_readiness(
        {
            "n8n_base_url": "https://n8n.example.internal",
            "requested_operation": "create_workflow",
            "allow_write": True,
            "explicit_human_approval": True,
            "sandbox_tags": ["atlas_sandbox"],
            "production_target": True,
        },
        root=ATLAS_ROOT,
        project=ATLAS_ROOT,
    )

    posture = result["n8n_api_connector_posture"]
    assert posture["connection_mode"] == "blocked"
    assert "production_write_blocked" in posture["blocked_reasons"]


def test_n8n_api_connector_blocks_credentials_access():
    result = assess_n8n_api_connector_readiness(
        {
            "n8n_base_url": "https://n8n.example.internal",
            "requested_operation": "read_credentials",
        },
        root=ATLAS_ROOT,
        project=ATLAS_ROOT,
    )

    posture = result["n8n_api_connector_posture"]
    assert posture["connection_mode"] == "blocked"
    assert "credentials_access_blocked" in posture["blocked_reasons"]


def test_quality_gate_report_exposes_n8n_api_connector_posture():
    result = build_quality_gate_report(ATLAS_ROOT, WEB_ROOT)

    assert isinstance(result["n8n_api_connector_posture"], dict)
    assert result["n8n_api_connector_posture"]["advisory_only"] is True
    assert result["n8n_api_connector_posture"]["connection_mode"] in {
        "not_configured",
        "read_only_ready",
        "sandbox_write_ready",
        "blocked",
    }
    assert result["source_reports"]["n8n_api_connector_readiness"]["status"] == "ok"
