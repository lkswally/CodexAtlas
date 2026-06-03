import os
import shutil
from pathlib import Path
from uuid import uuid4
from unittest.mock import patch

os.environ["ATLAS_DISABLE_EVENT_LOGS"] = "1"

from tests._support_paths import ATLAS_ROOT, TEMP_ROOT
from tools.mcp_permission_matrix_readiness import assess_mcp_permission_matrix_readiness


def _mcp_readiness_stub():
    return {
        "status": "ok",
        "configured_mcp_servers": ["openaiDeveloperDocs"],
        "readiness_state": "cli_ready_no_servers_configured",
    }


def _make_temp_project() -> Path:
    base = TEMP_ROOT / "mcp_permission_matrix_cases"
    base.mkdir(parents=True, exist_ok=True)
    project = base / f"case_{uuid4().hex}"
    project.mkdir(parents=True, exist_ok=False)
    return project


def test_mcp_permission_matrix_allows_github_read_only():
    project = _make_temp_project()
    try:
        with patch("tools.mcp_permission_matrix_readiness.check_mcp_readiness", return_value=_mcp_readiness_stub()):
            result = assess_mcp_permission_matrix_readiness(
                {
                    "platform": "github",
                    "requested_capability": "read_only",
                },
                root=ATLAS_ROOT,
                project=project,
            )
    finally:
        shutil.rmtree(project, ignore_errors=True)

    posture = result["mcp_permission_posture"]
    assert posture["platform"] == "github"
    assert posture["requested_capability"] == "read_only"
    assert posture["allowed"] is True
    assert posture["recommended_mode"] == "read_only"


def test_mcp_permission_matrix_blocks_gmail_execute():
    with patch("tools.mcp_permission_matrix_readiness.check_mcp_readiness", return_value=_mcp_readiness_stub()):
        result = assess_mcp_permission_matrix_readiness(
            {
                "platform": "gmail",
                "requested_capability": "execute",
                "requested_action": "send email",
            },
            root=ATLAS_ROOT,
        )

    posture = result["mcp_permission_posture"]
    assert posture["allowed"] is False
    assert posture["risk_level"] == "high"
    assert "real_email_send_blocked_by_default" in posture["blocked_reasons"]


def test_mcp_permission_matrix_blocks_n8n_production_write():
    with patch("tools.mcp_permission_matrix_readiness.check_mcp_readiness", return_value=_mcp_readiness_stub()):
        result = assess_mcp_permission_matrix_readiness(
            {
                "platform": "n8n",
                "requested_capability": "production_write",
                "dry_run_available": False,
                "rollback_available": False,
            },
            root=ATLAS_ROOT,
        )

    posture = result["mcp_permission_posture"]
    assert posture["allowed"] is False
    assert posture["recommended_mode"] == "read_only"
    assert "production_write_blocked_by_default" in posture["blocked_reasons"]


def test_mcp_permission_matrix_blocks_n8n_sandbox_write_without_approval():
    with patch("tools.mcp_permission_matrix_readiness.check_mcp_readiness", return_value=_mcp_readiness_stub()):
        result = assess_mcp_permission_matrix_readiness(
            {
                "platform": "n8n",
                "requested_capability": "sandbox_write",
                "rollback_available": True,
                "human_approval_granted": False,
            },
            root=ATLAS_ROOT,
        )

    posture = result["mcp_permission_posture"]
    assert posture["allowed"] is False
    assert "sandbox_write_requires_explicit_human_approval" in posture["blocked_reasons"]


def test_mcp_permission_matrix_allows_chrome_devtools_manual_opt_in_with_privacy_warnings():
    with patch("tools.mcp_permission_matrix_readiness.check_mcp_readiness", return_value=_mcp_readiness_stub()):
        result = assess_mcp_permission_matrix_readiness(
            {
                "platform": "chrome_devtools",
                "requested_capability": "read_only",
            },
            root=ATLAS_ROOT,
        )

    posture = result["mcp_permission_posture"]
    assert posture["allowed"] is True
    assert posture["recommended_mode"] == "read_only"
    assert posture["risk_level"] in {"medium", "high"}
    assert posture["human_approval_required"] is True
    assert posture["privacy_warnings"]


def test_mcp_permission_matrix_blocks_google_sheets_production_write():
    with patch("tools.mcp_permission_matrix_readiness.check_mcp_readiness", return_value=_mcp_readiness_stub()):
        result = assess_mcp_permission_matrix_readiness(
            {
                "platform": "google_sheets",
                "requested_capability": "production_write",
                "requested_action": "write row",
            },
            root=ATLAS_ROOT,
        )

    posture = result["mcp_permission_posture"]
    assert posture["allowed"] is False
    assert "sheet_write_or_execute_blocked_by_default" in posture["blocked_reasons"]


def test_mcp_permission_matrix_blocks_filesystem_write_outside_repo():
    project = _make_temp_project()
    outside_target = TEMP_ROOT / f"outside_{uuid4().hex}" / "danger.txt"
    try:
        outside_target.parent.mkdir(parents=True, exist_ok=True)
        with patch("tools.mcp_permission_matrix_readiness.check_mcp_readiness", return_value=_mcp_readiness_stub()):
            result = assess_mcp_permission_matrix_readiness(
                {
                    "platform": "filesystem",
                    "requested_capability": "sandbox_write",
                    "human_approval_granted": True,
                    "rollback_available": True,
                    "target_path": str(outside_target),
                },
                root=ATLAS_ROOT,
                project=project,
            )
    finally:
        shutil.rmtree(project, ignore_errors=True)
        shutil.rmtree(outside_target.parent.parent, ignore_errors=True)

    posture = result["mcp_permission_posture"]
    assert posture["allowed"] is False
    assert "filesystem_write_outside_governed_workspace_blocked" in posture["blocked_reasons"]
